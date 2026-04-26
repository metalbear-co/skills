---
name: mirrord-kafka
description: >
  Helps DevOps engineers configure mirrord Operator's Kafka queue splitting feature end-to-end.
  Generates MirrordKafkaClientConfig and MirrordKafkaTopicsConsumer Kubernetes CRD YAMLs,
  the matching mirrord.json split_queues section, and Helm value guidance.
  Use this skill whenever the user mentions Kafka splitting with mirrord, MirrordKafkaClientConfig,
  MirrordKafkaTopicsConsumer, Kafka queue splitting, Kafka topic splitting, configuring mirrord
  with Kafka, setting up Kafka for mirrord operator, or troubleshooting Kafka splitting sessions.
  Also trigger when users mention split_queues with queue_type Kafka, or ask about connecting
  mirrord to a Kafka cluster. This is a Team/Enterprise feature of mirrord.
metadata:
  author: MetalBear
  version: "1.0"
---

# mirrord Kafka Splitting Configuration Skill

## Purpose

Guide DevOps engineers through the full setup of mirrord Operator's Kafka queue splitting:

1. **Helm values** — Enable `operator.kafkaSplitting` in the mirrord-operator chart
2. **MirrordKafkaClientConfig** — Configure how the operator connects to Kafka
3. **MirrordKafkaTopicsConsumer** — Link a workload to the topics it consumes
4. **mirrord.json** — The `feature.split_queues` section developers use to filter messages
5. **Validation** — Check generated YAML for required fields and cross-references
6. **Troubleshooting** — Surface known issues and workarounds

## Critical First Steps

**Step 1: Load reference files**

Read the reference files relevant to the user's request:

- `references/kafka-client-config-crd.md` — `MirrordKafkaClientConfig` field spec, auth patterns
- `references/kafka-topics-consumer-crd.md` — `MirrordKafkaTopicsConsumer` field spec
- `references/known-issues.md` — Active bugs, gotchas, and workarounds from the field

Always read the CRD reference for any resource you're generating. Read known-issues when generating any config (to proactively warn) or when the user reports problems.

**Step 2: Inspect the cluster (if kubectl is available)**

Before asking the user a bunch of questions, try to learn from the cluster itself. Run these commands to auto-discover context:

```bash
# Current context and cluster info
kubectl config current-context
kubectl cluster-info 2>/dev/null | head -5

# Check if mirrord operator is installed and which namespace
kubectl get ns mirrord --no-headers 2>/dev/null
kubectl get deploy -n mirrord -l app=mirrord-operator --no-headers 2>/dev/null

# Check if Kafka splitting CRDs exist (confirms feature is enabled)
kubectl get crd mirrordkafkaclientconfigs.queues.mirrord.metalbear.co --no-headers 2>/dev/null
kubectl get crd mirrordkafkatopicsconsumers.queues.mirrord.metalbear.co --no-headers 2>/dev/null

# List existing Kafka configs and topic consumers (if any)
kubectl get mirrordkafkaclientconfigs -n mirrord --no-headers 2>/dev/null
kubectl get mirrordkafkatopicsconsumers --all-namespaces --no-headers 2>/dev/null
```

If the user mentions a specific namespace or workload, also inspect it:
```bash
# Get the target workload's pod spec to extract env vars, container names
kubectl get deployment/<name> -n <ns> -o yaml 2>/dev/null
# Or for StatefulSet/Rollout
kubectl get statefulset/<name> -n <ns> -o yaml 2>/dev/null

# Look for Kafka-related services in the cluster
kubectl get svc --all-namespaces --no-headers 2>/dev/null | grep -i kafka
```

This auto-discovery reduces the number of questions you need to ask. For instance, if you find a Kafka service at `kafka.default.svc.cluster.local:9092`, you can propose it as the bootstrap server. If you find the target deployment's env vars, you can extract topic and group ID variable names directly.

If kubectl is not available or the user doesn't have cluster access, fall back to asking.

**Step 3: Gather remaining context**

After inspecting the cluster, ask only for what you couldn't discover. Most setups require these inputs:

