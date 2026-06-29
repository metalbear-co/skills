# mirrord-preview-environments

Help AI agents and users configure **mirrord Preview Environments** — isolated in-cluster pods that run a chosen image while matching an existing workload and receiving **filtered or duplicated** traffic via an **environment key**.

## What it does

- Explain **when** to use previews vs local `mirrord exec` / `mirrord up`
- Guide **`mirrord preview start`**, **`status`**, **`stop`**
- Relate **`mirrord.json`** fields: root **`key`**, **`feature.preview`**, **`target`**, incoming filters with **`{{ key }}`**
- Point to the **[`metalbear-co/mirrord-preview`](https://github.com/metalbear-co/mirrord-preview)** GitHub Action for PR workflows
- Document **readiness gate** behavior (preview pods intentionally not Ready)

## Example prompts

```
"How do I start a mirrord preview environment for deployment/api in staging?"

"What should my mirrord.json look like for a preview with TTL 60 minutes?"

"Why isn't my preview pod becoming Ready?"

"Set up GitHub Actions to start a preview on PR open and stop on close"

"What is the environment key used for in preview environments?"
```

## Prerequisites

- **Enterprise** plan (see [Preview Environments](https://metalbear.com/mirrord/docs/use-cases/preview-environments))
- **mirrord operator** installed and licensed
- **Container image** pushed to a registry the cluster can pull

## Quick CLI reference

```bash
mirrord preview start -f mirrord.json -i myregistry/my-app:tag -k my-preview-key
mirrord preview status
mirrord preview stop --key my-preview-key
```

## Learn more

- [Preview Environments (official)](https://metalbear.com/mirrord/docs/use-cases/preview-environments)
- [mirrord-preview GitHub Action](https://github.com/metalbear-co/mirrord-preview)
- [Pod readiness gates (Kubernetes)](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-readiness-gate)
