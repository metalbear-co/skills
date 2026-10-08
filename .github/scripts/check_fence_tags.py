#!/usr/bin/env python3
"""Check that every fenced json/yaml block in the repo's Markdown carries a tag.

The convention is documented in CONTRIBUTING.md. In short, the fence info
string reads `<lang> <tag>`, where <lang> is json or yaml and <tag> is one of
the tags below. Blocks tagged as mirrord or mirrord-up config must parse as
strict JSON or YAML and contain no '...' placeholders.

Usage:
    python3 .github/scripts/check_fence_tags.py            # check, exit 1 on failure
    python3 .github/scripts/check_fence_tags.py --list     # also print every block

Requires PyYAML and markdown-it-py (.github/scripts/requirements.txt).
"""

import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

REPO_ROOT = Path(__file__).resolve().parents[2]

# Synced verbatim from upstream by .github/workflows/update-references.yml.
# Keep in sync with the exempt list in CONTRIBUTING.md.
EXEMPT = {
    "skills/mirrord-config/references/configuration.md",
    "skills/mirrord-config/references/schema.json",
    "skills/mirrord-operator/references/values.yaml",
    "skills/mirrord-up/references/schema.json",
}

# Schemas that fragment paths resolve against, per config tag.
SCHEMAS = {
    "mirrord": "skills/mirrord-config/references/schema.json",
    "mirrord-up": "skills/mirrord-up/references/schema.json",
}

LANGS = {"json": "json", "yaml": "yaml", "yml": "yaml"}

# Tags whose blocks must parse.
CONFIG_TAGS = {"mirrord", "mirrord-up"}
OTHER_TAGS = {
    "mirrord-invalid",
    "chaos-rule",
    "crd",
    "helm-values",
    "k8s",
    "workflow",
    "output",
    "other",
}

# Dotted schema path. Segments are identifiers or `*`, each optionally
# followed by `[]` for array items, e.g. feature.db_branches[] or services.*
PATH_RE = re.compile(r"^(?:[A-Za-z_][A-Za-z0-9_-]*|\*)(?:\[\])?(?:\.(?:[A-Za-z_][A-Za-z0-9_-]*|\*)(?:\[\])?)*$")



def parse_tag(tag):
    """Split a tag into (base, path). Returns (None, None) if malformed."""
    base, sep, path = tag.partition("=")
    if sep:
        if base not in CONFIG_TAGS or not PATH_RE.match(path):
            return None, None
        return base, path
    if base in CONFIG_TAGS or base in OTHER_TAGS:
        return base, None
    return None, None


# A bare "..." line is a YAML document end marker, which safe_load silently drops.
YAML_DOC_END_RE = re.compile(r"^\.\.\.(?:[ \t]+#.*)?[ \t]*$")

MARKDOWN = MarkdownIt("commonmark")


def iter_fences(text):
    """Yield (line_no, info, body) for every fenced code block, as CommonMark
    renders it: inside blockquotes and list items, but not in indented code or
    HTML blocks."""
    for token in MARKDOWN.parse(text):
        if token.type == "fence":
            yield token.map[0] + 1, token.info.strip(), token.content.removesuffix("\n")


def reject_constant(name):
    raise ValueError(f"non-standard JSON constant {name}")


def reject_duplicate_keys(pairs):
    keys = [k for k, _ in pairs]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        raise ValueError(f"duplicate key(s) {', '.join(dupes)}")
    return dict(pairs)


class StrictYamlLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys instead of keeping the last."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise yaml.constructor.ConstructorError(
                    None, None, f"duplicate key {key!r}", key_node.start_mark)
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def parse(lang, body):
    if lang == "json":
        return json.loads(body, parse_constant=reject_constant, object_pairs_hook=reject_duplicate_keys)
    return yaml.load(body, Loader=StrictYamlLoader)


def any_scalar(node, test, stack=(), clean=None):
    """True if `test` holds for any key or scalar value in the parsed tree.

    Raises ValueError on a cycle, which a recursive YAML alias such as
    `a: &x [*x]` produces and which no JSON config can express. Containers
    already found clean are skipped, so YAML aliases that share a subtree are
    walked once instead of once per reference.
    """
    clean = set() if clean is None else clean
    if isinstance(node, (dict, list)):
        if id(node) in stack:
            raise ValueError("recursive YAML alias")
        if id(node) in clean:
            return False
        stack += (id(node),)
        children = [x for pair in node.items() for x in pair] if isinstance(node, dict) else node
        if any(any_scalar(child, test, stack, clean) for child in children):
            return True
        clean.add(id(node))
        return False
    return test(node)


