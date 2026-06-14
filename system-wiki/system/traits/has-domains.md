---
trait: HasDomains
owning_module: framework
framework: Stancl\Tenancy\Database\Concerns\HasDomains
source_paths:
  - vendor/stancl/tenancy/src/Database/Concerns/HasDomains.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasDomains

**Namespace:** `Stancl\Tenancy\Database\Concerns\HasDomains`
**Package:** `stancl/tenancy`
**Registry entry:** [index.md#hasdomains](./index.md#hasdomains)

## Purpose

Part of the [stancl/tenancy](https://tenancyforlaravel.com/) multi-tenancy package. Adds domain-based tenant identification to the `Tenant` model. Enables the system to route incoming HTTP requests to the correct tenant by matching the request's domain (or subdomain) against the `domains` table.

In Everspot, `HasDomains` is used on `Modules\Common\Models\Tenant` alongside `HasDatabase` to implement full database-per-tenant tenancy with domain-based routing (`DomainTenantResolver`).

## Contributed Columns

No columns on the `tenants` table itself. Domain-to-tenant mappings are stored in a separate `domains` table (managed by the package).

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Description |
|--------|------|-------------|
| `domains()` | `HasMany` | All domain records associated with this tenant (from the `domains` table). |

## Contributed Scopes

None.

## Contributed Methods (key subset from the package)

| Method | Description |
|--------|-------------|
| `createDomain($domain)` | Creates a new domain record for this tenant. |
| `deleteDomain($domain)` | Removes a domain record. |
| `getDomains()` | Returns all domains for the tenant. |

## Configuration / Contract

The model must use `HasDomains` and the tenancy config must specify `DomainTenantResolver` (or compatible) as the tenant resolver. The `domains` table must exist (migrated from `stancl/tenancy`). The `stancl/tenancy` package must be installed.

## Used By

Used only on `Modules\Common\Models\Tenant`. Discoverable by `use HasDomains` / `use Stancl\Tenancy\Database\Concerns\HasDomains` in Everspot source.
