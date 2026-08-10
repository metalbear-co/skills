![mirrord Agent Skills](assets/mirrord-agent-skills.png)

# mirrord Agent Skills

Nine [Agent Skills](https://agentskills.io/home) that close the AI agent feedback loop on Kubernetes: real env vars, real DNS, real network, real traffic, real databases, real Kafka, real preview environments, multi-service local sessions, and real failure conditions. Built by [MetalBear](https://metalbear.com/) to be used with [mirrord](https://metalbear.com/mirrord/).

AI coding agents work from what's in their context window. Your Kubernetes cluster is full of state that isn't. These skills teach your agent how and when to use mirrord so the code it writes against your live infrastructure stops being informed guessing.

## Installation

### Claude Code

```bash
/plugin marketplace add metalbear-co/skills
/plugin install mirrord@mirrord-skills
```

### Codex

```bash
codex plugin marketplace add metalbear-co/skills
```

Then install the `mirrord` plugin from `/plugins`. All nine skills come with it.

### OpenCode

OpenCode loads skills natively, so there's nothing to register — the skills just need to be on disk:

```bash
curl -fsSL https://raw.githubusercontent.com/metalbear-co/skills/main/install.sh | sh
```

That writes the nine skill folders into `~/.config/opencode/skills/`. Restart OpenCode and they're available. Re-run it any time to update — it replaces the `mirrord-*` folders and leaves your other skills alone.

The same script serves any agent that reads a skills directory:

```bash
sh install.sh --agent codex     # ~/.agents/skills
sh install.sh --agent claude    # ~/.claude/skills
sh install.sh --dest <dir>      # anywhere else
```

### Cursor, Gemini, or any other [Agent Skills](https://agentskills.io)-compatible agent

```bash
npx skills add metalbear-co/skills
```

### GitHub Copilot, Cline, and other rules-file agents

The [`ports/`](./ports/) directory carries the same core content as drop-in rules files: copy [`ports/github-copilot/copilot-instructions.md`](./ports/github-copilot/copilot-instructions.md) into your repo's `.github/`, or [`ports/cline/.clinerules`](./ports/cline/.clinerules) into your repo root. Want another format? [Open an issue](https://github.com/metalbear-co/skills/issues) with the target you'd like next.

## The nine skills

| Skill | What it does |
|-------|--------------|
| [mirrord-quickstart](./skills/mirrord-quickstart/) | Zero-to-first-session: install mirrord, find a target, run the first session. |
| [mirrord-config](./skills/mirrord-config/) | Generate and validate `mirrord.json` for any workflow (steal, mirror, env injection, file system hooks). |
| [mirrord-operator](./skills/mirrord-operator/) | Install and configure the mirrord Operator for team-scale concurrent shared-cluster use. |
| [mirrord-ci](./skills/mirrord-ci/) | Wire mirrord into CI pipelines so integration tests hit real cluster services. |
| [mirrord-db-branching](./skills/mirrord-db-branching/) | Per-developer copy-on-write database branches off your staging DB. |
| [mirrord-kafka](./skills/mirrord-kafka/) | Kafka queue splitting so each developer consumes a private slice of a real topic. |
| [mirrord-prev-env](./skills/mirrord-prev-env/) | Preview environments: deploy a built image as an isolated, traffic-filtered pod in a shared cluster — ad hoc or per-PR in CI. |
| [mirrord-up](./skills/mirrord-up/) | Multiple concurrent local sessions from `mirrord-up.yaml` — compose-style multi-service debugging. |
| [mirrord-chaos](./skills/mirrord-chaos/) | Chaos testing: inject latency or connection errors into a session's outgoing traffic via per-session rules, interactively or in CI. |

## Example prompts

Once installed, your agent activates the right skill based on the prompt:

- "I'm new to mirrord, help me run my Node app against my staging cluster."
- "Steal traffic from `pod/api-server`, but only requests carrying my baggage header so I don't break anyone else's session."
- "Install the operator on our EKS cluster and configure RBAC so only the `dev` group can use it."
- "Set up GitHub Actions to run our integration tests with mirrord against the staging cluster."
- "Give me an isolated DB branch off the staging Postgres for this feature."
- "Set up queue splitting on the `orders.created` topic for my local consumer."
- "Spin up a per-PR preview environment in GitHub Actions so the team can review my change against real traffic."
- "Generate a mirrord-up.yaml so I can debug my auth and dashboard services together."
- "Make 30% of my service's calls to the payments API time out, so I can test our retry logic."

## Trusted by

mirrord runs across teams like [monday.com](https://metalbear.com/mirrord/case-study/monday/) (350+ engineers on a single shared staging cluster), [SurveyMonkey](https://metalbear.com/mirrord/case-study/surveymonkey/), [CoLab](https://metalbear.com/mirrord/case-study/colab/), [Cadence](https://metalbear.com/mirrord/case-study/cadence/), [Daylight Security](https://metalbear.com/mirrord/case-study/daylight/), and [Zooplus](https://metalbear.com/mirrord/case-study/zooplus/). Daylight's team cut their edit-test cycle from 5–8 minutes to about 5 seconds after pairing Cursor with mirrord.

## Skill structure

Each skill is a folder following the [Agent Skills format](https://agentskills.io/home):

- `SKILL.md` - Instructions the agent loads on demand
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)

## Learn more

- [mirrord for AI Agents](https://metalbear.com/mirrord/ai) - product page with installation guides for every supported agent
- [mirrord documentation](https://metalbear.com/mirrord/docs)

## Contributing

PRs welcome. Open an issue if you'd like to see a skill added or improved.
