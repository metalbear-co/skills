# MirrordPropertyList CRD Reference (Kafka client connection)

The **current** resource for the operator's Kafka client connection (replaces the deprecated `MirrordKafkaClientConfig`). A `MirrordSplitConfig` queue references it by name via `clientConfig`.

**API Version:** `mirrord.metalbear.co/v1`
**Kind:** `MirrordPropertyList`
**Namespace:** looked up in two places, in order: (1) the **target workload's namespace** (also the namespace of its `MirrordSplitConfig`) — the recommended default, and it wins if a list of the same name also exists in the operator's namespace; (2) the **operator's own namespace**, as a fallback that lets one connection config be shared across many teams/namespaces (requires operator **3.191.0+**; earlier operators only look in the target's namespace). ConfigMap/Secret refs inside a property list resolve in whichever namespace the list itself was found in. A property list in the target's namespace that the operator can't parse fails the session outright — it does not fall through to the operator's namespace. This lookup is unrelated to the deprecated `MirrordKafkaClientConfig`, which only ever lived in the operator's namespace.

## spec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `properties` | list of `{name, value}` or `{name, valueFrom}` | Yes | Kafka client properties, passed straight to the underlying client. A few `mirrord.`-prefixed keys are consumed by the operator (see below). |

Each property is either:
- `- name: <key>` / `value: "<string>"` — inline value, or
- `- name: <key>` / `valueFrom: { secretKeyRef: { name: <secret>, key: <key> } }` — read from a Kubernetes Secret.

Full list of Kafka client properties: [librdkafka CONFIGURATION.md](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md).

## Operator-specific (`mirrord.`-prefixed) keys

Consumed by the operator, not forwarded to the Kafka client:

