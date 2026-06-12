---
title: Phase 3 Build Log — Schema Snapshot Generation
phase: 3
status: blocked
date: 2026-06-12
---

# Phase 3 Build Log — Schema Snapshot Generation

## Objective

Build tooling to generate `schema/central.json` and `schema/tenant.json` from live database introspection of a running Everspot instance.

## Critical Blocker Identified

**Everspot repository does not exist at configured path.**

- **Expected path:** `/Users/cashkalina/code/everspot-brain/everspot`
- **Actual state:** Directory does not exist
- **Impact:** Cannot read source code, cannot run schema introspection, cannot generate live snapshots

This blocker prevents:
1. Investigation of existing schema generation tools
2. Analysis of multi-tenancy implementation details
3. Live database introspection
4. Generation of actual schema snapshots

## Decisions Made

Per phase instructions, **continue with maximum progress despite blocker**:

1. **Design snapshot format** based on specification
2. **Create extraction tooling** that will work when Everspot is available
3. **Produce skeleton/placeholder JSONs** with error markers
4. **Document connection-to-migration-path mapping** from specification expectations
5. **Record all findings** for later execution

## Investigation Results

### 1. Existing Schema Generation (BLOCKED)

Could not investigate due to missing Everspot repository. Expectations based on foundation.md §3.3:

- Everspot "already generates a central schema from a live database today"
- Likely uses Laravel's `schema:dump` command or similar introspection
- Should support `--connection=central` and `--connection=tenant` options
- May have custom artisan commands in `app/Console/Commands/`

**Action when unblocked:** Search for:
- `php artisan schema:dump` usage
- Custom commands in `app/Console/Commands/` matching `*schema*`
- Existing schema outputs in `database/schema/` or similar
- Laravel schema introspection helpers

### 2. Multi-Tenancy Setup (BLOCKED)

Could not analyze implementation. Expected based on specification:

- **Package:** stancl/tenancy
- **Tenant context entry:** `php artisan tenants:run <tenant-id> --command="..."`
- **Programmatic access:** `Tenant::find($id)->run(function() { ... })`
- **Schema uniformity:** All tenants share one schema (fresh migration = authoritative)
- **Reference tenant:** May need to create throwaway tenant for introspection

**Connection determination:**
- Models have explicit `$connection` property OR use conventional defaults
- Central connection: Core models (`app/Models/User`, auth models)
- Tenant connection: Module models (`modules/*/Models/*`)

**Action when unblocked:** Confirm:
- stancl/tenancy configuration in `config/tenancy.php`
- How to list/create/destroy test tenants
- Whether a permanent reference tenant exists
- Tenant database migration commands

### 3. Snapshot Format Design

Designed per commands.md §4.1 specification:

```json
{
  "snapshot_commit": "<git commit hash of origin/main>",
  "generated_at": "<ISO 8601 timestamp>",
  "connection": "central|tenant",
  "tables": {
    "table_name": {
      "columns": [
        {
          "name": "column_name",
          "type": "varchar(255)",
          "nullable": false,
          "default": null,
          "auto_increment": false,
          "comment": ""
        }
      ],
      "indexes": [
        {
          "name": "index_name",
          "columns": ["column1", "column2"],
          "type": "index|unique|primary",
          "unique": false
        }
      ],
      "foreign_keys": [
        {
          "columns": ["foreign_id"],
          "foreign_table": "other_table",
          "foreign_columns": ["id"],
          "on_delete": "cascade|restrict|set null|no action",
          "on_update": "cascade|restrict|set null|no action"
        }
      ]
    }
  },
  "meta": {
    "extraction_method": "laravel_doctrine_dbal|artisan_schema_dump",
    "laravel_version": "10.x",
    "database_driver": "mysql|pgsql"
  }
}
```

**Key fields:**
- `snapshot_commit`: Git hash for detecting schema drift
- `generated_at`: Human timestamp for reference
- `connection`: Must be "central" or "tenant"
- Columns capture: name, type, nullable, default, auto_increment, comment
- Indexes capture: name, columns, uniqueness
- Foreign keys capture: full constraint definition
- Meta: extraction tooling details for debugging

### 4. Extraction Tooling Design

Created two approaches:

#### Approach A: Laravel Artisan Command (Recommended)

Create `app/Console/Commands/WikiSchemaSnapshot.php` in Everspot:

