# Preview environments — troubleshooting

Short reference for agents helping users debug Preview Environments. Authoritative behavior is described in [Preview Environments](https://metalbear.com/mirrord/docs/use-cases/preview-environments).

## Symptom: Preview pod never becomes `Ready`

**Expected.** Preview pods use a **readiness gate** that intentionally does not evaluate to True so the workload’s **Service** does not route normal cluster traffic to the preview, while the pod can still align with target labels/annotations. Do not treat this as a failed deployment by default.

- Doc: [readinessGate](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-readiness-gate)

## Symptom: No traffic reaches the preview

Checklist:

1. **Environment key** — Same key in CLI/config, filters, and **client baggage** (or chosen header) if using `mirrord-session={{ key }}` style routing.
2. **Incoming mode / filters** — Must match how staging duplicates or steers traffic (see `mirrord.json` schema for `feature.network.incoming`).
3. **Operator / Enterprise** — Preview requires operator; confirm plan and operator health (see mirrord-operator skill).

## Symptom: `mirrord preview start` times out and deletes the session

The CLI **`--timeout`** (seconds) bounds how long it waits for the preview session to reach the CLI’s notion of ready. If cluster pull, RBAC, or operator is slow, increase timeout or fix the underlying issue (image pull, quota, etc.).

## Symptom: `preview start` refuses to create (session already exists)

Use **`--force`** to replace an existing preview for the same **key + target** combination, or **`mirrord preview stop`** first with the correct key.

## Symptom: Image pull errors

The image must exist in a **registry the cluster can reach** with the target namespace’s **imagePullSecrets** if required. The user must build and push before `preview start`.

## Related skills

- **mirrord-operator** — install, Helm, licensing
- **mirrord-config** — validate full `mirrord.json` against `schema.json`
- **mirrord-db-branching** — branch isolation often scoped by the same **environment key**