| Key | Values | Description |
|-----|--------|-------------|
| `mirrord.client_implementation` | `librdkafka` (default), `java` | Kafka client backend. Use `java` for **Kafka Streams** consumers (`appConfig.appId`). |
| `mirrord.auth.kind` | `MSK_IAM` | Extra authentication mechanism (only supported value). See [MSK IAM](#aws-msk-iam). |
| `mirrord.auth.aws_region` | e.g. `eu-south-1` | AWS region; required when `mirrord.auth.kind` is `MSK_IAM`. |
| `mirrord.temporary_group_id` | `"true"` | Works around `INCONSISTENT_GROUP_PROTOCOL` errors from clients that advertise their own partition-assignment protocol (e.g. KafkaJS). Requires operator **3.195.0+**. See [KafkaJS / custom group protocols](#kafkajs--custom-group-protocols-mirrordtemporary_group_id). |

> **Do not set `group.id`.** The consumer group used by the operator's own client is managed by mirrord.

## Namespace lookup order and legacy fallback

The operator resolves a `clientConfig` name in this order:

1. A `MirrordPropertyList` in the target's namespace.
2. A `MirrordPropertyList` in the operator's namespace (operator **3.191.0+**) — for sharing one connection config across namespaces.
3. A legacy `MirrordKafkaClientConfig` of the same name in the operator's namespace, if no `MirrordPropertyList` was found in either namespace above.

This keeps older setups working while you migrate.

## Common properties

| Property | Typical value | Notes |
|----------|---------------|-------|
| `bootstrap.servers` | `kafka.default.svc.cluster.local:9092` | Required. |
| `security.protocol` | `PLAINTEXT`, `SSL`, `SASL_SSL`, `SASL_PLAINTEXT` | Depends on cluster auth. |
| `sasl.mechanism` | `PLAIN`, `SCRAM-SHA-256`, `SCRAM-SHA-512`, `OAUTHBEARER` | For SASL. |
| `sasl.username` / `sasl.password` | credentials | For SASL PLAIN/SCRAM — use `valueFrom.secretKeyRef`. |
| `ssl.certificate.pem` / `ssl.key.pem` / `ssl.ca.pem` | PEM contents | For SSL/mTLS. |
| `ssl.key.password` | string | If the private key is password-protected. |

## Examples

### Plaintext (dev)

```yaml
apiVersion: mirrord.metalbear.co/v1
kind: MirrordPropertyList
metadata:
  name: kafka-connection
  namespace: meme
spec:
  properties:
    - name: bootstrap.servers
      value: kafka.default.svc.cluster.local:9092
    - name: security.protocol
      value: PLAINTEXT
```

### AWS MSK IAM

```yaml
spec:
  properties:
    - name: bootstrap.servers
      value: b-1.mycluster.kafka.eu-south-1.amazonaws.com:9098
    - name: mirrord.auth.kind
      value: MSK_IAM
    - name: mirrord.auth.aws_region
      value: eu-south-1
```

When `mirrord.auth.kind: MSK_IAM`, the operator automatically adds `sasl.mechanism=OAUTHBEARER` and `security.protocol=SASL_SSL`. Tokens are produced via the default AWS credential provider chain — the easiest path is IAM role assumption, annotating the operator's service account with the role ARN via `sa.roleArn` in the operator Helm chart.

### SSL/mTLS via Kubernetes Secret (recommended for credentials)

Never inline PEM key material or passwords. Store them in a Secret and reference with `valueFrom.secretKeyRef`:

```yaml
spec:
  properties:
    - name: bootstrap.servers
      value: kafka.default.svc.cluster.local:9093
    - name: security.protocol
      value: SSL
    - name: ssl.certificate.pem
      valueFrom:
        secretKeyRef:
          name: mirrord-kafka-ssl
          key: ssl.certificate.pem
    - name: ssl.key.pem
      valueFrom:
        secretKeyRef:
          name: mirrord-kafka-ssl
          key: ssl.key.pem
    - name: ssl.ca.pem
      valueFrom:
        secretKeyRef:
          name: mirrord-kafka-ssl
          key: ssl.ca.pem
```

> By default the operator has read access only to secrets in the operator's namespace, even though the `MirrordPropertyList` itself lives in the target's namespace. Confirm the referenced Secret is reachable by the operator; if not, the admin must grant read access.

### Kafka Streams (Java client)

```yaml
spec:
  properties:
    - name: bootstrap.servers
      value: kafka.default.svc.cluster.local:9092
    - name: mirrord.client_implementation
      value: java
```

Kafka Streams also requires the operator's Kafka sidecar (`operator.kafkaSplittingSidecar.enabled: true` in the Helm chart).

### KafkaJS / custom group protocols (`mirrord.temporary_group_id`)

Some client libraries — KafkaJS, for example — advertise their own partition-assignment protocol name, which the operator's librdkafka-based consumer cannot join a group with. This surfaces as an `INCONSISTENT_GROUP_PROTOCOL` error when a split session starts.

Set `mirrord.temporary_group_id: "true"` on the Kafka `MirrordPropertyList`:

```yaml
spec:
  properties:
    - name: bootstrap.servers
      value: kafka.default.svc.cluster.local:9092
    - name: mirrord.temporary_group_id
      value: "true"
```

With this set, splits patch the workload's consumer-group env vars (`appConfig.groupId`) to a generated temporary group, alongside the topic rewrite. The operator keeps the original group to itself, so it never negotiates a protocol with the application's client — any client library works. Offsets are preserved: the operator keeps committing into the original group, and the workload resumes exactly where it left off when the split ends.

Temporary group names follow the temporary topic name format (`mirrord-tmp-...`) — if you use group ACLs, the application's credentials must be allowed to join groups with that prefix, and the operator's credentials need `DeleteGroups` for cleanup. Requires operator **3.195.0+**.

## JKS credentials → PEM

The client only supports PEM. Convert a Java KeyStore first:

```sh
keytool -importkeystore -srckeystore keystore.jks -srcstoretype JKS \
  -destkeystore keystore.p12 -deststoretype PKCS12
openssl pkcs12 -in keystore.p12 -clcerts -nokeys -out client-cert.pem
openssl pkcs12 -in keystore.p12 -nocerts -nodes -out client-key.pem

keytool -importkeystore -srckeystore truststore.jks -srcstoretype JKS \
  -destkeystore truststore.p12 -deststoretype PKCS12
openssl pkcs12 -in truststore.p12 -nokeys -out ca-cert.pem
```

Then use `ssl.certificate.pem`, `ssl.key.pem`, `ssl.ca.pem` (via a Secret).

## Mapping from the deprecated resource

`MirrordKafkaClientConfig` properties map one-to-one onto `MirrordPropertyList` properties. Differences:
- **Namespace:** `MirrordPropertyList` lives in the **target's** namespace; `MirrordKafkaClientConfig` lived in the **operator's** namespace.
- **MSK IAM:** the old `authenticationExtra: { kind: MSK_IAM, awsRegion: ... }` becomes the `mirrord.auth.kind` / `mirrord.auth.aws_region` properties.
- **Secrets:** the old `loadFromSecret` becomes per-property `valueFrom.secretKeyRef`.
- The old `parent` inheritance has no direct equivalent — repeat shared properties, or use `spec.clientConfigs.kafka` on the `MirrordSplitConfig` to share one `MirrordPropertyList` across queues.