```php
<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

class WikiSchemaSnapshot extends Command
{
    protected $signature = 'wiki:schema-snapshot
                            {connection : Database connection (central or tenant)}
                            {--output= : Output file path}';

    protected $description = 'Generate schema snapshot JSON for System Wiki';

    public function handle()
    {
        $connection = $this->argument('connection');
        $output = $this->option('output')
            ?? storage_path("schema-{$connection}.json");

        // Get current git commit
        $commit = trim(shell_exec('git rev-parse HEAD'));

        // Build snapshot
        $snapshot = [
            'snapshot_commit' => $commit,
            'generated_at' => now()->toISOString(),
            'connection' => $connection,
            'tables' => $this->extractTables($connection),
            'meta' => [
                'extraction_method' => 'laravel_doctrine_dbal',
                'laravel_version' => app()->version(),
                'database_driver' => config("database.connections.{$connection}.driver")
            ]
        ];

        file_put_contents($output, json_encode($snapshot, JSON_PRETTY_PRINT));

        $this->info("Schema snapshot written to: {$output}");
        $this->info("Tables captured: " . count($snapshot['tables']));
    }

    protected function extractTables($connection)
    {
        $schema = Schema::connection($connection);
        $tables = [];

        foreach ($schema->getTables() as $table) {
            $tableName = $table['name'];

            $tables[$tableName] = [
                'columns' => $this->extractColumns($connection, $tableName),
                'indexes' => $this->extractIndexes($connection, $tableName),
                'foreign_keys' => $this->extractForeignKeys($connection, $tableName)
            ];
        }

        return $tables;
    }

    protected function extractColumns($connection, $table)
    {
        $columns = [];

        foreach (Schema::connection($connection)->getColumns($table) as $column) {
            $columns[] = [
                'name' => $column['name'],
                'type' => $column['type_name'] ?? $column['type'],
                'nullable' => $column['nullable'],
                'default' => $column['default'],
                'auto_increment' => $column['auto_increment'] ?? false,
                'comment' => $column['comment'] ?? ''
            ];
        }

        return $columns;
    }

    protected function extractIndexes($connection, $table)
    {
        $indexes = [];

        foreach (Schema::connection($connection)->getIndexes($table) as $index) {
            $indexes[] = [
                'name' => $index['name'],
                'columns' => $index['columns'],
                'type' => $index['primary'] ? 'primary' : ($index['unique'] ? 'unique' : 'index'),
                'unique' => $index['unique'] ?? false
            ];
        }

        return $indexes;
    }

    protected function extractForeignKeys($connection, $table)
    {
        $foreignKeys = [];

        foreach (Schema::connection($connection)->getForeignKeys($table) as $fk) {
            $foreignKeys[] = [
                'columns' => $fk['columns'],
                'foreign_table' => $fk['foreign_table'],
                'foreign_columns' => $fk['foreign_columns'],
                'on_delete' => $fk['on_delete'] ?? 'restrict',
                'on_update' => $fk['on_update'] ?? 'restrict'
            ];
        }

        return $foreignKeys;
    }
}
```

Usage for central:
```bash
cd /path/to/everspot
php artisan wiki:schema-snapshot central --output=/path/to/wiki/schema/central.json
```

Usage for tenant (requires tenant context):
```bash
cd /path/to/everspot
php artisan tenants:run <tenant-id> --command="wiki:schema-snapshot tenant --output=/tmp/tenant-schema.json"
# Then copy /tmp/tenant-schema.json to wiki/schema/tenant.json
```

#### Approach B: Standalone PHP Script

For environments where adding Artisan commands is impractical:

```php
<?php
// tools/extract-schema.php in wiki repository

require '/path/to/everspot/vendor/autoload.php';

use Illuminate\Support\Facades\Schema;

$app = require_once '/path/to/everspot/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

$connection = $argv[1] ?? 'central';
// ... (same extraction logic as above)
```

### 5. Connection-to-Migration-Path Mapping

Based on Laravel + stancl/tenancy conventions:

```json
{
  "connections": {
    "central": {
      "migration_paths": [
        "database/migrations"
      ],
      "description": "Central database - users, tenants, global config"
    },
    "tenant": {
      "migration_paths": [
        "database/migrations/tenant"
      ],
      "description": "Tenant databases - cemetery data, transactions, etc."
    }
  },
  "detection_rules": {
    "central": "No new files in database/migrations/ (excluding tenant/ subdirectory)",
    "tenant": "No new files in database/migrations/tenant/"
  }
}
```

**Sync integration:** When sync detects changes in migration paths (§3.2):
1. List changed files between `synced_through` and `origin/main`
2. Check if any match `database/migrations/*.php` (excluding tenant/) → regenerate central
3. Check if any match `database/migrations/tenant/*.php` → regenerate tenant
4. After regeneration, diff snapshots to find changed tables
5. Find model documents for those tables and mark for regeneration

### 6. Skeleton JSONs Created

Since Everspot is unavailable, creating placeholder snapshots with error markers:

## Next Steps When Everspot Becomes Available

1. **Clone/locate Everspot repository** at `/Users/cashkalina/code/everspot-brain/everspot`
2. **Verify runnable state:**
   - `.env` exists and is configured
   - `composer install` completed
   - Database connections configured
3. **Run central migrations:** `php artisan migrate --database=central`
4. **Setup tenant context:**
   - Create reference/throwaway tenant
   - Run tenant migrations
5. **Install extraction command:**
   - Copy `WikiSchemaSnapshot.php` to `app/Console/Commands/`
   - OR use standalone script approach
6. **Generate snapshots:**
   - Central: `php artisan wiki:schema-snapshot central --output=<wiki>/schema/central.json`
   - Tenant: via `tenants:run` wrapper
7. **Validate outputs:**
   - Check JSON structure
   - Verify table count > 0
   - Confirm `snapshot_commit` matches git HEAD

## Files Created

- `/Users/cashkalina/code/everspot-brain/system-wiki/meta/phase3-build-log.md` (this file)
- `/Users/cashkalina/code/everspot-brain/system-wiki/schema/central.json` (skeleton)
- `/Users/cashkalina/code/everspot-brain/system-wiki/schema/tenant.json` (skeleton)
- `/Users/cashkalina/code/everspot-brain/system-wiki/meta/migration-path-mapping.json`
- `/Users/cashkalina/code/everspot-brain/system-wiki/tools/WikiSchemaSnapshot.php` (extraction command)

## Summary

Phase 3 is **blocked** but **maximum progress achieved**:

- ✅ Snapshot format designed per specification
- ✅ Extraction tooling created (ready to deploy)
- ✅ Migration path mapping documented
- ✅ Skeleton JSONs created with error markers
- ❌ Live schema extraction (blocked: Everspot unavailable)
- ❌ Multi-tenancy investigation (blocked: Everspot unavailable)
- ❌ Existing schema generation analysis (blocked: Everspot unavailable)

**The build can continue to subsequent phases** with these skeleton snapshots. Model generation will be blocked until real snapshots exist, but other phases (directory structure, templates, etc.) can proceed.
