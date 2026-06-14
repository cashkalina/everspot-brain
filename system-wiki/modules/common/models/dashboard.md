---
model: Dashboard
module: Common
table: dashboards
connection: tenant
primary_source: modules/Common/Models/Dashboard.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/DashboardObserver.php
  - modules/Common/Models/DashboardElement.php
  - modules/Common/Models/User.php
traits:
  - HasByUserFields
  - HasSearch
  - SoftDeletes
related_models: [DashboardElement, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Dashboard

## Overview

The Dashboard model represents a configurable dashboard page that can be assigned to users. Each dashboard has a title, description, layout, and type (standard or custom), and contains one or more [DashboardElement](./dashboard-element.md) records that define the widgets displayed.

Dashboards are linked to users via a many-to-many `dashboard_user` pivot table, with a per-user `is_default` flag tracking which dashboard is that user's home screen. The model carries soft deletes and audit user stamps via traits, and supports search indexing.

Lifecycle events (including user assignment propagation and cache invalidation) are handled by `DashboardObserver`, registered in `CommonServiceProvider`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| type | varchar | No | custom | Dashboard type (`standard` or `custom`) |
| title | varchar | No | - | Dashboard title |
| description | text | Yes | - | Optional description |
| layout | varchar | No | - | Layout identifier (key into `LAYOUTS` constant) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

**Constants:**
```php
const LAYOUTS = [
    'layout-1' => [
        'label'       => 'Layout 1',
        'description' => 'A simple layout.',
        'view'        => 'common::components.dashboard.layouts.layout-1',
    ],
];

const TYPES = [
    'standard' => 'Standard',
    'custom'   => 'Custom',
];
```

**Search fields:** `['title', 'description']`

## Accessors & Mutators

- `getFormattedTypeAttribute(): string` — human-readable type label from `TYPES` constant
- `getFormattedLayoutAttribute(): string` — human-readable layout label from `LAYOUTS` constant
- `getSelectFieldNameAttribute(): string` — display name for select fields (the dashboard title)

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; searchable on `title` and `description`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — dashboards are soft-deleted, never hard-deleted

## Relationships

- `dashboardElements()` — has many [DashboardElement](./dashboard-element.md): the widget elements on this dashboard
- `users()` — belongs-to-many [User](./user.md) via `dashboard_user` (pivot `id`, `is_default`): users who have this dashboard assigned

## Scopes

_None._

## Events

_None._

## Observers

- `DashboardObserver` — registered in `CommonServiceProvider::registerObservers()` (`Dashboard::observe(DashboardObserver::class)`). Handles:
  - `creating` — sets default values before creation
  - `created`, `updated` — propagates changes
  - `deleting`, `deleted`, `restored`, `forceDeleted` — cascade and cleanup hooks

## Key Methods

- `getGroupedElements(): Collection` — returns dashboard elements ordered by `sort_order`, grouped by `location`
- `getLayout(): array` — returns the layout config array from `LAYOUTS` for this dashboard's `layout` value; throws `\Exception` if the layout key is not found

## Common Usage

```php
// Create a dashboard
$dashboard = Dashboard::create([
    'title'  => 'My Dashboard',
    'layout' => 'layout-1',
    'type'   => 'custom',
]);

// Assign to a user as default
$dashboard->users()->attach($user->id, ['is_default' => true]);

// Get grouped widget elements
$groups = $dashboard->getGroupedElements();

// Get layout view path
$layoutView = $dashboard->getLayout()['view'];
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