def is_placeholder(value):
    return value == "..."


def is_non_finite(value):
    """NaN or infinity, e.g. YAML .nan/.inf or a JSON number such as 1e999."""
    return isinstance(value, float) and not math.isfinite(value)


def resolve_fragment(schema, path):
    """Resolve a dotted fragment path against a JSON schema.

    Returns the object alternatives at `path` as a list of (properties, open,
    consts) tuples, or None if the path does not resolve to an object. `consts`
    maps properties declared with `const` (variant discriminators such as
    `flavor` or `type`) to their required value. oneOf and anyOf
    branches stay separate alternatives, so keys from mutually exclusive
    variants never combine; allOf parts and sibling keywords merge into each
    alternative. `open` means keys outside `properties` are allowed: an explicit
    `additionalProperties` of true or a schema, or a schema with no validation
    keywords (`true`, or only annotations such as `description`), which accepts
    anything at and below it.
    """
    defs = {**schema.get("definitions", {}), **schema.get("$defs", {})}
    annotations = {"description", "title", "default", "examples", "$comment", "deprecated", "readOnly", "writeOnly"}
    # An alternative: properties (name -> schemas that all apply), map value and
    # array item schemas, whether extra keys are allowed (None: not stated), and
    # whether it accepts anything.
    neutral = {"props": {}, "extra": [], "items": [], "open": None, "any": False}
    anything = {**neutral, "open": True, "any": True}

    def constrains(alt):
        return not alt["any"] and (alt["open"] is not None or any(alt[k] for k in ("props", "extra", "items")))

    def merge(a, b):
        if a["any"] or b["any"]:
            # Anything merged with a real constraint is that constraint.
            other = b if a["any"] else a
            return other if constrains(other) else anything
        props = {k: a["props"].get(k, []) + b["props"].get(k, []) for k in {**a["props"], **b["props"]}}
        is_open = a["open"] if b["open"] is None else b["open"] if a["open"] is None else a["open"] and b["open"]
        return {"props": props, "extra": a["extra"] + b["extra"], "items": a["items"] + b["items"], "open": is_open, "any": False}

    def alternatives(node, seen=()):
        while isinstance(node, dict) and "$ref" in node:
            ref = node["$ref"].rsplit("/", 1)[-1]
            if ref in seen:
                return []
            seen += (ref,)
            node = defs.get(ref)
        if node is True or (isinstance(node, dict) and set(node) <= annotations):
            return [anything]
        if not isinstance(node, dict):
            return []
        extra = node.get("additionalProperties")
        declares = "properties" in node or "additionalProperties" in node
        alts = [{
            "props": {k: [v] for k, v in node.get("properties", {}).items()},
            "extra": [extra] if isinstance(extra, dict) else [],
            "items": [node["items"]] if isinstance(node.get("items"), dict) else [],
            "open": (extra is True or isinstance(extra, dict)) if declares else None,
            "any": False,
        }]
        for part in node.get("allOf", []):
            alts = [merge(a, b) for a in alts for b in alternatives(part, seen)]
        for key in ("anyOf", "oneOf"):
            if key in node:
                alts = [merge(a, b) for a in alts for branch in node[key] for b in alternatives(branch, seen)]
        return alts

    def all_of(schemas):
        alts = [neutral]
        for s in schemas:
            alts = [merge(a, b) for a in alts for b in alternatives(s)]
        return alts

    current = alternatives(schema)
    for segment in path.split("."):
        name, is_item = (segment[:-2], True) if segment.endswith("[]") else (segment, False)
        step = []
        for alt in current:
            schemas = alt["extra"] if name == "*" else alt["props"].get(name, [])
            step += [anything] if alt["any"] else all_of(schemas) if schemas else []
        if is_item:
            step = [n for alt in step for n in ([anything] if alt["any"] else all_of(alt["items"]) if alt["items"] else [])]
        current = step
        if not current:
            return None

    def const_of(schemas):
        for s in schemas:
            while isinstance(s, dict) and "$ref" in s:
                s = defs.get(s["$ref"].rsplit("/", 1)[-1])
            if isinstance(s, dict) and "const" in s:
                return [s["const"]]
        return []

    objects = []
    for a in current:
        if a["any"] or a["open"] is not None or a["props"]:
            consts = {k: c for k, schemas in a["props"].items() for c in const_of(schemas)}
            entry = (set(a["props"]), bool(a["open"]), consts)
            if entry not in objects:
                objects.append(entry)
    return objects or None


