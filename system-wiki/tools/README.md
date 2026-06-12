# System Wiki Tools

This directory contains tooling for maintaining the Everspot System Wiki.

## Schema Snapshot Generation

### WikiSchemaSnapshot.php

Laravel Artisan command for generating schema snapshots from live databases.

**Installation:**

1. Copy `WikiSchemaSnapshot.php` to Everspot's `app/Console/Commands/` directory
2. Laravel will auto-discover the command

**Usage:**

```bash
# Generate central schema snapshot
cd /path/to/everspot
php artisan wiki:schema-snapshot central --output=/path/to/wiki/schema/central.json

# Generate tenant schema snapshot (requires tenant context)
php artisan tenants:run <tenant-id> --command="wiki:schema-snapshot tenant --output=/tmp/tenant-schema.json"
cp /tmp/tenant-schema.json /path/to/wiki/schema/tenant.json

# Use --wiki-path for automatic output path
php artisan wiki:schema-snapshot central --wiki-path=/path/to/wiki
```

**Options:**

- `connection` (required): `central` or `tenant`
- `--output=<path>`: Custom output file path
- `--wiki-path=<path>`: Wiki repository path (auto-determines output path)
- `-v`: Verbose output (shows table list)

**Requirements:**

- Runnable Everspot instance
- Migrated databases (central and/or tenant)
- Git repository (for snapshot_commit hash)
- Laravel 10.x with Schema facade support

**Output Format:**

See `meta/phase3-build-log.md` for full JSON schema specification.

**Troubleshooting:**

- "Cannot connect to database": Check database configuration in `.env`
- "unknown" commit hash: Not in a git repository or git not in PATH
- Empty tables: Migrations not run or connection misconfigured
- Tenant context errors: stancl/tenancy not configured or no tenants exist

## Verification

After generating snapshots:

```bash
# Verify JSON is valid
cd /path/to/wiki
cat schema/central.json | jq . > /dev/null && echo "✓ Valid JSON"
cat schema/tenant.json | jq . > /dev/null && echo "✓ Valid JSON"

# Check table count
jq '.meta.table_count' schema/central.json
jq '.meta.table_count' schema/tenant.json

# Verify no error markers
! jq -e '.error' schema/central.json && echo "✓ No errors"
! jq -e '.error' schema/tenant.json && echo "✓ No errors"
```

## Integration with Sync

The `sync` command (see `meta/commands.md` §3.2) uses these snapshots:

1. Detects migration changes via `meta/migration-path-mapping.json`
2. Regenerates affected connection's snapshot
3. Diffs new vs old snapshot to find changed tables
4. Regenerates model documents for changed tables

**When to regenerate manually:**

- After running new migrations
- Before running `sync` for the first time
- When changing database structure outside migrations (not recommended)
- For periodic verification (compare against migrations)

## See Also

- `meta/commands.md` §4 - Full snapshot-schema command specification
- `meta/phase3-build-log.md` - Implementation notes and design decisions
- `meta/migration-path-mapping.json` - Connection-to-migration-path configuration
