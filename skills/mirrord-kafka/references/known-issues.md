# Known Issues & Gotchas — Kafka Splitting

These are real issues encountered by customers and tracked internally.

## MUST-KNOW: groupIdSources is required (INT-366)
**Status:** Open bug  
The CRD schema marks `groupIdSources` as optional, but the operator returns HTTP 500 when it's omitted.  
**Action:** Always include `groupIdSources` in every topic entry. There is no valid use case for omitting it.

## min.insync.replicas not copied to ephemeral topics (INT-384)
**Status:** Open bug  
When the source topic has `replication.factor=1` and `min.insync.replicas=1`, the operator copies the replication factor but not `min.insync.replicas` to ephemeral topics. Those topics inherit the broker default (often `2`), so with `acks=all` the producer waits for 2 replicas when only 1 exists → timeout.  
**Workaround:** Add `acks: "1"` to `MirrordKafkaClientConfig` properties if using single-replica topics.

## Java KeyStore (JKS) not directly supported (INT-165)
**Status:** Open — Low priority  
The operator's Kafka client (librdkafka) only supports PEM-format credentials. Java `.jks` files must be converted first.  
**Workaround:** Convert JKS to PEM:
```sh
# Keystore → PKCS12 → PEM
keytool -importkeystore -srckeystore keystore.jks -srcstoretype JKS \
  -destkeystore keystore.p12 -deststoretype PKCS12
openssl pkcs12 -in keystore.p12 -clcerts -nokeys -out client-cert.pem
openssl pkcs12 -in keystore.p12 -nocerts -nodes -out client-key.pem

# Truststore → PKCS12 → PEM
keytool -importkeystore -srckeystore truststore.jks -srcstoretype JKS \
  -destkeystore truststore.p12 -deststoretype PKCS12
openssl pkcs12 -in truststore.p12 -nokeys -out ca-cert.pem
```
Then use `ssl.certificate.pem`, `ssl.key.pem`, `ssl.ca.pem` in the client config.

## Vault-injected config not supported (PRO-102)
**Status:** Open — Triage  
Kafka splitting only works when topic name and group ID are exposed as environment variables in the pod spec (either directly or via ConfigMap). HashiCorp Vault `vault-agent-injector` injects config at runtime, which the operator cannot read.  
**Workaround:** Expose the topic name and group ID as regular env vars in the pod template for the operator to read. The actual application can still use Vault for other config.

## Operational friction with many Kafka clusters (SOL-144)
**Status:** Open — Urgent  
Customers with many namespaces and distinct Kafka clusters find `MirrordKafkaClientConfig` cumbersome because it's scoped to the operator namespace. Each distinct Kafka cluster needs its own config resource.  
**Guidance:** Use the `parent` inheritance feature to share common properties and create child configs only for cluster-specific overrides (like different `bootstrap.servers`).

## InconsistentGroupProtocol with Kafka Streams (INT-226)
**Status:** Resolved  
The operator's librdkafka consumer was incompatible with Kafka Streams' custom partition assignment. Fixed by integrating a JVM-based Kafka proxy.  
**Note:** If a customer uses Kafka Streams, they need operator version ≥ 3.114.0 and the JVM proxy integration enabled in the Helm chart.

## Ephemeral topic cleanup errors (INT-392)
**Status:** Open — Urgent  
Operator logs may show `UnknownTopicOrPartition` errors when trying to delete temporary topics that were already cleaned up. Can lead to split timeouts.  
**If seen:** Check operator logs, restart the operator if needed. This is a known race condition being worked on.

## Strimzi-specific setup (INT-258)
**Status:** Open — Needs documentation  
Strimzi clusters use custom K8s resources for topic/user management. The operator needs permissions to manage temporary topics, and targets need permissions to read them.  
**Guidance:** For Strimzi setups, ensure the operator's Kafka user has ACLs to create/delete topics with the `mirrord-tmp-*` prefix, and that target workload users can read from those topics.

## Customizing temporary topic names
Available since chart `1.27` / operator `3.114.0`.  
Default format: `mirrord-tmp-{{RANDOM}}{{FALLBACK}}{{ORIGINAL_TOPIC}}`  
Configurable via `operator.kafkaSplittingTopicFormat` Helm value or `OPERATOR_KAFKA_SPLITTING_TOPIC_FORMAT` env var.  
All three template variables (`{{RANDOM}}`, `{{FALLBACK}}`, `{{ORIGINAL_TOPIC}}`) are required.

---

## Quick Symptom Lookup

| Symptom | Likely cause | Reference |
|---------|-------------|-----------|
| Operator returns 500 when starting session | `groupIdSources` missing from `MirrordKafkaTopicsConsumer` | INT-366 |
| Session timeout + `UnknownTopicOrPartition` in logs | Ephemeral topic cleanup race condition | INT-392 |
| Producer timeout with single-replica topics | `min.insync.replicas` not copied to ephemeral topics | INT-384 |
| `InconsistentGroupProtocol` error | Kafka Streams incompatibility (needs JVM proxy) | INT-226 |
| Splitting doesn't start, env vars not found | Vault-injected config — operator can't read it | PRO-102 |
| Auth fails with JKS credentials | librdkafka only supports PEM format | INT-165 |
| Splitting works but permissions fail on temp topics | Strimzi ACLs need `mirrord-tmp-*` prefix rules | INT-258 |

## Operator version requirements

Some fixes require a minimum operator version:
- **≥ 3.114.0**: JVM-based Kafka proxy (fixes Kafka Streams compatibility), custom temp topic naming
- Always ask the user to check their operator version when troubleshooting: `kubectl get deploy mirrord-operator -n mirrord -o jsonpath='{.spec.template.spec.containers[0].image}'`
