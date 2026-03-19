![mirrord Agent Skills](assets/mirrord-agent-skills.png)
# mirrord Agent Skills

A collection of skills for AI coding agents to work with MetalBear's mirrord. Skills are packaged instructions and scripts that extend agent capabilities for Kubernetes development workflows.

Skills follow the [Agent Skills format](https://agentskills.io/home).

## Installation

### Using npx (requires Node.js)

```bash
npx skills add metalbear-co/skills
```

### Claude Code plugin

```bash
/plugin marketplace add metalbear-co/skills
```

## Available Skills

| Skill | Description |
|-------|-------------|
| [mirrord-config](./skills/mirrord-config/) | Generate and validate mirrord.json configs |
| [mirrord-quickstart](./skills/mirrord-quickstart/) | Get started with mirrord from zero |
| [mirrord-operator](./skills/mirrord-operator/) | Set up operator for team environments |
| [mirrord-ci](./skills/mirrord-ci/) | Set up mirrord in CI pipelines |
| [mirrord-db-branching](./skills/mirrord-db-branching/) | Configure isolated database branches for development |


## Usage

Skills are automatically available once installed. The agent will use them when relevant tasks are detected.

**Examples:**
- "Create a mirrord config to steal traffic on port 3000 from pod/api-server"
- "Validate my mirrord.json and fix any errors"
- "I'm new to mirrord, how do I get started?"
- "Help me connect my local Python app to my staging Kubernetes cluster"
- "Install mirrord operator for my team"
- "Set up mirrord for my GitHub Actions CI pipeline"

## Skill Structure

Each skill contains:
- `SKILL.md` - Instructions for the agent
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

