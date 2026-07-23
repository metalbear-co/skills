# Common Issues

> Source: https://metalbear.com/mirrord/docs/sharing-the-cluster/db-branching/

> **Config nesting:** `db_branches` must live under the top-level `feature` object
> (`{"feature": {"db_branches": [ ... ]}}`). Placed at the top level it is ignored.

## Branch creation times out or is very slow

Often caused by using `"mode": "all"` on a large database. The `all` mode copies the entire database including all data, which can take a long time.

**Solution:** Use `"mode": "schema"` or `"mode": "empty"` instead:

```json
{ "copy": { "mode": "schema" } }
```

If you need specific data, use filtered copying (SQL engines):

```json
{
  "copy": {
    "mode": "schema",
    "tables": { "users": { "filter": "id < 100" } }
  }
}
```

Note: filters are ignored when `"mode": "all"` is set — combine filters with `"empty"` or `"schema"` instead.

Unrecoverable pod failures (e.g. `ImagePullBackOff`, `OOMKilled`) fail the branch immediately with the underlying error rather than waiting for `creation_timeout_secs`.

## Connection fails with SSL/TLS errors

Branch databases disable SSL by default. If your application client is configured to require SSL, the connection will fail.

**Solution:** Configure your application to allow non-SSL connections to the branch, or stop the client from forcing SSL. (GCP Cloud SQL IAM is the exception — see below.)

## GCP Cloud SQL connection fails

GCP Cloud SQL with IAM authentication requires TLS. If the connection URL doesn't include `sslmode=require`, the connection will fail.

**Solution:** Ensure the URL includes the SSL mode parameter:

```
postgresql://user@host:5432/dbname?sslmode=require
```

## Branch is not being reused between sessions

If you expect a branch to persist and be reused but a new one is created each time, check:

1. The `id` field must be set and identical between sessions.
2. The branch TTL hasn't expired. TTL is counted from when no session is using the branch. Default is 5 minutes and it **caps at 15 minutes**. Set `ttl_secs` or `ttl_mins` (mutually exclusive).

```json
{
  "feature": {
    "db_branches": [
      { "id": "my-stable-branch", "ttl_mins": 15, "type": "pg", "connection": { "url": "DATABASE_URL" } }
    ]
  }
}
```

Note: `id` is ignored for local Redis instances.

## Application connects to wrong database

If your application isn't connecting to the branch, the connection variable(s) in your config likely don't match what the app actually reads.

**Solution:** Verify the exact environment variable(s):

```bash
mirrord exec --target pod/<pod-name> -- env | grep -iE 'database|postgres|mysql|redis|mongo'
```

Then match your config to it:

```json
{ "connection": { "url": "DATABASE_URL" } }
```

For apps that split the connection across variables, use params mode; for a value packed into one variable, use `value_pattern`. See the Connection Modes doc.

## AWS RDS IAM authentication fails

mirrord reads AWS credentials from the **target pod's** environment (not your local shell).

**Solution:** Ensure the target pod exposes:
- `AWS_REGION` or `AWS_DEFAULT_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN` (if using temporary credentials)

With IRSA (IAM Roles for Service Accounts), the pod's service account must be configured correctly. For non-standard variable names, set custom sources under `iam_auth`.

## DynamoDB full copy fails

DynamoDB has no password-based auth. `"copy": { "mode": "all" }` **requires** `iam_auth`.

**Solution:**

```json
{ "type": "dynamodb", "iam_auth": { "type": "aws_rds" }, "copy": { "mode": "all" } }
```

Also note: DynamoDB `filter` strings can't use `ExpressionAttributeValues`/`Names` placeholders; only self-contained expressions work. LSIs are not copied; branch tables use PayPerRequest billing.

## MongoDB branch filter syntax errors

MongoDB uses JSON-based filter syntax, not SQL. Filters must be valid MongoDB query documents as escaped JSON strings, and MongoDB supports only `empty` / `all` (no `schema`).

```json
{
  "copy": {
    "mode": "all",
    "collections": {
      "users": { "filter": "{\"role\": \"admin\"}" },
      "orders": { "filter": "{\"status\": {\"$in\": [\"pending\", \"processing\"]}}" }
    }
  }
}
```

## Schema migrations rejected

`migrations` requires the branch `name` to be set and is only available for MySQL, MariaDB, PostgreSQL, and MSSQL. A migration that conflicts with one already applied to the branch fails your session only; the branch stays usable.

## Generic branch never becomes ready

A plain TCP readiness probe can pass before the service is actually usable (e.g. before first-boot setup completes).

**Solution:** Use an `http_get` or `exec` probe that proves usability:

```json
{ "readiness": { "type": "http_get", "path": "/health" } }
```

Heavy JVM images (Elasticsearch, Cassandra, Couchbase) can OOM at the 512Mi branch-pod default; an admin must raise `dbPod.resources` in `genericBranchConfig`. If an image isn't in the admin's `allowedImages` glob list, the branch fails immediately naming the image.

## Version compatibility issues

Each engine has minimum operator, CLI, and Helm chart versions, plus a per-engine Helm value that must be enabled (e.g. `operator.mysqlBranching: true`, `operator.pgBranching: true`, `operator.dynamodbBranching: true`, `operator.genericBranching: true`). See the Version Requirements table in `SKILL.md`.

**Check your versions:**

```bash
mirrord --version
kubectl get deployment -n mirrord mirrord-operator -o jsonpath='{.spec.template.spec.containers[0].image}'
```

## Local Redis container fails to start

When using local Redis (`"location": "local"`), the container runtime must be available.

**Solution:** Verify Docker (or your runtime) is running:

```bash
docker info
```

Check the local Redis configuration:

```json
{
  "feature": {
    "db_branches": [
      {
        "type": "redis",
        "location": "local",
        "local": { "runtime": "container", "container_runtime": "docker", "port": 6379 }
      }
    ]
  }
}
```