For `MirrordKafkaClientConfig`:
- Kafka bootstrap servers address (may be discoverable from cluster services)
- Authentication method (none, SASL, SSL/mTLS, MSK IAM)
- Whether credentials are in a K8s Secret

For `MirrordKafkaTopicsConsumer`:
- Target workload name, kind (Deployment/StatefulSet/Rollout), and namespace
- For each topic: the env var holding the topic name, and the env var holding the consumer group ID
- Which container in the pod spec holds these env vars
- The name of the `MirrordKafkaClientConfig` to reference

If the user provides a pod spec, deployment YAML, or Helm values — or if you retrieved them from the cluster — extract these details directly rather than asking.

## Generation Workflow

### 1. Helm Values

Remind the user to enable Kafka splitting in the operator chart if they haven't:

```yaml
operator:
  kafkaSplitting: true
```

Mention this only once, early in the conversation. Don't repeat it.

### 2. Generate MirrordKafkaClientConfig

Key rules:
- **Must be in the operator's namespace** (default: `mirrord`)
- **Never set `group.id`** — the operator overrides it at runtime
- Use `loadFromSecret` for sensitive values (passwords, certs) rather than inline
- Use `parent` inheritance when the user has multiple Kafka clusters sharing common config
- For MSK/AWS: use `authenticationExtra` with `kind: MSK_IAM`
- **Default `security.protocol` to `SASL_SSL`** when the user mentions SASL but doesn't specify transport. This is the safer default. Flag the assumption: "I've defaulted to `SASL_SSL` — if your broker uses plaintext transport, change this to `SASL_PLAINTEXT`."

Output format:
```yaml
apiVersion: queues.mirrord.metalbear.co/v1alpha
kind: MirrordKafkaClientConfig
metadata:
  name: <descriptive-name>
  namespace: mirrord
spec:
  properties:
  - name: bootstrap.servers
    value: <broker-address>
  # ... additional properties based on auth method
```

### 3. Generate MirrordKafkaTopicsConsumer

Key rules:
- **Must be in the same namespace as the target workload**
- **`groupIdSources` is REQUIRED** — omitting it causes a 500 error even though the schema says optional
- Each topic's `id` is what developers will reference in their mirrord.json
- `clientConfig` references a `MirrordKafkaClientConfig` by name (in the operator namespace)
- Choose descriptive topic IDs — they become the contract between DevOps and developers
- **For StatefulSet or Rollout targets:** consider setting `consumerRestartTimeout` (default 60s) and `splitTtl`. StatefulSets and Rollouts often restart slower than Deployments. `splitTtl` keeps the workload patched after the last session ends, avoiding a full restart if a new session starts soon — useful for teams actively developing.

Output format:
```yaml
apiVersion: queues.mirrord.metalbear.co/v1alpha
kind: MirrordKafkaTopicsConsumer
metadata:
  name: <workload>-topics-consumer
  namespace: <workload-namespace>
spec:
  consumerApiVersion: apps/v1
  consumerKind: <Deployment|StatefulSet|Rollout>
  consumerName: <workload-name>
  topics:
  - id: <topic-id>
    clientConfig: <kafka-client-config-name>
    nameSources:
    - directEnvVar:
        container: <container-name>
        variable: <TOPIC_ENV_VAR>
    groupIdSources:
    - directEnvVar:
        container: <container-name>
        variable: <GROUP_ID_ENV_VAR>
```

### 4. Generate mirrord.json split_queues section

After generating the CRDs, show the developer-facing mirrord.json config that references the topic IDs:

```json
{
  "operator": true,
  "target": "deployment/<workload>/container/<container>",
  "feature": {
    "split_queues": {
      "<topic-id>": {
        "queue_type": "Kafka",
        "message_filter": {
          "<header-name>": "<regex-pattern>"
        }
      }
    }
  }
}
```

Explain that `message_filter` matches Kafka message **headers** (not body), and all specified headers must match for a message to be routed to the local app. An empty `message_filter: {}` means match-none (the local app gets zero messages from that topic).

