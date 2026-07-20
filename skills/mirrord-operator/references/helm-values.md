# mirrord Operator — Helm values reference

Digest of the important knobs in the operator chart. Authoritative source (always check for the latest):
https://raw.githubusercontent.com/metalbear-co/charts/main/mirrord-operator/values.yaml

> **Secrets rule:** never inline a cloud API key, license key, or PEM in `values.yaml` or on the
> CLI. Use a Kubernetes Secret ref or a Google Secret Manager ref (see [Authentication](#authentication)).

## Top-level

| Value | Default | Notes |
|-------|---------|-------|
| `namespace` | `mirrord` | Namespace the operator runs in. |
| `createNamespace` | `true` | Set `false` to manage the namespace yourself. |
| `roleNamespaces` | `[]` | Namespaces to create a namespaced mirrord role in (empty = none). Bind users to it yourself. |
| `extraObjects` | `[]` | Extra Kubernetes resources rendered as templates with the chart. |
| `openshift` | `false` | Set `true` on OpenShift to render a SecurityContextConstraints. |

## Authentication

### Cloud API key (default) — `cloud.apiKey.*`

Exactly one of:

| Value | Notes |
|-------|-------|
| `cloud.apiKey.keyRef` | Name of a Kubernetes Secret holding the key under data key `apiKey`. **Recommended.** |
| `cloud.apiKey.gsmRef` | Google Secret Manager ID `projects/PROJECT_ID/secrets/SECRET_NAME/versions/latest` (read via ADC; see `sa.gcpSa`). |
| `cloud.apiKey.key` | Inline value — plaintext in the pod spec. Dev/test only. |

Generate the key in the dashboard (**Settings**, [app.metalbear.com](https://app.metalbear.com)); shown once. Rotate/revoke from the dashboard.

### License — `license.*` (deprecated for cloud auth; used for license server / offline)

| Value | Notes |
|-------|-------|
| `license.key` | Inline license key. Deprecated for cloud; still the shared secret for a self-hosted license server. |
| `license.keyRef` | Secret name holding the key (data key `OPERATOR_LICENSE_KEY`). |
| `license.keyGsmRef` | GSM ID for the license key. |
| `license.file.secret` | Secret name for the license PEM (default `mirrord-operator-license`). |
| `license.file.secret.data.license.pem` | Inline PEM as a YAML literal block (air-gapped). |
| `license.pemRef` | Secret name holding a `license.pem` (air-gapped). |
| `license.pemGsmRef` | GSM ID for the license PEM. |
| `license.licenseServer` | URL of a self-hosted license server (air-gapped). |
| `license.allowSeatOverages` | `true` — allow usage above max seats (Enterprise). Set `false` to enforce. |

## Feature flags (all under `operator.*`, default `false` unless noted)

**Queue splitting:** `sqsSplitting`, `kafkaSplitting`, `rmqSplitting`, `gcpPubsubSplitting`, `azureServiceBusSplitting`, `redisPubsubSplitting`, `temporalSplitting`, `bullmqSplitting`.
- `kafkaSplittingSidecar.enabled` (default `false`) — JVM sidecar for Kafka Streams clients; `image`, `port` (33000), `requests`/`limits`.
- `temporalProxy.port` (7233), `idleKafkaSplitTtlMillis`, `kafkaSplittingTopicFormat`, `sqsSplittingLingerTimeout` (60000), `queueSplittingWaitForReadyTarget` (`true`).

**DB branching (per engine):** `mysqlBranching`, `pgBranching`, `mariadbBranching`, `mongodbBranching`, `mssqlBranching`, `redisBranching`, `dynamodbBranching`, `clickhouseBranching`, `spannerBranching`, `genericBranching`.
- `dbBranchingLiteralCredentials` (default `true`) — cluster-wide Secret perms so users can pass literal DB credentials in mirrord config instead of referencing existing Secrets.
- Per-engine pod overrides: `operator.<engine>BranchConfig.dbPod.*` — `image.registry`, `initImage.registry`, `migrationImages.flyway.registry`, `imagePullSecrets`, `imagePullPolicy`, `labels`, `annotations`, `volume`, `resources`. Generic: `genericBranchConfig.dbPod.allowedImages` (glob list; absent = all allowed).

**Preview environments:** `previewEnv` (default `false`).
- `shareIngress.shareDomain` — domain share hosts are minted under (`<slug>.<shareDomain>`, no leading `*.`); empty = no link sharing.
- `preview.cleanupAfterMins` (15), `preview.annotations`, `preview.labels`, `preview.idleHoldBufferMessages` (512), `preview.idleHoldBufferBytes` (8388608), `preview.imagePullPolicy`.

**Other operator toggles:** `metrics` (Prometheus), `applicationPauseAutoSync` (ArgoCD), `suspendFluxControllers` (Flux), `isolatePodsRestart` (`true`), `injectSessionKeyHeader` (`true`), `disableTelemetries` (Enterprise only), `requireFrontProxyClientCert` (`true`).

## Operator deployment — `operator.*`

| Value | Default | Notes |
|-------|---------|-------|
| `image` | `ghcr.io/metalbear-co/operator` | Override for internal registry. |
| `replicas` | `1` | Leader + standby replicas for HA. |
| `port` | `443` | Change to `3000`/`8443` if 443 is restricted; ensure node reachability. Binds `[::]` with `0.0.0.0` fallback. |
| `requests` / `limits` | `100m/100Mi` · `200m/200Mi` | ~200 concurrent sessions at defaults; raise for more. |
| `clusterName` | unset | Friendly cluster label in telemetry / license server. |
| `logLevel` | `mirrord=info,operator=info,kube_runtime=warn` | stdout log filter. |
| `jsonLog` | `false` | JSON stdout logs. |
| `otelLogExportUrl` / `otelTraceExportUrl` / `otelLogLevel` | unset | OTel export (independent of stdout). |
| `maxSessionTimeSeconds` | unset | Cap session lifetime. |
| `noPodTargetsSessionTimeoutMillis` | `60000` | Timeout when no ready target pods. |
| `subscribeEventBufferSize` | `2048` | `mirrord subscribe` event buffer depth. |
| `copyTarget.useAgentImage` | `true` | Copy-target dummy container uses the agent image (has `sleep`). |
| `jiraWebhookUrl` | unset | mirrord for Jira integration. |
| `extraEnv`, `extraVolumes`, `extraVolumeMounts`, `podAnnotations`, `podLabels`, `labels`, `tolerations`, `affinity`, `nodeSelector`, `imagePullSecrets` | — | Standard deployment knobs. |

### Multi-cluster — `operator.multiCluster.*`

Primary-cluster orchestration via Envoy. `enabled` (primary only), `defaultCluster` (required when enabled — where stateful ops happen), `managementOnly` (`true`), `remoteSessionTimeoutSecs` (300), `sessionTtlSecs` (60), `clusters` map. Members set `operator.multiClusterMember: true` (+ `multiClusterMemberIamGroup` for EKS IAM or `multiClusterMemberAzureGroup` for AKS Workload Identity). Per-cluster `authType`: `eks` (IAM, auto-refresh), `aks` (Workload Identity), `bearerToken` (auto-refresh), `mtls` (manual rotation). Remote-cluster credentials live in Secrets labeled `operator.metalbear.co/remote-cluster-credentials=true`.

## Agent — `agent.*`

| Value | Default | Notes |
|-------|---------|-------|
| `image` / `image.registry` / `image.tag` | `ghcr.io/metalbear-co/mirrord` | Override for internal registry. |
| `tls` | `false` | TLS-secure agent connections; requires agent ≥ 3.97.0. |
| `injectHeaders` | `true` | Agent marks whether a request went through the agent / was stolen. |
| `port` | random high port | Set a fixed port for service-mesh exclusions. |
| `extraEnv` | `{}` | Extra agent env vars. |
| `priorityClass.*` | create `mirrord-agent-pod`, value `1000000000` | PriorityClass for agent pods. |
| `extraConfig` | — | Arbitrary agent config not covered above (`json_log`, `labels`, `annotations`, `tolerations`, `privileged`, …). |

## Service accounts & TLS

- `sa.create` (`true`), `sa.name` (`mirrord-operator`), `sa.roleArn` (AWS IRSA), `sa.gcpSa` (GCP impersonation), `sa.azureClientId` (AKS Workload Identity).
- `service.name` (`mirrord-operator`).
- `tls.secret` (`mirrord-operator-tls`), `tls.useExistingSecret` (`false`), `tls.apiService.insecureSkipTLSVerify` (`true`; set `false` with a verified cert), `tls.certManager.enabled` (`false`, `createIssuer`, `issuer`, `certificate`), `tls.data.tls.crt`/`tls.key`.

## RBAC roles created by the chart

- Namespaced: `role.mirrord-operator-user` (per `roleNamespaces`).
- Cluster: `clusterRole.mirrord-operator-user-basic`, `clusterRole.mirrord-operator-user`, `clusterRole.mirrord-operator-ci` (scoped for CI / preview environments). Each accepts `labels` (for aggregated RBAC). Bind these to your users/groups/service accounts yourself.
