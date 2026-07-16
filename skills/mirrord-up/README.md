# mirrord-up

Run **multiple concurrent mirrord sessions** from one `mirrord-up.yaml` — compose-style lifecycle for related microservices.

## What it does

This skill helps AI agents:

- **Generate** or explain `mirrord-up.yaml` (`common`, `services`, targets, filters, `run`)
- **Guide** `mirrord up`, `mirrord up init`, and CLI flags (`-f`, `--key`, `-m`, `-u`)
- **Explain** default **split** mode and the auto HTTP filter based on the session key
- **Warn** that `services.*.messages` (queue splitting) is not supported in `mirrord up` yet

## Example prompts

```
"How do I run multiple mirrord sessions at once?"

"Generate a mirrord-up.yaml for my auth and payment services"

"What does mirrord up init do?"

"How does the session key work with mirrord up HTTP filters?"
```

## Prerequisites

- mirrord CLI installed and on `PATH`
- Cluster access (`kubectl` / kubeconfig) for targeted services
- Optional: operator when using `common.operator: true`

## Quick start

```bash
mirrord up init
mirrord up
```

```yaml
services:
  user-auth-service:
    run:
      command: ["python", "-m", "http.server"]

  stage-user-dashboard-app:
    target:
      path: pod/nginx
    run:
      command: ["node", "app.js"]
```

## Key commands

```bash
mirrord up init
mirrord up init -o ./mirrord-up.yaml
mirrord up
mirrord up -f mirrord-up-custom.yaml
mirrord up --key my-session-key
mirrord up -u   # also start mirrord ui in the background
```

## Learn more

- [Multiple concurrent sessions (mirrord up)](https://metalbear.com/mirrord/docs/using-mirrord/multiple-concurrent-sessions)
