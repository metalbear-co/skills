# Common Issues

> Source: https://github.com/metalbear-co/docs/tree/main/docs/troubleshooting

## "Operator not found" when running mirrord

The mirrord client cannot find or connect to the operator in the cluster.

**Solution:** Verify the operator pod is running:

```bash
kubectl get pods -n mirrord
kubectl get deployment -n mirrord mirrord-operator
```

If the pod isn't running, check the deployment status and events:

```bash
kubectl describe deployment -n mirrord mirrord-operator
kubectl logs -n mirrord -l app=mirrord-operator
```

## License key invalid or expired

The operator rejects connections due to licensing issues.

**Solution:**

1. Verify your license key is correctly set:
```bash
kubectl get secret -n mirrord mirrord-operator-license -o jsonpath='{.data.key}' | base64 -d
```

2. Check operator logs for license-related errors:
```bash
kubectl logs -n mirrord -l app=mirrord-operator | grep -i license
```

3. If the license expired, contact MetalBear for renewal. Then update the license secret and upgrade:
```bash
kubectl create secret generic mirrord-license \
  --from-literal=key=<NEW_LICENSE_KEY> \
  -n mirrord --dry-run=client -o yaml | kubectl apply -f -
helm upgrade mirrord-operator metalbear/mirrord-operator \
  --namespace mirrord \
  --set license.keyRef.secretName=mirrord-license \
  --set license.keyRef.secretKey=key
```

## "Permission denied" when using mirrord with operator

Users cannot create mirrord sessions due to RBAC restrictions.

**Solution:** The user needs appropriate permissions on mirrord CRDs. Create a ClusterRole and binding:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: mirrord-user
rules:
- apiGroups: ["mirrord.metalbear.co"]
  resources: ["targets", "sessions"]
  verbs: ["get", "list", "create", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: mirrord-user-binding
subjects:
- kind: User
  name: <username>
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: mirrord-user
  apiGroup: rbac.authorization.k8s.io
```

## "Namespace not allowed" error

The operator rejects sessions for targets in certain namespaces.

**Solution:** Check the `roleNamespaces` setting in your Helm values. An empty list means all namespaces are allowed:

```yaml
# values.yaml
roleNamespaces: []  # Allow all namespaces
```

Or specify allowed namespaces explicitly:

```yaml
roleNamespaces:
  - staging
  - development
```

Then upgrade:

```bash
helm upgrade mirrord-operator metalbear/mirrord-operator \
  --namespace mirrord -f values.yaml
```

## Operator pod keeps crashing or restarting

The operator pod fails to start or crashes repeatedly.

**Solution:**

1. Check pod logs:
```bash
kubectl logs -n mirrord -l app=mirrord-operator --previous
```

2. Check resource limits - the default may be too low for large clusters:
```yaml
operator:
  resources:
    limits:
      cpu: 200m
      memory: 200Mi  # Increase if needed for many concurrent sessions
```

3. Check events:
```bash
kubectl get events -n mirrord --sort-by='.lastTimestamp'
```

## Port 443 conflict or unavailable

The operator's webhook server cannot bind to port 443.

**Solution:** Configure the operator to use an alternative port:

```yaml
operator:
  port: 8443  # Or 3000
```

Then upgrade the Helm release.

## Webhook certificate errors

TLS certificate issues prevent the API server from calling the operator's webhooks.

**Solution:**

1. Check certificate secret exists:
```bash
kubectl get secret -n mirrord mirrord-operator-webhook-cert
```

2. Restart the operator to regenerate certificates:
```bash
kubectl rollout restart deployment -n mirrord mirrord-operator
```

3. If issues persist, reinstall:
```bash
helm uninstall mirrord-operator --namespace mirrord
helm install mirrord-operator metalbear/mirrord-operator --namespace mirrord
```

## `mirrord operator status` fails with `503 Service Unavailable` on GKE

If private networking is enabled, firewall rules may block the operator's API service.

**Solution:** Add a firewall rule that allows your cluster's master nodes to access TCP port 443 (or your configured operator port) in your cluster's pods.

## Sessions fail silently with service mesh

Service meshes (Istio, Linkerd) may interfere with operator-agent communication.

**Solution:**

1. Exclude the mirrord namespace from the mesh, or
2. Set a static agent port and add exclusion annotations:

```yaml
# In Helm values
agent:
  port: 50000
```

For Istio, add to target pod annotations:
```
traffic.sidecar.istio.io/excludeInboundPorts: '50000'
```

## Upgrading operator breaks existing sessions

Running sessions may fail after operator upgrade.

**Solution:** Wait for existing sessions to complete before upgrading, or coordinate with users:

```bash
# Check active sessions
kubectl get sessions.mirrord.metalbear.co -A

# Upgrade when no sessions are active
helm upgrade mirrord-operator metalbear/mirrord-operator --namespace mirrord
```
