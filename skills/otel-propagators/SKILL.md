---
name: otel-propagators
description: >
  Configure OpenTelemetry context propagation (OTEL_PROPAGATORS) for services running in Kubernetes,
  especially when using mirrord to intercept or steal traffic. Use this skill whenever the user
  mentions OTEL_PROPAGATORS, OpenTelemetry propagators, trace context headers, W3C tracecontext,
  B3 headers, distributed tracing setup, OTel auto-instrumentation configuration, or configuring
  header propagation for mirrord sessions. Also trigger when someone asks about traceparent headers,
  baggage propagation, connecting local dev tracing to a cluster, or ensuring downstream services
  see the correct trace context when traffic is intercepted by mirrord. This skill covers env vars,
  Kubernetes Instrumentation CRDs, docker-compose, Spring Boot properties, and local dev config
  for mirrord users.
metadata:
  author: MetalBear
  version: "1.0"
---

# OpenTelemetry Propagators Configuration Skill

## Purpose

Help developers configure `OTEL_PROPAGATORS` and related OpenTelemetry SDK environment variables
so that trace context headers are properly injected and extracted across services — especially
when using **mirrord** to intercept traffic from a Kubernetes cluster.

### Why This Matters for mirrord Users

When a developer runs `mirrord` in steal or mirror mode, their local process handles HTTP
requests that originated in the cluster. If the upstream service injected trace headers
(e.g., `traceparent`, `X-B3-TraceId`), the local process must:

1. **Extract** the incoming trace context from request headers
2. **Propagate** it to any downstream calls the local process makes
3. Use **matching propagator formats** on both sides (cluster + local)

Without matching `OTEL_PROPAGATORS` configuration, trace continuity breaks and downstream
services lose visibility into the request chain.

## Critical First Step

**Read the propagators reference before generating any configuration:**

```
view /path/to/this/skill/references/propagators-reference.md
```

This file contains the full list of valid propagator values, per-language quirks,
Kubernetes Instrumentation CRD patterns, and common pitfalls.

## Workflow

### 1. Gather Context

Ask the user (only if not already clear from context):

- **What language/framework?** (Java, Python, Node.js, Go, .NET, Ruby)
- **What propagation format does the cluster use?** (W3C tracecontext is default; may also need B3 for service meshes like Istio/Linkerd)
- **Deployment mode?** (env vars, K8s Instrumentation CR via OTel Operator, docker-compose, Spring Boot properties)
- **Are they using mirrord?** If yes, generate BOTH cluster-side and local-side config
- **Collector endpoint?** (e.g., `http://otel-collector:4317`)

### 2. Select Propagators

Default recommendation: `tracecontext,baggage`

Add others based on context:
| Scenario | Propagators |
|---|---|
| Standard W3C (recommended default) | `tracecontext,baggage` |
| Istio / Envoy service mesh | `tracecontext,baggage,b3,b3multi` |
| Zipkin ecosystem | `b3multi` or `b3` |
| AWS X-Ray | `xray` (add `tracecontext,baggage` too) |
| Jaeger (legacy) | `jaeger` (add `tracecontext,baggage` too) |
| Mixed / migration | `tracecontext,baggage,b3multi` |

### 3. Generate Configuration

Based on deployment mode, produce ONE of the following output types:

#### A) Environment Variables (universal)

```bash
export OTEL_PROPAGATORS="tracecontext,baggage"
export OTEL_SERVICE_NAME="my-service"
export OTEL_TRACES_EXPORTER="otlp"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
```

#### B) Kubernetes Instrumentation CR (OTel Operator)

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: my-instrumentation
  namespace: <namespace>
spec:
  exporter:
    endpoint: http://otel-collector.<namespace>.svc.cluster.local:4317
  propagators:
    - tracecontext
    - baggage
  sampler:
    type: parentbased_traceidratio
    argument: "1"
```

Plus the annotation for the Deployment:

```yaml
annotations:
  instrumentation.opentelemetry.io/inject-<language>: "true"