If the user already has the mirrord config skill installed, mention they can use it for the full mirrord.json — this skill focuses on the Kafka-specific parts.

## Validation

After generating YAML, perform these checks:

### Required field checks
- [ ] `MirrordKafkaClientConfig` has `metadata.namespace` set to operator namespace
- [ ] `MirrordKafkaClientConfig` has at least `bootstrap.servers` in properties
- [ ] `MirrordKafkaClientConfig` does NOT set `group.id`
- [ ] `MirrordKafkaTopicsConsumer` has all three consumer fields (`consumerApiVersion`, `consumerKind`, `consumerName`)
- [ ] Every topic entry has `id`, `clientConfig`, `nameSources`, AND `groupIdSources`
- [ ] Topic IDs are unique within the resource
- [ ] `consumerKind` is one of: `Deployment`, `StatefulSet`, `Rollout`

### Cross-reference checks
- [ ] `clientConfig` in topics references a `MirrordKafkaClientConfig` that exists (or is being generated alongside)
- [ ] Topic IDs used in mirrord.json match topic IDs in the `MirrordKafkaTopicsConsumer`
- [ ] Target in mirrord.json matches the workload referenced in the topics consumer

### Proactive warnings
Check known-issues.md and warn about:
- Single-replica topics → mention the `min.insync.replicas` workaround
- JKS credentials → offer conversion commands
- Vault-injected config → explain the env var requirement
- Strimzi clusters → mention ACL requirements for `mirrord-tmp-*` topics

Present validation results clearly:
```
✅ Validation passed
⚠️ Warning: [description + workaround]
❌ Error: [what's wrong + how to fix]
```

## Response Format

### For full setup (new user)
1. Brief overview of the 3 resources needed
2. Generated `MirrordKafkaClientConfig` YAML
3. Generated `MirrordKafkaTopicsConsumer` YAML
4. Example `mirrord.json` snippet for developers
5. Validation results
6. Any applicable warnings from known issues

### For single resource generation
1. Generated YAML
2. Validation results
3. Applicable warnings

### For troubleshooting
1. Read `references/known-issues.md` — use the **Quick Symptom Lookup** table to match symptoms
2. Ask the user for their operator version: `kubectl get deploy mirrord-operator -n mirrord -o jsonpath='{.spec.template.spec.containers[0].image}'`
3. Match the user's symptoms to known issues
4. Provide specific workaround or next steps
5. Suggest checking operator logs: `kubectl logs -n mirrord -l app==mirrord-operator --tail 100`

## Common Scenarios

**"Set up Kafka splitting for my deployment"**
→ Ask for: bootstrap servers, auth method, workload name/namespace, topic env vars, group ID env vars
→ Generate both CRDs + mirrord.json example

**"My Kafka splitting session times out"**
→ Read known-issues. Check for INT-384 (min.insync.replicas) or INT-392 (ephemeral topic cleanup).
→ Suggest increasing `consumerRestartTimeout`, checking operator logs.

**"We use JKS for Kafka auth"**
→ Provide JKS→PEM conversion commands from known-issues.
→ Generate config using PEM properties or secret reference.

**"We have multiple Kafka clusters"**
→ Use parent/child `MirrordKafkaClientConfig` inheritance.
→ One base config with shared properties, child configs per cluster.

**"How do developers filter messages?"**
→ Explain `message_filter` matches Kafka headers via regex.
→ Suggest using tracing headers (like `baggage`) if the framework supports them.
→ Note that body/key filtering is not yet supported (INT-315, INT-167).

## What NOT to Do

- Don't hallucinate CRD fields — only use fields from the reference files
- Don't set `group.id` in `MirrordKafkaClientConfig` — the operator overrides it
- Don't generate `MirrordKafkaClientConfig` outside the operator namespace
- Don't omit `groupIdSources` — it will 500 even though schema says optional
- Don't suggest Vault-injected config will work — it doesn't yet
- Don't promise body/key-based filtering for Kafka — only header-based filtering is supported
