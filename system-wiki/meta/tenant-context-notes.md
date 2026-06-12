---
title: Multi-Tenancy and Tenant Context Notes
status: foundational
version: 1
last_updated: 2026-06-12
---

# Multi-Tenancy and Tenant Context Notes

This document records expectations and implementation notes about Everspot's multi-tenancy architecture, specifically for schema snapshot generation.

## Overview

Everspot uses **stancl/tenancy** for multi-tenant database isolation. Each tenant has its own database with an identical schema. The wiki needs to capture this schema once (since all tenants share it) for model documentation.

## Expected Architecture

### Two Database Connections

**Central connection:**
- Configured in `config/database.php` as `'central'` or similar
- Stores: users, tenants table, roles, permissions, global config
- Single shared database across all tenants
- Models: `app/Models/User`, `app/Models/Tenant`, core auth models
- Migrations: `database/migrations/` (root level)

**Tenant connection:**
- Configured in `config/database.php` as `'tenant'` or via stancl/tenancy config
- Stores: cemetery data, plots, burials, contracts, payments, services
- One database per tenant, all sharing identical schema
- Models: `modules/*/Models/*` (most module models)
- Migrations: `database/migrations/tenant/` (subdirectory)

### Connection Determination in Models

Models declare their connection in two ways:

1. **Explicit `$connection` property:**
   ```php
   class Payment extends Model
   {
       protected $connection = 'tenant';
   }
   ```

2. **Convention/default:**
   - No explicit property → use default connection
   - Default varies by model location:
     - `app/Models/*` → typically central
     - `modules/*/Models/*` → typically tenant

The wiki derives connection by:
1. Checking model's `$connection` property
2. Falling back to conventional default
3. **Validating** against schema snapshot membership (table must exist in exactly one snapshot)

## Tenant Context Mechanics

### Entering Tenant Context

**Via Artisan command:**
```bash
php artisan tenants:run <tenant-id> --command="some:command"
```

**Programmatically:**
```php
use App\Models\Tenant;

$tenant = Tenant::find($tenantId);
$tenant->run(function () {
    // Code here executes in tenant context
    // DB queries use tenant database
    Schema::getTables(); // Returns tenant tables
});
```

**Alternative (manual initialization):**
```php
tenancy()->initialize($tenant);
// ... do work ...
tenancy()->end();
```

### Schema Extraction Strategy

Since all tenants share one schema, we can:

**Option 1: Use existing tenant**
- Identify any existing tenant (first, last, doesn't matter)
- Enter its context
- Extract schema
- All tenants will have identical schema

**Option 2: Create throwaway tenant**
- Create fresh tenant: `php artisan tenants:create`
- Run migrations on it
- Extract schema
- Optionally destroy: `php artisan tenants:delete <id>`

**Option 3: Use reference tenant**
- Maintain one permanent "reference" or "schema" tenant
- Never used for actual data
- Only for schema extraction and testing

The wiki's `tools/generate-snapshots.sh` implements Option 1 (use first available tenant) with fallback to Option 2 (manual tenant ID).

## Expected Tenancy Configuration

Based on typical stancl/tenancy setup:

**config/tenancy.php:**
```php
'tenant_model' => \App\Models\Tenant::class,

'central_domains' => [
    'localhost',
],

'database' => [
    'central_connection' => 'central',
    'tenant_connection' => 'tenant',
],

'migration_parameters' => [
    '--path' => ['database/migrations/tenant'],
],
```

**TenancyServiceProvider registration:**
- Likely in `app/Providers/TenancyServiceProvider.php`
- Configures tenancy initialization (domain vs. subdomain vs. custom)
- Sets up automatic tenant resolution

## Verification When Everspot Becomes Available

When the Everspot repository is accessible, verify:

1. **Package installed:**
   ```bash
   grep stancl/tenancy composer.json
   ```

2. **Configuration exists:**
   ```bash
   ls config/tenancy.php
   ```

3. **Tenant model location:**
   ```bash
   git show origin/main:app/Models/Tenant.php
   ```

4. **Migration directories:**
   ```bash
   ls database/migrations/
   ls database/migrations/tenant/
   ```

5. **Artisan commands available:**
   ```bash
   php artisan list | grep tenant
   # Expected: tenants:create, tenants:migrate, tenants:run, tenants:list, etc.
   ```

6. **Test tenant context:**
   ```bash
   php artisan tinker
   >>> \App\Models\Tenant::first()
   >>> tenancy()->initialize(\App\Models\Tenant::first())
   >>> Schema::connection('tenant')->getTables()
   ```

## Schema Snapshot Generation Flow

**For central (straightforward):**
```bash
cd /path/to/everspot
php artisan wiki:schema-snapshot central --output=/path/to/wiki/schema/central.json
```

**For tenant (requires context):**
```bash
cd /path/to/everspot

# Find a tenant ID
php artisan tenants:list
# Or: php artisan tinker --execute='echo \App\Models\Tenant::first()->id;'

# Generate via tenant context
php artisan tenants:run <tenant-id> --command="wiki:schema-snapshot tenant --output=/tmp/tenant.json"

# Copy to wiki
cp /tmp/tenant.json /path/to/wiki/schema/tenant.json
```

**Or use the automated script:**
```bash
cd /path/to/wiki
./tools/generate-snapshots.sh [optional-tenant-id]
```

## Edge Cases and Considerations

**Mixed-connection models:**
- Some models might query both connections
- Each model still belongs to exactly one for its primary table
- Related models on other connection are still linkable

**Tenant-unaware queries:**
- Code outside tenant context always uses central
- Models with `$connection = 'tenant'` will fail if accessed outside tenant context
- This is correct behavior - prevents cross-tenant data leaks

**Schema changes during snapshot:**
- Central schema changes: simply regenerate central snapshot
- Tenant schema changes: regenerate from ANY tenant (they all match)
- If a migration runs on some tenants but not others, those tenants are out of sync (application-level issue, not wiki concern)

**No tenants exist:**
- Snapshot generation fails
- Resolution: create at least one tenant, run migrations on it
- Throwaway tenant is fine - schema is what matters, not data

## Integration with Wiki Commands

**Generate command (§2):**
- Reads model class from Everspot source
- Checks model's `$connection` property
- Looks up table in appropriate snapshot (central.json or tenant.json)
- Renders schema section from snapshot

**Sync command (§3.2):**
- Monitors migration paths (database/migrations/ and database/migrations/tenant/)
- On tenant migration change: regenerates tenant.json from any available tenant
- On central migration change: regenerates central.json
- Diffs snapshots to find changed tables
- Regenerates docs for models of those tables

**Snapshot-schema command (§4):**
- Central: direct connection introspection
- Tenant: enters tenant context, introspects, exits context
- Both output same JSON format
- Both record current git commit for drift detection

## References

- stancl/tenancy documentation: https://tenancyforlaravel.com/
- foundation.md §3.3 - Schema snapshots architecture
- commands.md §4 - Snapshot-schema command specification
- phase3-build-log.md - Implementation notes and blocker details
