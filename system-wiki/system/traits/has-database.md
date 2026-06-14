---
trait: HasDatabase
owning_module: framework
framework: Stancl\Tenancy\Database\Concerns\HasDatabase
source_paths:
  - vendor/stancl/tenancy/src/Database/Concerns/HasDatabase.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasDatabase

**Namespace:** `Stancl\Tenancy\Database\Concerns\HasDatabase`
**Package:** `stancl/tenancy`
**Registry entry:** [index.md#hasdatabase](./index.md#hasdatabase)

## Purpose

Part of the [stancl/tenancy](https://tenancyforlaravel.com/) multi-tenancy package. Adds database-related functionality to the `Tenant` model: creating, migrating, and dropping per-tenant databases. Works in conjunction with the `TenantWithDatabase` contract.

In Everspot, `HasDatabase` is used on `Modules\Common\Models\Tenant` (along with `HasDomains`) to implement database-per-tenant tenancy. When a new Tenant record is created, the tenancy package provisions a fresh database for it and runs migrations.

## Contributed Columns

The column set depends on the `TenantWithDatabase` contract implementation and tenancy configuration. Stancl tenancy stores tenancy identifiers in the `tenants` table (managed by the base `BaseTenant` model). `HasDatabase` itself typically manages a `tenancy_db_name` value stored in the tenant's data JSON or a dedicated column.

## Contributed Casts

None contributed directly by the trait.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods (key subset from the package)

| Method | Description |
|--------|-------------|
| `database()` | Returns the tenant's database manager instance. |
| `getTenantDatabaseName()` | Returns the database name for this tenant. |
| `createDatabase()` | Creates the tenant's database. |
| `deleteDatabase()` | Drops the tenant's database. |
| `migrateTenant()` | Runs tenant migrations on the tenant's database. |

## Configuration / Contract

The model must implement `Stancl\Tenancy\Contracts\TenantWithDatabase`. The `stancl/tenancy` package must be installed and configured (`config/tenancy.php`). Tenancy bootstrappers must be registered to switch database connections per request.

## Used By

Used only on `Modules\Common\Models\Tenant`. Discoverable by `use HasDatabase` / `use Stancl\Tenancy\Database\Concerns\HasDatabase` in Everspot source.
