# mirrord-chaos

Chaos test your app with mirrord: inject artificial latency or connection errors into a mirrord session's **outgoing traffic** via per-session chaos rules, managed through the mirrord UI server's HTTP API.

## What it does

This skill helps AI agents:
- **Generate** valid chaos rule JSON files (selector + effect + priority)
- **Manage** rules over the chaos API: create, list, get, modify, delete, clear
- **Wire** chaos into CI: headless `mirrord ui start`, token from `~/.mirrord/token`, session ID from `GET /api/sessions`, rules applied from repo files
- **Explain** rule semantics: per-session scoping, highest-priority-wins, percentage, TCP-only selectors today
- **Troubleshoot** chaos-specific issues (validation rejections, rules that never fire, auth errors)

## Two modes

1. **Interactive**: `mirrord ui`, a `mirrord exec` session, and `curl` against `http://127.0.0.1:59281/api/chaos/rules/{session_id}`.
2. **CI**: rule files checked into the repo, applied by the pipeline before the test run, torn down after.

## Example prompts

```
"Add 750ms latency to my service's database connections with mirrord"

"Make 30% of calls to the payments API time out"

"How do I create and delete mirrord chaos rules?"

"Run my integration tests with injected connection errors in CI"

"What's the mirrord chaos API?"
```

## Key requests

```bash
export CHAOS_TOKEN="$(cat ~/.mirrord/token)"
export CHAOS_URL="http://127.0.0.1:59281/api/chaos/rules/$SESSION_ID"

curl --request POST \
  --header 'Content-Type: application/json' \
  --header "x-auth-token: $CHAOS_TOKEN" \
  --data @latency-rule.json \
  "$CHAOS_URL"
```

## Prerequisites

- mirrord **CLI 3.232.0+**
- `mirrord ui` running (serves the chaos API, default port 59281)
- A live mirrord session to attach rules to
- Chaos testing is an **alpha** feature

## Learn more

- [Chaos Testing docs](https://metalbear.com/mirrord/docs/use-cases/chaos-testing)
- [Local UI docs](https://metalbear.com/mirrord/docs/using-mirrord/local-ui)
