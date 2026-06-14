# System Wiki Tools

This directory contains tooling for maintaining the Everspot System Wiki.

## Overview

Two primary tools automate wiki maintenance:

1. **generate-schema-snapshots.php** — Standalone extractor that boots Everspot framework in-process to generate schema/central.json and schema/tenant.json
2. **extract-model-skeleton.php** — PHP script that extracts mechanical parts of model documentation from source code

## Schema Snapshot Generation

### generate-schema-snapshots.php (Standalone Extractor)

**Recommended approach.** Boots Everspot's Laravel framework in-process WITHOUT writing any files to Everspot repository.

**Features:**
- NO writes to Everspot repo (read-only framework boot)
- Handles tenant context via stancl/tenancy automatically
- Filters by database name (critical: Laravel's Schema::getTables() returns ALL databases)
- Skips framework tables (migrations, jobs, cache, telescope_*, nova_*, pulse_*, etc.)
- Anchors snapshot_commit to Everspot origin/main commit

**Usage:**

```bash
cd /path/to/wiki
php tools/generate-schema-snapshots.php \
  --central schema/central.json \
  --tenant schema/tenant.json \
  --tenant-id <existing-tenant-id>

# Or use the wrapper script:
./tools/generate-snapshots.sh [optional-tenant-id]
```

**Multi-Tenancy Context:**

Everspot uses stancl/tenancy for database isolation. Each tenant has its own database with identical schema.

**Tenant initialization:**
```php
$tenant = Tenant::find($tenantId);
tenancy()->initialize($tenant);  // Switch to tenant context
// ... extract schema ...
tenancy()->end();  // Restore central context
```

**Connection handling:**
- Central: uses 'mysql' connection (Everspot's primary connection name)
- Tenant: uses 'tenant' connection (auto-configured after tenancy()->initialize())

**All tenants share one schema**, so extraction from any migrated tenant is authoritative.

**Requirements:**

- Runnable Everspot instance with vendor/autoload.php and bootstrap/app.php
- At least one migrated tenant (for tenant schema extraction)
- wiki.config.json with everspot_repo_path configured
- MySQL server running with databases migrated

**Snapshot JSON Format:**

```json
{
  "snapshot_commit": "86b4328c28...",
  "generated_at": "2026-06-12T...",
  "connection": "central|tenant",
  "tables": {
    "table_name": {
      "columns": [{"name": "...", "type": "...", "nullable": false, "default": null}],
      "indexes": [{"name": "...", "columns": ["..."], "type": "primary|unique|index"}],
      "foreign_keys": [{"columns": ["..."], "foreign_table": "...", "on_delete": "..."}]
    }
  },
  "meta": {
    "table_count": 152,
    "extraction_method": "laravel_schema_introspection"
  }
}
```

**Troubleshooting:**

- "Cannot connect to database": Check Everspot .env configuration (DB_HOST, DB_DATABASE, DB_USERNAME)
- "unknown" commit hash: Not in a git repository or git not in PATH
- Empty tables: Migrations not run or connection misconfigured
- Tenant context errors: stancl/tenancy not configured or no tenants exist (create with `php artisan tenants:create`)
- Wrong table count: Check database name filtering (extractor filters by connected database name)

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

## Model Skeleton Extraction

### extract-model-skeleton.php

Extracts deterministic, mechanical parts of model documentation, leaving only prose sections for AI to write.

**Purpose:**
- Mechanizes frontmatter, properties, methods, relationships, scopes extraction
- Handles inheritance (parent classes, traits) recursively
- Derives source_paths automatically
- Supports STI pattern (separates "Defined in X" vs "Inherited from Y")
- Produces partial markdown with AI sections marked `<!-- AI: ... -->`

**Usage:**

```bash
php tools/extract-model-skeleton.php <model-path-from-everspot-root>

# Examples:
php tools/extract-model-skeleton.php modules/Transaction/Models/Payment.php > draft.md
php tools/extract-model-skeleton.php app/Models/User.php > draft.md
```

**What It Extracts (Mechanical Sections):**

- Frontmatter: model, module, table, source_paths[], related[], built_at, deprecated
- Properties: $casts, $fillable, $guarded, $appends, $hidden, custom arrays
- Relationships: method signatures with return types (HasMany, BelongsTo, etc.)
- Public Methods: signatures and return types
- Scopes: global scopes and query scopes
- Section structure and headers

**What It Marks for AI (Prose Sections):**

- Overview (business purpose)
- Connection determination (if not explicit in $connection property)
- Relationship descriptions
- Method descriptions
- Common usage examples
- Tags selection
- Completeness assessment
- Events and observers

**Inheritance Handling:**

- Parses parent classes recursively (Payment → Transaction → BaseModel)
- Includes all traits in source_paths
- Separates "Defined in Payment" vs "Inherited from Transaction" sections
- Uses parent's table name if child doesn't define one (STI pattern)

**Limitations:**

- Related model names use heuristic pluralization (may need AI correction)
- Cannot determine connection without schema snapshot lookup
- Cannot extract method body content (events, observers)
- Does not parse trait method definitions (lists trait in source_paths only)
- Does not extract constants/enums

**Integration:**

- **Generate command:** skeleton → AI fill → validate → commit
- **Sync command:** regenerate skeleton → preserve human blocks → AI refill → validate

## Integration with Sync

The `sync` command (see `meta/commands/sync.md`) uses these tools:

1. Detects migration changes by monitoring database/migrations/ paths
2. Regenerates affected snapshot (central.json or tenant.json)
3. Diffs snapshots to find changed tables
4. For each changed table: runs extract-model-skeleton.php → AI fills prose → validates → commits

**When to regenerate snapshots manually:**

- After running new migrations
- Before bootstrap or first sync run
- When validating schema accuracy

**When to use extract-model-skeleton.php directly:**

- Generating a new model document manually
- Debugging mechanical section extraction
- Testing skeleton generator changes

## See Also

- `meta/commands/` — Full command specifications (one file per command); see `meta/commands/index.md`
- `meta/foundation.md` — Authoritative design spec and architecture
- `meta/conventions.md` — Model enumeration rules, STI detection, naming conventions
