# mirrord-db-branching

Configure mirrord for isolated database branches during development.

## What it does

This skill helps AI agents:
- **Generate** valid `db_branches` configs for mirrord.json
- **Configure** MySQL, PostgreSQL, MongoDB, and Redis branches
- **Set up** copy modes (empty, schema, all, filtered)
- **Configure** IAM authentication for AWS RDS and GCP Cloud SQL
- **Manage** database branches via CLI commands

## Example prompts

```
"Set up a MySQL database branch for testing migrations"

"Configure mirrord to use a PostgreSQL branch with schema copy"

"Help me set up a local Redis instance with mirrord"

"Configure DB branching with AWS RDS IAM authentication"

"How do I filter which rows get copied to my database branch?"
```

## Supported databases

| Database | Type value | Notes |
|----------|------------|-------|
| MySQL | `"mysql"` | Requires `operator.mysqlBranching: true` |
| PostgreSQL | `"pg"` | Supports IAM auth (AWS RDS, GCP Cloud SQL) |
| MongoDB | `"mongodb"` | Uses collections instead of tables |
| Redis | `"redis"` | Can run locally or remotely |

## Quick example

```json
{
  "db_branches": [
    {
      "type": "pg",
      "version": "16",
      "connection": {
        "url": {
          "type": "env",
          "variable": "DATABASE_URL"
        }
      },
      "copy": {
        "mode": "schema"
      }
    }
  ]
}
```

## Branch management

```bash
# View branch status
mirrord db-branches status

# Destroy a branch
mirrord db-branches destroy <branch-name>

# Destroy all branches
mirrord db-branches destroy --all
```

## References

This skill uses local reference files:
- `references/db-branches-schema.json` — JSON Schema for db_branches configuration

## Learn more

- [DB Branching Overview](https://metalbear.com/mirrord/docs/using-mirrord/db-branching/)
- [Advanced Configuration](https://metalbear.com/mirrord/docs/using-mirrord/db-branching-advanced-config/)
- [Branch Management](https://metalbear.com/mirrord/docs/using-mirrord/db-branch-management/)