def root_keys(lang, body):
    try:
        data = parse(lang, body)
    except Exception:
        return "<unparsed>"
    if isinstance(data, dict):
        return ",".join(str(k) for k in data)
    if isinstance(data, list):
        return "<list>"
    return f"<{type(data).__name__}>"


def check_file(path, rel, blocks, failures, schemas):
    check_text(path.read_text(encoding="utf-8"), rel, blocks, failures, schemas)


def load_schemas():
    return {tag: json.loads((REPO_ROOT / p).read_text(encoding="utf-8")) for tag, p in SCHEMAS.items()}


def check_text(text, rel, blocks, failures, schemas):
    for line_no, info, body in iter_fences(text):
        words = info.split()
        if not words or words[0].lower() not in LANGS:
            continue
        lang = LANGS[words[0].lower()]
        tags = words[1:]
        tag = tags[0] if len(tags) == 1 else ("<untagged>" if not tags else " ".join(tags))
        blocks.append((rel, line_no, tag, root_keys(lang, body)))
        where = f"{rel}:{line_no}"

        if not tags:
            failures.append(f"{where}: untagged {lang} block")
            continue
        if len(tags) > 1:
            failures.append(f"{where}: expected one tag, got '{' '.join(tags)}'")
            continue
        base, frag_path = parse_tag(tag)
        if base is None:
            failures.append(f"{where}: unknown tag '{tag}'")
            continue
        if base in CONFIG_TAGS:
            if lang == "yaml":
                for offset, body_line in enumerate(body.split("\n"), start=1):
                    if YAML_DOC_END_RE.match(body_line):
                        failures.append(f"{rel}:{line_no + offset}: '{tag}' block contains a '...' placeholder line")
            try:
                data = parse(lang, body)
            except Exception as e:
                msg = str(e).splitlines()[0]
                failures.append(f"{where}: '{tag}' block does not parse as {lang}: {msg}")
                continue
            try:
                if any_scalar(data, is_placeholder):
                    failures.append(f"{where}: '{tag}' block contains a '...' placeholder")
                if any_scalar(data, is_non_finite):
                    failures.append(f"{where}: '{tag}' block contains a NaN or infinite number")
            except ValueError as e:
                failures.append(f"{where}: '{tag}' block contains a {e}")
                continue
            if frag_path is None:
                continue
            alternatives = resolve_fragment(schemas[base], frag_path)
            if alternatives is None:
                failures.append(f"{where}: path '{frag_path}' does not resolve to an object in {SCHEMAS[base]}")
                continue
            if not isinstance(data, dict):
                failures.append(f"{where}: '{tag}' fragment is not an object")
                continue
            keys = set(data)
            if any(
                is_open or (keys <= props and all(data[k] == consts[k] for k in keys & set(consts)))
                for props, is_open, consts in alternatives
            ):
                continue
            unknown = sorted(str(k) for k in keys if not any(k in props for props, _, _ in alternatives))
            if unknown:
                failures.append(f"{where}: keys {', '.join(unknown)} are not properties of '{frag_path}' in {SCHEMAS[base]}")
            else:
                failures.append(
                    f"{where}: keys {', '.join(sorted(map(str, keys)))} and their const values do not match "
                    f"any one alternative of '{frag_path}' in {SCHEMAS[base]}")


def markdown_files():
    """Tracked and untracked-but-not-ignored *.md files in this repository.

    Asking git keeps nested checkouts (docs-src/ in docs-sync.yml) and ignored
    folders such as node_modules/ out of the scan.
    """
    out = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.md"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout
    return sorted({rel for rel in out.split("\0") if rel and (REPO_ROOT / rel).is_file()})


def main():
    list_all = "--list" in sys.argv[1:]
    blocks, failures = [], []
    schemas = load_schemas()
    for rel in markdown_files():
        if rel not in EXEMPT:
            check_file(REPO_ROOT / rel, rel, blocks, failures, schemas)

    if list_all:
        for rel, line_no, tag, keys in blocks:
            print(f"{rel}:{line_no}\t{tag}\t{keys}")
        print()

    counts = Counter(t.split("=")[0] + ("=" if "=" in t else "") for _, _, t, _ in blocks)
    print(f"{len(blocks)} json/yaml blocks")
    for tag, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {n:4d}  {tag}")

    if failures:
        print(f"\n{len(failures)} failure(s):")
        for f in failures:
            print(f"  {f}")
        print("\nSee CONTRIBUTING.md for the fence tag convention.")
        return 1
    print("\nAll json/yaml blocks are tagged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
