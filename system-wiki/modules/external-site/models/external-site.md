---
model: ExternalSite
module: ExternalSite
table: external_sites
connection: tenant
primary_source: modules/ExternalSite/Models/ExternalSite.php
source_paths:
  - app/Models/BaseModel.php
  - modules/ExternalSite/Providers/ExternalSiteServiceProvider.php
  - app/Providers/EventServiceProvider.php
traits:
  - SoftDeletes
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [integration, admin]
---

# ExternalSite

## Overview

The ExternalSite model represents a configured external-facing website integration — for example, a public memorial or obituary portal — that the cemetery has set up through Everspot. Each site has a `type` (backed by the `ExternalSiteType` enum), a human-readable `name`, and a URL-safe `slug` (unique; used as the route key) that identifies it in web URLs.

Sites carry a boolean `is_public` flag controlling whether their content is publicly visible, and a `config_data` JSON column that holds arbitrary site-configuration key-value pairs specific to each site type (resolved by `SiteConfigFactory`). Soft deletes allow sites to be deactivated without loss of record history.

This is a lightweight configuration model with no direct relationships to other Everspot domain models — it stands alone as a registry of external integrations.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| type | varchar | No | - | Site type (backed by `ExternalSiteType` enum) |
| name | varchar | No | - | Human-readable site name |
| slug | varchar | No | - | URL-safe unique identifier; used as route key |
| is_public | tinyint | No | 0 | Whether the site is publicly accessible |
| config_data | json | Yes | - | Arbitrary site-type-specific configuration data |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `slug`

**Foreign keys:** _None._

## Casts

- `type` → `ExternalSiteType::class` (PHP-backed enum)
- `is_public` → `boolean`
- `config_data` → `array`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `is_public` defaults to `0` (false) at the database level.

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — external sites are soft-deleted, preserving configuration history

## Relationships

_None._

## Scopes

_None._

## Events

_None._

## Observers

_None registered._ The `ExternalSiteServiceProvider::registerObservers()` method is present but empty.

## Key Methods

- `getRouteKeyName(): string` — returns `'slug'`; routes to external sites use the `slug` column instead of `id`
- `getSiteConfig(): SiteConfig` — delegates to `SiteConfigFactory::create($this)` and returns the type-specific configuration object

## Routing

`getRouteKeyName()` returns `'slug'` — route-model binding resolves `ExternalSite` records by their `slug` column rather than the default `id`.

## Common Usage

```php
// Find a site by slug (route-model binding uses slug automatically)
$site = ExternalSite::where('slug', 'oak-hill-memorial')->firstOrFail();

// Get type-specific configuration
$config = $site->getSiteConfig();

// Filter to public sites
$publicSites = ExternalSite::where('is_public', true)->get();

// Create a new external site
$site = ExternalSite::create([
    'type'      => ExternalSiteType::Memorial,
    'name'      => 'Oak Hill Memorial Portal',
    'slug'      => 'oak-hill-memorial',
    'is_public' => true,
    'config_data' => ['theme' => 'light'],
]);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
