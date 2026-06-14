---
model: DashboardElement
module: Common
table: dashboard_elements
connection: tenant
primary_source: modules/Common/Models/DashboardElement.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/Dashboard.php
traits:
  - SoftDeletes
related_models: [Dashboard]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin]
---

# DashboardElement

## Overview

The DashboardElement model represents a single widget (component) placed on a [Dashboard](./dashboard.md). Each element specifies which component class it renders (`component`), its position within the dashboard layout (`location` and `sort_order`), and optional `config` data as JSON.

Elements are instantiated at render time via `DashboardComponentFactory`, which resolves the `component` string to a concrete `DashboardComponent` implementation. The `override_permissions` flag allows an element to bypass the standard permission check for its content.

The model uses soft deletes. It has no observers and no custom audit stamps.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| dashboard_id | bigint | No | - | FK → dashboards: the parent dashboard |
| component | varchar | No | - | Component class identifier |
| config | json | Yes | - | Component-specific configuration |
| location | int | No | - | Layout location slot number |
| sort_order | int | No | - | Display order within the location |
| override_permissions | tinyint | No | 0 | Whether to bypass permission checks for this element |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `dashboard_id` → `dashboards.id`

**Indexes:** FK-backing index on `dashboard_id`.

## Casts

- `config` → `array`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

- `getFormattedComponentAttribute(): string` — returns the human-readable title of the resolved `DashboardComponent` instance

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — dashboard elements are soft-deleted, never hard-deleted

## Relationships

- `dashboard()` — belongs to [Dashboard](./dashboard.md) (`dashboard_id`): the parent dashboard

## Scopes

- `forLocation($query, int $location)` — filters elements to a specific layout `location` slot

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getComponent(): DashboardComponent` — resolves the `component` string via `DashboardComponentFactory::create()` and returns the concrete component instance for rendering

## Common Usage

```php
// Add an element to a dashboard
$element = $dashboard->dashboardElements()->create([
    'component'  => 'recent-orders',
    'location'   => 1,
    'sort_order' => 0,
    'config'     => ['limit' => 10],
]);

// Get the component for rendering
$component = $element->getComponent();
echo $component->title();   // "Recent Orders"

// Elements in a specific location slot
$sidebarWidgets = $dashboard->dashboardElements()
    ->forLocation(2)
    ->orderBy('sort_order')
    ->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
