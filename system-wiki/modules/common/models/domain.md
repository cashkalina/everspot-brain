---
model: Domain
module: Common
table: domains
connection: central
primary_source: modules/Common/Models/Domain.php
source_paths:
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/DomainObserver.php
  - modules/Common/Models/Tenant.php
traits: []
related_models: [Tenant]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# Domain

## Overview

The Domain model represents a subdomain or custom domain that is mapped to a [Tenant](./tenant.md) for routing purposes. It extends Stancl Tenancy's `BaseDomain` model and lives in the **central** database (not the per-tenant databases). When an HTTP request arrives, the domain is resolved to a tenant via `DomainTenantResolver`, which bootstraps the appropriate tenant context.

Each tenant can have multiple domains, but one is marked `is_primary = true`. The `makePrimary()` helper atomically promotes a domain to primary and updates the in-memory `primary_domain` relation on the parent tenant.

Two URL-related accessors provide the protocol prefix and full root URL, supporting both HTTP and HTTPS depending on the `tenancy.should_use_https` config.

Note: There is a typo in the source — the accessor is named `getProtocalAttribute()` (misspelling of "protocol"); the computed attribute `url_root` references `$this->protocal` accordingly.

Lifecycle side effects (cache clearing, routing updates) are handled by `DomainObserver`, registered in `CommonServiceProvider`.

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | int | No | - | Primary key |
| domain | varchar | No | - | Domain string (e.g. `acme.everspot.app`) |
| tenant_id | varchar | No | - | FK → tenants: the owning tenant |
| is_primary | tinyint | No | 0 | Whether this is the tenant's primary domain |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `tenant_id` → `tenants.id`

**Indexes:** FK-backing index on `tenant_id`.

## Casts

_None declared on the model (inherits from BaseDomain)._

## Attributes

_None declared (inherits from BaseDomain)._

## Accessors & Mutators

- `getProtocalAttribute(): string` — returns `'https://'` or `'http://'` depending on `config('tenancy.should_use_https')` (**note:** accessor key is `protocal` — a typo in the source)
- `getUrlRootAttribute(): string` — returns `$this->protocal . $this->domain` — the full root URL for this domain

## Traits

_None._

## Relationships

Inherits `tenant()` (belongs to [Tenant](./tenant.md)) from `BaseDomain`.

## Scopes

_None._

## Events

_None._

## Observers

- `DomainObserver` — registered in `CommonServiceProvider::registerObservers()` (`Domain::observe(DomainObserver::class)`). Handles:
  - `saved` — triggers domain routing updates
  - `created`, `updated`, `deleted`, `restored`, `forceDeleted` — routing/cache side effects

## Key Methods

- `makePrimary(): static` — sets `is_primary = true` on this domain, clears the flag on sibling domains, updates `$this->tenant->primary_domain` in memory, and returns `$this`

## Common Usage

```php
// Get the tenant's primary domain URL
$url = $tenant->primary_domain->url_root;

// Promote a domain to primary
$domain->makePrimary();

// List all domains for a tenant
$domains = Domain::where('tenant_id', $tenant->id)->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
