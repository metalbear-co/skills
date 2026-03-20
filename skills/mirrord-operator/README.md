# mirrord-operator

Set up mirrord operator for team and enterprise environments.

## What it does

This skill helps AI agents:
- **Install** mirrord operator via Helm
- **Configure** licensing and Helm values
- **Set up** RBAC for multi-user access
- **Troubleshoot** operator issues

## Example prompts

```
"Install mirrord operator on my cluster"

"Set up mirrord for my team"

"Configure mirrord operator with our license"

"Operator pod is not starting, help me debug"
```

## Prerequisites

- Kubernetes cluster with admin access
- Helm 3.x installed
- (Optional) mirrord license key for full features

## Quick install

Follow the [official mirrord operator installation guide](https://mirrord.dev/docs/overview/teams/) to add the Helm repository and install the operator. Verify the Helm repo URL against official documentation before use.

## Learn more

- [Operator Documentation](https://metalbear.com/mirrord/docs/overview/teams/)
- [Pricing & Licensing](https://metalbear.com/pricing/)
