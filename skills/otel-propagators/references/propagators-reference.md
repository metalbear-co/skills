# OpenTelemetry Propagators Reference

## Table of Contents

1. [Valid Propagator Values](#valid-propagator-values)
2. [Headers Injected by Each Propagator](#headers-injected)
3. [Language-Specific Setup](#language-specific-setup)
4. [Kubernetes Instrumentation CRD Patterns](#kubernetes-patterns)
5. [Auto-Instrumentation Annotations](#annotations)
6. [mirrord Integration Patterns](#mirrord-patterns)
7. [Troubleshooting](#troubleshooting)

---

## Valid Propagator Values

These are the only valid values for `OTEL_PROPAGATORS` per the OpenTelemetry specification.
Values are comma-separated, no spaces.

| Value | Propagator Class | Use Case |
|---|---|---|
| `tracecontext` | W3CTraceContextPropagator | **Default**. W3C standard. Use everywhere. |
| `baggage` | W3CBaggagePropagator | Propagates key-value pairs across services. Almost always paired with `tracecontext`. |
| `b3` | B3Propagator (single-header) | Zipkin compatibility. Single `b3` header. |
| `b3multi` | B3Propagator (multi-header) | Zipkin compatibility. Multiple `X-B3-*` headers. Common in service meshes. |
| `jaeger` | JaegerPropagator | Legacy Jaeger. Uses `uber-trace-id` header. |
| `ottrace` | OtTracePropagator | OpenTracing compatibility. |
| `xray` | AwsXrayPropagator | AWS X-Ray. Uses `X-Amzn-Trace-Id` header. |
| `xray-lambda` | AwsXrayLambdaPropagator | AWS Lambda variant of X-Ray. |

**Default if unset:** `tracecontext,baggage` (most SDK implementations)

**Important:** Values MUST be deduplicated. Setting `tracecontext,tracecontext` is invalid.

---

## Headers Injected by Each Propagator {#headers-injected}

Understanding which headers each propagator injects/extracts is critical for debugging
and for ensuring mirrord passes the right headers through.

### W3C Trace Context (`tracecontext`)
```
traceparent: 00-<trace-id>-<span-id>-<flags>
tracestate: <vendor>=<value>
```

### W3C Baggage (`baggage`)
```
baggage: key1=value1,key2=value2
```

### B3 Single Header (`b3`)
```
b3: <trace-id>-<span-id>-<sampling>-<parent-span-id>
```

### B3 Multi Header (`b3multi`)
```
X-B3-TraceId: <trace-id>
X-B3-SpanId: <span-id>
X-B3-ParentSpanId: <parent-span-id>
X-B3-Sampled: 1
```

### Jaeger (`jaeger`)
```
uber-trace-id: <trace-id>:<span-id>:<parent-span-id>:<flags>
```

### AWS X-Ray (`xray`)
```
X-Amzn-Trace-Id: Root=1-<hex-timestamp>-<id>;Parent=<parent-id>;Sampled=1
```

---

## Language-Specific Setup {#language-specific-setup}

### Java

**Auto-instrumentation agent:**
```bash
export JAVA_TOOL_OPTIONS="-javaagent:/path/to/opentelemetry-javaagent.jar"
export OTEL_PROPAGATORS="tracecontext,baggage"
export OTEL_SERVICE_NAME="my-java-service"
```

Or via system property:
```
-Dotel.propagators=tracecontext,baggage
```

**Available propagator artifacts (Java-specific):**
- `tracecontext` → W3CTraceContextPropagator (included in SDK)
- `baggage` → W3CBaggagePropagator (included in SDK)
- `b3`, `b3multi` → requires `io.opentelemetry:opentelemetry-extension-trace-propagators`
- `jaeger` → requires `io.opentelemetry:opentelemetry-extension-trace-propagators`
- `ottrace` → requires `io.opentelemetry.contrib:opentelemetry-extension-trace-propagators`
- `xray` → requires `io.opentelemetry.contrib:opentelemetry-aws-xray-propagator`

**Spring Boot:**
```properties
# application.properties
otel.propagators=tracecontext,baggage
```

```yaml
# application.yaml
otel:
  propagators:
    - tracecontext
    - baggage
```

Note: System property `otel.propagators` takes precedence over `OTEL_PROPAGATORS` env var.

### Python

```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install  # install instrumentation packages

export OTEL_PROPAGATORS="tracecontext,baggage"
export OTEL_SERVICE_NAME="my-python-service"
opentelemetry-instrument python app.py
```

**Gotcha:** Python auto-instrumentation defaults to `http/protobuf` protocol.
If your collector listens on gRPC port 4317, either:
- Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318` (use HTTP port), or
- Set `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`

### Node.js

```bash
npm install @opentelemetry/auto-instrumentations-node

export OTEL_PROPAGATORS="tracecontext,baggage"
export OTEL_SERVICE_NAME="my-node-service"
export NODE_OPTIONS="--require @opentelemetry/auto-instrumentations-node/register"
node app.js
```

**Gotcha:** If `OTEL_NODE_ENABLED_INSTRUMENTATIONS` and `OTEL_NODE_DISABLED_INSTRUMENTATIONS`
are both set, enabled is applied first, then disabled filters from that list.

### Go

Go requires code-level setup (no zero-code agent equivalent for propagators):

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
)

otel.SetTextMapPropagator(
    propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ),
)
```

However, `OTEL_PROPAGATORS` env var IS respected by the OTel K8s Operator's
Go auto-instrumentation (eBPF-based).

### .NET

```bash
export OTEL_PROPAGATORS="tracecontext,baggage"
export OTEL_SERVICE_NAME="my-dotnet-service"
```

**Gotcha:** .NET auto-instrumentation defaults to `http/protobuf`. Same port
consideration as Python — use port 4318 for HTTP or set protocol to `grpc`.

---

## Kubernetes Instrumentation CRD Patterns {#kubernetes-patterns}

### Basic Instrumentation CR

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: my-instrumentation
  namespace: default
spec:
  exporter:
    endpoint: http://otel-collector.observability.svc.cluster.local:4317
  propagators:
    - tracecontext
    - baggage
  sampler:
    type: parentbased_traceidratio
    argument: "1"
```

### With Service Mesh (Istio/Linkerd) — Add B3

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: mesh-instrumentation
  namespace: default
spec:
  exporter:
    endpoint: http://otel-collector.observability.svc.cluster.local:4317
  propagators:
    - tracecontext
    - baggage
    - b3
    - b3multi
  sampler:
    type: parentbased_traceidratio
    argument: "1"
```

### Per-Language Overrides

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: Instrumentation
metadata:
  name: multi-lang-instrumentation
spec:
  exporter:
    endpoint: http://otel-collector:4317
  propagators:
    - tracecontext
    - baggage
  sampler:
    type: parentbased_traceidratio
    argument: "1"
  python:
    env:
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: http://otel-collector:4318  # Python needs HTTP port
  dotnet:
    env:
      - name: OTEL_EXPORTER_OTLP_ENDPOINT
        value: http://otel-collector:4318  # .NET needs HTTP port
```

---

## Auto-Instrumentation Annotations {#annotations}

Add these annotations to your Deployment/Pod spec to activate auto-instrumentation:

| Language | Annotation |
|---|---|
| Java | `instrumentation.opentelemetry.io/inject-java: "true"` |
| Python | `instrumentation.opentelemetry.io/inject-python: "true"` |
| Node.js | `instrumentation.opentelemetry.io/inject-nodejs: "true"` |
| .NET | `instrumentation.opentelemetry.io/inject-dotnet: "true"` |
| Go | `instrumentation.opentelemetry.io/inject-go: "true"` |

**Namespace-level** (all pods in namespace):
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-namespace
  annotations:
    instrumentation.opentelemetry.io/inject-java: "true"
```

**Targeting specific Instrumentation CR:**
```yaml
annotations:
  instrumentation.opentelemetry.io/inject-java: "my-namespace/my-instrumentation"
```

**Multi-container pods:**
```yaml
annotations:
  instrumentation.opentelemetry.io/inject-java: "true"
  instrumentation.opentelemetry.io/container-names: "app-container"
```

**Important:** The Instrumentation CR must be deployed BEFORE the annotated
Deployment. If the pod starts before the CR exists, the init container won't
be injected and auto-instrumentation will silently fail.

---

## mirrord Integration Patterns {#mirrord-patterns}

### Pattern 1: Mirror Cluster OTel Env Vars

Let mirrord pull the OTel env vars from the remote pod so local dev uses
identical propagator config:

```json
{
  "feature": {
    "env": {
      "include": "OTEL_PROPAGATORS;OTEL_SERVICE_NAME;OTEL_TRACES_EXPORTER;OTEL_EXPORTER_OTLP_ENDPOINT;OTEL_EXPORTER_OTLP_PROTOCOL;OTEL_TRACES_SAMPLER;OTEL_TRACES_SAMPLER_ARG;OTEL_RESOURCE_ATTRIBUTES"
    }
  }
}
```

**When to use:** When you want your local process to behave identically to the
cluster pod, including sending traces to the same collector.

### Pattern 2: Override Service Name for Local Dev

Mirror propagator config but mark local traces distinctly:

```json
{
  "feature": {
    "env": {
      "include": "OTEL_PROPAGATORS;OTEL_EXPORTER_OTLP_ENDPOINT;OTEL_EXPORTER_OTLP_PROTOCOL;OTEL_TRACES_SAMPLER;OTEL_TRACES_SAMPLER_ARG",
      "override": {
        "OTEL_SERVICE_NAME": "my-service-local-dev",
        "OTEL_RESOURCE_ATTRIBUTES": "deployment.environment=local-dev"
      }
    }
  }
}
```

**When to use:** When you want to distinguish local dev traces from production
traces in your observability backend.

### Pattern 3: Local Collector + Cluster Propagators

Run a local OTel Collector and point local traces there, while still using
matching propagators for header compatibility:

```json
{
  "feature": {
    "env": {
      "include": "OTEL_PROPAGATORS",
      "override": {
        "OTEL_SERVICE_NAME": "my-service-local",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"
      }
    }
  }
}
```

**When to use:** When you have a local collector for dev (e.g., Jaeger all-in-one)
but need header format compatibility with the cluster.

### Pattern 4: Disable Tracing Locally, Keep Propagation

If you don't want to send traces but still need to propagate headers so
downstream cluster services maintain their traces:

```json
{
  "feature": {
    "env": {
      "include": "OTEL_PROPAGATORS",
      "override": {
        "OTEL_TRACES_EXPORTER": "none",
        "OTEL_METRICS_EXPORTER": "none",
        "OTEL_LOGS_EXPORTER": "none"
      }
    }
  }
}
```

**Why this works:** Per the OTel spec, `OTEL_SDK_DISABLED=true` has NO effect
on propagators. But setting exporters to `none` stops data emission while
propagators still extract + inject headers.

---

## Troubleshooting {#troubleshooting}

### Headers not propagating

1. Check that `OTEL_PROPAGATORS` is set on BOTH sides (sender + receiver)
2. Verify the values match — `tracecontext` on one side and `b3` on the other = broken
3. For mirrord: check `env.include` captures `OTEL_PROPAGATORS`
4. For K8s Operator: verify the Instrumentation CR was deployed BEFORE the pod started

### Traces break at mirrord boundary

1. Ensure local process has auto-instrumentation enabled (agent JAR, `opentelemetry-instrument`, `NODE_OPTIONS`, etc.)
2. Confirm propagator format matches between cluster and local
3. Check if HTTP framework middleware is stripping trace headers
4. Verify collector endpoint is reachable (mirrord proxies cluster DNS)

### "Unknown propagator" errors in logs

- Verify the propagator value is in the valid set above
- Check for typos: `trace-context` (wrong) vs `tracecontext` (correct)
- Check for spaces: `tracecontext, baggage` (wrong) vs `tracecontext,baggage` (correct)
- For Java: ensure the propagator extension JAR is on the classpath

### K8s Operator init container not injecting

1. Check pod events: `kubectl describe pod <name>`
2. Look for `opentelemetry-auto-instrumentation` init container in events
3. Ensure annotation matches: `instrumentation.opentelemetry.io/inject-<lang>: "true"`
4. Ensure Instrumentation CR exists in the correct namespace
5. Check Operator logs: `kubectl logs -l app.kubernetes.io/name=opentelemetry-operator -n <operator-ns>`

### Python/DotNet port mismatch

Python and .NET default to `http/protobuf` protocol. If your collector is on
port 4317 (gRPC), you'll get connection errors. Fix:

```yaml
python:
  env:
    - name: OTEL_EXPORTER_OTLP_ENDPOINT
      value: http://otel-collector:4318
```

Or set `OTEL_EXPORTER_OTLP_PROTOCOL=grpc` to force gRPC.
