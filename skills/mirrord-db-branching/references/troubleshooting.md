# Common Issues

> Source: https://github.com/metalbear-co/docs/tree/main/docs/troubleshooting

## Branch creation times out or is very slow

This is often caused by using `"mode": "all"` on a large database. The `all` mode copies the entire database including all data, which can take a long time for databases with significant data.

**Solution:** Use `"mode": "schema"` or `"mode": "empty"` instead:

```json
{
  "copy": {
    "mode": "schema"
  }
}
```

If you need specific data, use filtered copying:

```json
{
  "copy": {
    "mode": "schema",
    "tables": {
      "users": {"filter": "id < 100"}
    }
  }
}
```

## Connection fails with SSL/TLS errors

Branch databases disable SSL by default. If your application client is configured to require SSL, the connection will fail.

**Solution:** Configure your application to allow non-SSL connections to the branch database, or check if the client is forcing SSL when it shouldn't.

## GCP Cloud SQL connection fails

GCP Cloud SQL with IAM authentication requires TLS. If your connection URL doesn't include `sslmode=require`, the connection will fail.

**Solution:** Ensure your connection URL includes the SSL mode parameter:

```
postgresql://user@host:5432/dbname?sslmode=require
```

## Branch is not being reused between sessions

If you expect a branch to persist and be reused but a new one is created each time, check:

1. The `id` field must be set and identical between sessions
2. The branch TTL (`ttl_secs`) hasn't expired - max is 900 seconds (15 minutes)

**Solution:** Set an explicit `id` and ensure TTL is sufficient:

```json
{
  "db_branches": [
    {
      "id": "my-stable-branch",
      "ttl_secs": 900,
      "type": "pg",
      ...
    }
  ]
}
```

## Application connects to wrong database

If your application isn't connecting to the branch database, the environment variable name in your config likely doesn't match what your application actually uses.

**Solution:** Verify the exact environment variable your application reads for the database connection:

```bash
# Check what env var your app uses
mirrord exec --target pod/<pod-name> -- env | grep -i database
mirrord exec --target pod/<pod-name> -- env | grep -i postgres
mirrord exec --target pod/<pod-name> -- env | grep -i mysql
```

Then update your config to match:

```json
{
  "connection": {
    "url": {
      "type": "env",
      "variable": "DATABASE_URL"
    }
  }
}
```

## AWS RDS IAM authentication fails

When using AWS RDS with IAM authentication, mirrord needs access to AWS credentials from the target pod's environment.

**Solution:** Ensure the target pod has the required AWS environment variables:
- `AWS_REGION` or `AWS_DEFAULT_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (if using temporary credentials)

If using IRSA (IAM Roles for Service Accounts), the pod must have the appropriate annotations and the service account must be configured correctly.

## MongoDB branch filter syntax errors

MongoDB uses JSON-based filter syntax, not SQL. Filters must be valid MongoDB query documents as escaped JSON strings.

**Solution:** Use proper MongoDB query syntax:

```json
{
  "copy": {
    "mode": "all",
    "collections": {
      "users": {"filter": "{\"role\": \"admin\"}"},
      "orders": {"filter": "{\"status\": {\"$in\": [\"pending\", \"processing\"]}}"}
    }
  }
}
```

## Version compatibility issues

DB branching requires specific minimum versions:

- **MySQL**: Operator 3.129.0+, CLI 3.160.0+, Helm chart 1.37.0+
- **PostgreSQL**: Operator 3.131.0+, CLI 3.175.0+, Helm chart 1.40.2+

**Solution:** Check your versions:

```bash
mirrord --version
kubectl get deployment -n mirrord mirrord-operator -o jsonpath='{.spec.template.spec.containers[0].image}'
```

Also ensure the appropriate feature flag is enabled in the Helm chart:
- MySQL: `operator.mysqlBranching: true`
- PostgreSQL: `operator.pgBranching: true`

## Local Redis container fails to start

When using local Redis (`"location": "local"`), the container runtime must be available and properly configured.

**Solution:** Verify Docker or your container runtime is running:

```bash
docker info
```

Check the local Redis configuration:

```json
{
  "db_branches": [
    {
      "type": "redis",
      "location": "local",
      "local": {
        "runtime": "container",
        "container_runtime": "docker",
        "port": 6379,
        "version": "7-alpine"
      }
    }
  ]
}
```
