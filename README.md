![mirrord Agent Skills](assets/mirrord-agent-skills.png)

# mirrord Agent Skills

Six [Agent Skills](https://agentskills.io/home) that close the AI agent feedback loop on Kubernetes: real env vars, real DNS, real network, real traffic, real databases, real Kafka. Built by [MetalBear](https://metalbear.com/) to be used with [mirrord](https://metalbear.com/mirrord/).

AI coding agents work from what's in their context window. Your Kubernetes cluster is full of state that isn't. These skills teach your agent how and when to use mirrord so the code it writes against your live infrastructure stops being informed guessing.

## Installation

### Claude Code

```bash
/plugin marketplace add metalbear-co/skills
```

### Cursor, Codex, Gemini, or any [Agent Skills](https://agentskills.io)-compatible agent

```bash
npx skills add metalbear-co/skills
```

Using an agent that doesn't consume Agent Skills yet? The same content can be ported to `.cursorrules`, `agents.md`, Cline rules, and similar. Open an issue with the target you'd like next.

## The six skills

| Skill | What it does |
|-------|--------------|
| [mirrord-quickstart](./skills/mirrord-quickstart/) | Zero-to-first-session: install mirrord, find a target, run the first session. |
| [mirrord-config](./skills/mirrord-config/) | Generate and validate `mirrord.json` for any workflow (steal, mirror, env injection, file system hooks). |
| [mirrord-operator](./skills/mirrord-operator/) | Install and configure the mirrord Operator for team-scale concurrent shared-cluster use. |
| [mirrord-ci](./skills/mirrord-ci/) | Wire mirrord into CI pipelines so integration tests hit real cluster services. |
| [mirrord-db-branching](./skills/mirrord-db-branching/) | Per-developer copy-on-write database branches off your staging DB. |
| [mirrord-kafka](./skills/mirrord-kafka/) | Kafka queue splitting so each developer consumes a private slice of a real topic. |

## Example prompts

Once installed, your agent activates the right skill based on the prompt:

- "I'm new to mirrord, help me run my Node app against my staging cluster."
- "Steal traffic from `pod/api-server`, but only requests carrying my baggage header so I don't break anyone else's session."
- "Install the operator on our EKS cluster and configure RBAC so only the `dev` group can use it."
- "Set up GitHub Actions to run our integration tests with mirrord against the staging cluster."
- "Give me an isolated DB branch off the staging Postgres for this feature."
- "Set up queue splitting on the `orders.created` topic for my local consumer."

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
