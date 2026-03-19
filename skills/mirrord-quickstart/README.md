# mirrord-quickstart

Get started with mirrord from zero to first session.

## What it does

This skill helps AI agents guide new users through:
- **Requirements** — verify kubectl and cluster access
- **Installation** — CLI, VS Code, or IntelliJ
- **First session** — connect to a pod and verify it works

## Example prompts

```
"I'm new to mirrord, how do I get started?"

"Help me install mirrord on macOS"

"How do I run my first mirrord session?"

"Connect my local Node.js app to a Kubernetes pod"
```

## Installation options

| Method | Command |
|--------|---------|
| Homebrew | `brew install metalbear-co/mirrord/mirrord` |
| Binary | Download from [GitHub Releases](https://github.com/metalbear-co/mirrord/releases) |
| VS Code | Search "mirrord" in Extensions |
| IntelliJ | Search "mirrord" in Plugins |

## First session

```bash
# List available targets
mirrord ls

# Run your app with mirrord
mirrord exec --target pod/<pod-name> -- <your-command>
```

## Learn more

- [mirrord Documentation](https://metalbear.com/mirrord/docs/)
- [GitHub Repository](https://github.com/metalbear-co/mirrord)
