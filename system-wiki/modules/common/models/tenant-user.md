---
model: TenantUser
module: Common
table: tenant_users
connection: central
primary_source: modules/Common/Models/TenantUser.php
source_paths: []
traits: []
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# TenantUser

## Overview

The TenantUser model is a minimal central-database table that maps user accounts to tenants. It lives in the **central** database alongside `tenants` and `domains`, providing a global registry of which users have access to which tenants. This enables cross-tenant user lookup and routing at the platform level.

Like [TenantIntegration](./tenant-integration.md), the model is extremely thin — it extends Laravel's base `Model` (not `BaseModel`), has no traits, no custom methods, no observers, and no defined relationships. All fields are mass-assignable.

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| tenant_id | varchar | No | - | FK → tenants: the tenant this user belongs to |
| user_id | bigint | No | - | Reference to the tenant-side user record ID |
| email | varchar | No | - | User's email address (denormalized for cross-tenant lookup) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `tenant_id` → `tenants.id`

**Indexes:** FK-backing index on `tenant_id`; index on `email` for cross-tenant lookup.

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
// Find all tenants a user belongs to (by email)
$tenantUsers = TenantUser::where('email', 'john@example.com')->get();

// Find all users for a specific tenant
$tenantUsers = TenantUser::where('tenant_id', 'acme-funeral')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
