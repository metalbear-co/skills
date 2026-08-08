# Using mirrord in this repository

This project runs against a Kubernetes cluster. Use mirrord to run and verify code against the cluster's real services: mirrord runs a local process as if it were a pod in the cluster (real env vars, DNS, network, file access, and optionally inbound traffic), with no image build and no deployment.

## When to reach for mirrord

- Before writing code that touches other services, databases, or queues: inspect the real runtime context first.
- After writing code: run it (or its tests) through mirrord against the cluster to verify it, instead of guessing from static context.

## Commands

- List possible targets: `mirrord ls [-n <namespace>]`
- Run anything in a target's context: `mirrord exec --target deployment/<name> [-n <namespace>] -- <command>`
  - Example: `mirrord exec --target deployment/api -- npm test`
- Inspect a target's environment: `mirrord exec --target deployment/<name> -- env`
- Install if missing: `brew install metalbear-co/mirrord/mirrord` (macOS/Linux), `choco install --pre mirrord` (Windows), or `curl -fsSL https://raw.githubusercontent.com/metalbear-co/mirrord/main/scripts/install.sh | bash`

## Configuration

- Config lives at `.mirrord/mirrord.json` (picked up automatically), or pass one with `-f <path>`.
- JSON schema: https://raw.githubusercontent.com/metalbear-co/mirrord/main/mirrord-schema.json
- `feature.network.incoming` is `"mirror"` (copy the target's inbound traffic), `"steal"` (take it), or `"off"`.

## Rules

- Target staging or development clusters, never production.
- Default to `"mirror"`. Use `"steal"` only when your process must be the one responding, and prefer an HTTP filter on shared staging so you only take your own requests. Several users or agents stealing concurrently from the same target requires the mirrord Operator (mirrord for Teams).
- Sessions clean up on exit; nothing you run is deployed to the cluster.
- If `mirrord ls` fails, verify `kubectl get pods` works first (kubeconfig or permissions).

More for agents: https://metalbear.com/agents.md — Docs: https://metalbear.com/mirrord/docs
