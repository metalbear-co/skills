# MirrordSplitConfig CRD Reference (Kafka)

The **current** resource for configuring Kafka queue splitting (replaces the deprecated `MirrordKafkaTopicsConsumer`). One `MirrordSplitConfig` describes which queues a target workload consumes and how the app discovers their names. It is shared across all queue services — this reference covers the Kafka (`kind: kafka`) shape.

**API Version:** `queues.mirrord.metalbear.co/v1`
**Kind:** `MirrordSplitConfig`
**Namespace:** the **same namespace as the target workload**.

Requires mirrord operator **3.170.0+** and CLI **3.221.0+**. On older operators, only the legacy CRDs are available.

Detect the CRD: `kubectl get crd mirrordsplitconfigs.queues.mirrord.metalbear.co`

## Top-level spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `targetRef` | object | Yes | The workload to split. `apiVersion` (e.g. `apps/v1`, `argoproj.io/v1alpha1`), `kind` (`Deployment`, `StatefulSet`, or `Rollout`), `name`. |
| `queues` | list | Yes | One or more queues consumed by the workload (see below). |
| `clientConfigs` | object | No | Set the client config once for all queues of a kind, e.g. `clientConfigs.kafka: kafka-connection`. A per-queue `clientConfig` overrides it. |
| `restart` | object | No | `restart.timeout` (seconds, default 60) — how long to wait for a new pod to become ready after the workload restart the split requires. |
| `ttl` | integer (seconds) | No | Idle window after the last Kafka session ends during which the split stays fully live, so a reconnecting session resumes **instantly** with no restart. `0`/unset skips straight to the drain window. Requires operator **3.194.0+** (ignored on older operators). See [Session reuse and drain](#session-reuse-and-drain). |
| `drainTimeout` | integer (seconds) | No | Drain window that starts once the idle window (`ttl`) elapses with no reconnect: stops forwarding new messages and lets the workload finish the already-forwarded backlog, capped at this value. On operators older than 3.194.0, this field alone controls how long the workload stays patched after its last session ends. See [Session reuse and drain](#session-reuse-and-drain). |

## queues[] entry (Kafka)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Arbitrary queue ID developers reference from `feature.split_queues` in their mirrord config. Unique within the object form. |
| `kind` | string | Yes | Must be `kafka`. |
| `clientConfig` | string | Yes* | Name of a `MirrordPropertyList` holding the Kafka client connection, resolved in the target's namespace first, then the operator's namespace (operator **3.191.0+**, for sharing one config across namespaces). *Optional if set via `spec.clientConfigs.kafka`. Falls back to a legacy `MirrordKafkaClientConfig` of the same name in the operator's namespace if no `MirrordPropertyList` exists in either namespace. |
| `appConfig.topic` | list | Yes | How the app discovers the topic name (see [appConfig sources](#appconfig-sources)). |
| `appConfig.groupId` | list | one of groupId/appId | How the app discovers the consumer **group id**. Standard consumers. The operator's forwarder joins this group; the consumer env is left untouched. |
| `appConfig.appId` | list | one of groupId/appId | How the app discovers the Kafka **Streams application id**. The operator patches this var to a fresh app id. Requires the Java client (`mirrord.client_implementation: java`). |

Exactly one of `appConfig.groupId` or `appConfig.appId` must be set.

## appConfig sources

Each `appConfig.topic` / `groupId` / `appId` is a list of source entries. Fields per entry:

| Field | Description |
|-------|-------------|
| `env` | Exact environment variable name holding the value. |
| `envLike` | Regex matching environment variable names (use instead of `env`). |
| `fallback` | Fallback value if the variable is absent (only valid with `env`). The env var is still rewritten to point at the temporary topic. |
| `valueSelector` | A jq expression extracting the value from the variable's value — for env vars that hold JSON rather than a plain name. |
| `valuePattern` | A regex for when the name is embedded in a larger string. The capture group (named `value`, else the first group) marks the part swapped for the temporary topic; surrounding text is kept. |
| `containers` | Limit to specific containers (optional; defaults to all non-infra containers). |

**Env var readability:** the operator can only read a consumer's env vars if they are either (1) defined directly in the pod template via `value` or `valueFrom` (configMapKeyRef), or (2) loaded from ConfigMaps via `envFrom`. Vault-injected env vars are not readable.

## Session reuse and drain

When the **last** Kafka session on a workload ends, the operator does not tear the split down right away. Two sequential windows run first, before the temporary queues are deleted and the workload is unpatched:

1. **Idle window — `spec.ttl`.** The split stays fully live: the operator keeps forwarding the original topic into the temporary topic the patched workload reads. A session that reconnects during this window reuses the split **instantly**, with no restart.
2. **Drain window — `spec.drainTimeout`.** Starts once the idle window elapses with no reconnect. The operator stops forwarding new messages and lets the patched workload finish consuming what's already in the temporary topic. A session that reconnects during this window resumes forwarding instead of rebuilding from scratch. Ends **early** once the temporary topic is fully drained, capped at `drainTimeout`.

| Field | Phase | Effect |
|-------|-------|--------|
| `spec.ttl` | Idle | `N`: keep the split warm for up to `N` seconds so a reconnecting session resumes instantly. `0`/unset: skip straight to the drain window when the last session ends. |
| `spec.drainTimeout` | Drain | `N`: let the workload finish the backlog for up to `N` seconds, ending early once drained. `0`: unpatch immediately — unread temporary-topic messages are lost. Unset: no cap, wait until the backlog is fully consumed. |

> **Version requirement:** `spec.ttl`, and draining the temporary topic before unpatch (capped by `spec.drainTimeout`), require mirrord operator **3.194.0+**. On earlier operators, `spec.drainTimeout` alone controls how long the workload stays patched after the last session ends — the old single-field behavior.

> The legacy `operator.idleKafkaSplitTtlMillis` (`OPERATOR_KAFKA_SPLITTING_TTL`) Helm value only affects legacy `MirrordKafkaTopicsConsumer` objects that leave `spec.splitTtl` unset. It is **not** a cluster-wide default for `MirrordSplitConfig`, and there is no cluster-wide equivalent — set `spec.ttl`/`spec.drainTimeout` per config instead.

## Full example (standard consumer)

```yaml
apiVersion: queues.mirrord.metalbear.co/v1
kind: MirrordSplitConfig
metadata:
  name: meme-app-split
  namespace: meme
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: meme-app
  queues:
    - id: views-topic
      kind: kafka
      clientConfig: kafka-connection
      appConfig:
        topic:
          - env: KAFKA_TOPIC_NAME
            fallback: views-topic       # optional, used when the var is absent
            containers:
              - consumer
        groupId:
          - env: KAFKA_GROUP_ID
            containers:
              - consumer
```

## Kafka Streams example

```yaml
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: streams-app
  queues:
    - id: orders-topic
      kind: kafka
      clientConfig: kafka-connection      # MirrordPropertyList must set mirrord.client_implementation: java
      appConfig:
        topic:
          - env: KAFKA_TOPIC_NAME
            containers: [app]
        appId:
          - env: KAFKA_STREAMS_APP_ID
            containers: [app]
```

## Field mapping from the deprecated CRD

| `MirrordKafkaTopicsConsumer` (deprecated) | `MirrordSplitConfig` (new) |
|-------------------------------------------|----------------------------|
| `consumerApiVersion` / `consumerKind` / `consumerName` | `spec.targetRef.apiVersion` / `kind` / `name` |
| `topics[].id` | `spec.queues[].id` |
| `topics[].nameSources[].directEnvVar` | `appConfig.topic[]` (`variable`→`env`, `container`→`containers`, `fallback`→`fallback`) |
| `topics[].groupIdSources` | `appConfig.groupId[]` |
| `topics[].applicationIdSources` | `appConfig.appId[]` |
| `topics[].clientConfig` (a `MirrordKafkaClientConfig`) | `spec.queues[].clientConfig` (a `MirrordPropertyList` in the target namespace, or the same legacy name as a fallback) |
| `consumerRestartTimeout` | `spec.restart.timeout` |
| `splitTtl` | `spec.ttl` |
