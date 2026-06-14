---
title: Snapshot-schema Command
purpose: Regenerate schema/central.json and schema/tenant.json from live, migrated databases
last_updated: 2026-06-14
---

# Snapshot-schema

**Purpose:** Regenerate `schema/central.json` and `schema/tenant.json` from live, migrated databases.

**Operation type:** Write

**Inputs:**
- Runnable Everspot instance with:
  - Migrated central database
  - Configured tenant context (stancl/tenancy) with at least one migrated tenant database
- `wiki.config.json` for Everspot repository location

**Preconditions:**
- Everspot codebase is functional and can boot
- Central database is migrated to latest
- Tenant context can be entered and a fresh tenant database exists and is migrated

**Process:**

### Capture central schema

1. From the Everspot repository, run Laravel schema introspection on the central connection:
   ```bash
   php artisan schema:dump --connection=central --format=json
   ```
   Or use an equivalent method (e.g., `DB::connection('central')->getDoctrineSchemaManager()->listTableDetails()`).

2. Output format (JSON):
   ```json
   {
     "snapshot_commit": "<current origin/main commit hash>",
     "connection": "central",
     "tables": {
       "users": {
         "columns": [
           {"name": "id", "type": "bigint", "nullable": false, "default": null},
           {"name": "email", "type": "varchar(255)", "nullable": false, "default": null},
           ...
         ],
         "indexes": [
           {"name": "primary", "columns": ["id"], "unique": true},
           {"name": "users_email_unique", "columns": ["email"], "unique": true}
         ],
         "foreign_keys": [
           {"columns": ["role_id"], "references": "roles.id", "on_delete": "cascade"}
         ]
       },
       ...
     }
   }
   ```

3. Record `snapshot_commit` as the current `origin/main` commit hash of Everspot at the time of generation.

4. Write to `schema/central.json`.

### Capture tenant schema

1. Enter tenant context using stancl/tenancy:
   ```bash
   php artisan tenants:run <tenant-id> --command="schema:dump --connection=tenant --format=json"
   ```
   Or programmatically: `Tenant::find($id)->run(function() { /* introspect schema */ })`.

2. Use a reference tenant or create a throwaway tenant, migrate it, capture schema, optionally destroy it. Any freshly migrated tenant is authoritative because all tenants share one schema.

3. Output same JSON format as central, with `"connection": "tenant"` and `snapshot_commit` set to Everspot's current `origin/main`.

4. Write to `schema/tenant.json`.

### Validation

After generation:

1. Verify each snapshot is valid JSON and contains expected structure.
2. Check that at least one table exists per connection (empty snapshots indicate failure).
3. Cross-check: every model document's `table` should appear in exactly one snapshot. If a documented table is missing, flag for investigation.

**Outputs:**
- `schema/central.json` with current schema
- `schema/tenant.json` with current schema
- Each stamped with `snapshot_commit` for table-change detection

**Error handling:**
- Everspot cannot boot — fail with clear error. If this is a permanent environment issue, produce a skeleton JSON structure with a `"error": "everspot_unavailable"` marker and document in `meta/` as a blocker for schema-dependent operations.
- Tenant context cannot be entered — fail, report stancl/tenancy configuration issue
- Schema introspection returns empty or malformed — fail, do not overwrite existing snapshots
- JSON write failure — fail, report file system issue