```

#### C) Kubernetes Deployment Patch (no OTel Operator)

```yaml
spec:
  template:
    spec:
      containers:
        - name: my-container
          env:
            - name: OTEL_PROPAGATORS
              value: "tracecontext,baggage"
            - name: OTEL_SERVICE_NAME
              value: "my-service"
            - name: OTEL_TRACES_EXPORTER
              value: "otlp"
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://otel-collector:4317"
```

#### D) Spring Boot `application.properties`

```properties
otel.propagators=tracecontext,baggage
otel.resource.attributes.service.name=my-service
otel.exporter.otlp.endpoint=http://otel-collector:4317
```

#### E) Docker Compose

```yaml
services:
  my-service:
    environment:
      - OTEL_PROPAGATORS=tracecontext,baggage
      - OTEL_SERVICE_NAME=my-service
      - OTEL_TRACES_EXPORTER=otlp
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

### 4. Generate mirrord Local Dev Config (if applicable)

When the user is using mirrord, also generate the local-side configuration.
The local process must use the **same propagator set** as the cluster services.

**Environment variables for local dev session:**

```bash
# Match cluster propagators exactly
export OTEL_PROPAGATORS="tracecontext,baggage"
export OTEL_SERVICE_NAME="my-service-local"
export OTEL_TRACES_EXPORTER="otlp"
# Point to local or cluster collector
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
```

**Tip:** If the cluster has an OTel Collector accessible via mirrord's network,
the local process can reach it at its cluster-internal address since mirrord
proxies outgoing traffic to the cluster.

**mirrord.json env configuration** — make sure `OTEL_PROPAGATORS` is included
in the mirrored environment:

```json
{
  "feature": {
    "env": {
      "include": "OTEL_PROPAGATORS;OTEL_SERVICE_NAME;OTEL_TRACES_EXPORTER;OTEL_EXPORTER_OTLP_ENDPOINT;OTEL_EXPORTER_OTLP_PROTOCOL;OTEL_TRACES_SAMPLER;OTEL_TRACES_SAMPLER_ARG;OTEL_RESOURCE_ATTRIBUTES"
    }
  }
}
```

Or if the user prefers to override locally (e.g., different service name):

```json
{
  "feature": {
    "env": {
      "include": "OTEL_PROPAGATORS;OTEL_EXPORTER_OTLP_ENDPOINT;OTEL_EXPORTER_OTLP_PROTOCOL",
      "override": {
        "OTEL_SERVICE_NAME": "my-service-local-dev"
      }
    }
  }
}
```

### 5. Validate

After generating config, verify:

1. **Propagator values are valid** — only use values from the reference:
   `tracecontext`, `baggage`, `b3`, `b3multi`, `jaeger`, `ottrace`, `xray`, `xray-lambda`
2. **Cluster and local propagators match** — mismatch = broken traces
3. **No duplicates** — the spec requires deduplication
4. **Language-specific gotchas** are addressed (see reference)

## Response Format

1. Brief explanation of what's being configured and why (1-2 sentences)
2. Generated config in the appropriate format (code block)
3. If mirrord is involved: both cluster-side and local-side configs
4. Key callouts: gotchas, language-specific notes, or mesh considerations
5. Verification steps: how to confirm headers are propagating

## Common Pitfalls

- **Python + gRPC**: Python auto-instrumentation defaults to `http/protobuf`;
  if collector endpoint is `:4317` (gRPC), set `OTEL_EXPORTER_OTLP_ENDPOINT`
  to port `4318` instead
- **Istio/Linkerd**: Service meshes often use B3 headers; add `b3,b3multi` to
  propagators alongside `tracecontext,baggage`
- **mirrord env mismatch**: If `env.include` doesn't capture `OTEL_PROPAGATORS`,
  the local process falls back to SDK defaults which may differ from cluster config
- **Spring Boot**: System property `otel.propagators` overrides the env var
  `OTEL_PROPAGATORS`; check both
- **Collector not reachable locally**: Use mirrord's network proxying so the
  local process can reach the cluster collector at its service DNS name
- **OTEL_SDK_DISABLED=true does NOT affect propagators** — propagators still work
  even when the SDK is disabled

## What NOT to Do

- Don't recommend `OTEL_PROPAGATORS` values that aren't in the OTel spec
- Don't generate a Kubernetes `Instrumentation` CR without specifying propagators
  explicitly (the defaults may vary between Operator versions)
- Don't forget the `baggage` propagator — it's almost always needed alongside
  `tracecontext` for full context propagation
- Don't set OTEL env vars via Dockerfile `ENV` if the OTel Operator is also
  injecting them — they'll conflict
