---
model: Tenant
module: Common
table: tenants
connection: central
primary_source: modules/Common/Models/Tenant.php
source_paths:
  - app/Models/Plan.php
  - modules/Common/Models/Domain.php
traits:
  - HasDatabase
  - HasDomains
  - HasSchemalessAttributes
  - HasSettings
related_models: [Domain, Plan]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# Tenant

## Overview

The Tenant model represents a cemetery organization (client) in the multi-tenant Everspot system. It lives in the **central** database and extends Stancl Tenancy's `BaseTenant`, implementing `TenantWithDatabase` to provision a dedicated per-tenant database. The `HasDatabase` and `HasDomains` traits add database provisioning and domain-to-tenant routing respectively.

Each tenant has a primary contact, address, billing plan, and integration configuration stored in `config_data` (via `HasSchemalessAttributes`). Several accessors expose computed attributes from `config_data` for the accounting system and payment processor type/ID. The `HasSettings` trait allows per-tenant settings via the polymorphic `Setting` model.

On `saved`, the `booted()` hook fires analytics and CRM sync calls. The `getCustomColumns()` static method tells Stancl Tenancy which columns live on the central `tenants` table (vs. the JSON `data` column used by the framework).

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | varchar | No | - | Tenant identifier (string, e.g. `acme-funeral`) |
| plan_id | bigint | No | - | FK → plans: the tenant's billing plan |
| name | varchar | No | - | Tenant display name |
| legal_name | varchar | Yes | - | Official legal name |
| address_line_one | varchar | Yes | - | Street address line 1 |
| address_line_two | varchar | Yes | - | Street address line 2 |
| city | varchar | Yes | - | City |
| state | varchar | Yes | - | State/province (stored as string, not FK) |
| zip_code | varchar | Yes | - | ZIP / postal code |
| contact_phone | varchar | Yes | - | Primary contact phone |
| contact_email | varchar | Yes | - | Primary contact email |
| website | varchar | Yes | - | Website URL |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| data | json | Yes | - | Stancl Tenancy extra data (framework-managed) |
| config_data | json | Yes | - | Tenant configuration store (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) / [HasSettings](../../../system/traits/index.md#hassettings) — see trait docs) |

**Primary key:** `id`

**Foreign keys:** `plan_id` → `plans.id`

**Indexes:** FK-backing index on `plan_id`.

## Casts

- `staff_api_expiration` → `datetime`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

No explicit `$fillable` or `$guarded` — inherits `BaseTenant` behavior; `getCustomColumns()` defines the tenant's own columns for the framework.

## Accessors & Mutators

- `getAddressAttribute(): string` — one-line address from `address_line_one`, `address_line_two`, `city`, `state`, `zip_code`
- `getAccountingSystemAttribute(): ?string` — reads `config_data.integrations.accounting_system`
- `setAccountingSystemAttribute($value): void` — writes `config_data['integrations.accounting_system']`
- `getAccountingSystemIdAttribute(): ?string` — reads `config_data.integrations.accounting_system_id`
- `setAccountingSystemIdAttribute($value): void` — writes `config_data['integrations.accounting_system_id']`
- `getPaymentProcessorAttribute(): ?string` — reads `config_data.integrations.payment_processor`
- `setPaymentProcessorAttribute($value): void` — writes `config_data['integrations.payment_processor']`
- `getPaymentProcessorIdAttribute(): ?string` — reads `config_data.integrations.payment_processor_id`
- `setPaymentProcessorIdAttribute($value): void` — writes `config_data['integrations.payment_processor_id']`

## Traits

- [HasDatabase](../../../system/traits/index.md#hasdatabase) — Stancl Tenancy: per-tenant database provisioning and migration
- [HasDomains](../../../system/traits/index.md#hasdomains) — Stancl Tenancy: domain-to-tenant routing via the `domains` table
- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` JSON with dot-notation access
- [HasSettings](../../../system/traits/index.md#hassettings) — key-value settings store via polymorphic `Setting` model

## Relationships

- `plan()` — belongs to [Plan](../../../system/models/plan.md) (`plan_id`): the tenant's billing plan
- `primary_domain()` — has one [Domain](./domain.md) where `is_primary = true`: the tenant's primary domain

Inherits `domains()` (has many [Domain](./domain.md)) from `HasDomains`.

## Scopes

_None._

## Events

- `booted()` — `saved` hook: fires `analytics()->tenantUpdated($tenant)` and `crm()->syncTenant($tenant)`

## Observers

_None registered._

## Key Methods

- `getCustomColumns(): array` *(static)* — returns the list of column names that belong to the `tenants` central table (used by Stancl Tenancy to distinguish columns from the framework's JSON `data` column)
- `hasDefault(string $field): bool` — returns `true` when `config_data->$field === 'default'`
- `hasPaymentsEnabled(): bool` — returns `true` when `payment_processor !== 'pp-default'` (i.e. a real payment processor is configured)
- `getCurrentFullDomain()` — resolves the current full domain URL root for the tenant based on `DomainTenantResolver::$currentDomain`
- `getModelFullTitle(): string` — returns `"Tenant - {name}"`

## Common Usage

```php
// Get the current tenant (within tenant context)
$tenant = tenancy()->tenant;

// Access accounting system type
echo $tenant->accounting_system;   // e.g. "qbo"

// Check if payments are enabled
if ($tenant->hasPaymentsEnabled()) {
    // show payment options
}

// Get the primary domain URL
$url = $tenant->primary_domain->url_root;

// Tenant-scoped setting
$timezone = setting('timezone', $tenant);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
