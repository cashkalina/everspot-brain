---
model: TenantIntegration
module: Common
table: tenant_integrations
connection: central
primary_source: modules/Common/Models/TenantIntegration.php
source_paths: []
traits: []
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [integration, admin]
---

# TenantIntegration

## Overview

The TenantIntegration model is a minimal central-database table that cross-references tenants with their integrations. It lives in the **central** database (alongside `tenants` and `domains`) and provides a cross-tenant audit trail or routing layer for integration connections.

The model is extremely thin — it extends Laravel's base `Model` directly (not `BaseModel`), has no traits, no custom methods, no observers, and no relationships defined on the class. All fields are mass-assignable (`$guarded = []`).

The table links `tenant_id` (FK → `tenants.id`), `integration_id` (a cross-database reference to a tenant-side integration record), `system_type`, `system_id`, and connectivity timestamps — mirroring key fields from the tenant-side [Integration](./integration.md) model.

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| tenant_id | varchar | No | - | FK → tenants: the tenant this integration belongs to |
| integration_id | bigint | No | - | Reference to the tenant-side integration record ID |
| system_type | varchar | No | - | Integration type identifier (e.g. `qbo`, `stripe`) |
| system_id | varchar | Yes | - | External system account/company ID |
| connected_at | datetime | No | - | When the integration was connected |
| disconnected_at | datetime | Yes | - | When the integration was disconnected |
| pause_syncing | tinyint | No | 0 | Whether sync is paused |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `tenant_id` → `tenants.id`

**Indexes:** FK-backing index on `tenant_id`.

## Casts

_None._

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

_None declared on the model._

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._

## Common Usage

```php
// Query central DB for all active integrations across all tenants
$activeIntegrations = TenantIntegration::whereNotNull('connected_at')
    ->whereNull('disconnected_at')
    ->get();

// Find integrations for a specific tenant
$tenantIntegrations = TenantIntegration::where('tenant_id', 'acme-funeral')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
