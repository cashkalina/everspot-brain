---
model: WorkOrderCategory
module: WorkOrder
table: work_order_categories
connection: tenant
primary_source: modules/WorkOrder/Models/WorkOrderCategory.php
source_paths:
  - app/Models/BaseModel.php
  - modules/WorkOrder/Models/WorkOrder.php
traits: []
related_models: [WorkOrder, WorkOrderCategory]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, service]
---

# WorkOrderCategory

## Overview

The WorkOrderCategory model represents a category used to classify work orders within the cemetery management system. Categories help staff and managers organize work orders by type (e.g., "Grounds Maintenance", "Monument Repair", "Construction"), making it easier to filter, report on, and assign work.

Categories support a simple one-level parent/child hierarchy via the `parent_category_id` self-referential foreign key, allowing broad categories to group related sub-categories. Categories can be activated or deactivated via the `is_active` flag — the `active` scope restricts queries to active categories, which is the typical state used when populating category dropdowns in the UI.

The model is minimal: no traits beyond `BaseModel` inheritance, no observers, and no soft deletes. It owns `hasMany` work orders and a self-referential `belongsTo` for the parent category.

**Note on dual categorization:** Work orders have a `work_order_category_id` column that is a FK to `list_options` (filtered `type=work_order_category`), not directly to this table. `WorkOrderCategory` is a dedicated standalone category model in addition to the `ListOption`-based category. Both may be in use — this model provides the richer hierarchical structure.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| parent_category_id | bigint | Yes | - | FK → work_order_categories: optional parent category for hierarchical grouping |
| name | varchar | No | - | Category display name |
| is_active | tinyint | No | - | Whether this category is active and available for selection |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `parent_category_id` → `work_order_categories.id`

**Indexes:** single-column index on `is_active`; FK-backing index on `parent_category_id`.

## Casts

_None._

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `workOrders()` — has many [WorkOrder](./work-order.md) via conventional FK `work_order_category_id`: work orders classified under this category. **Note:** `work_orders.work_order_category_id` has no DB-level FK constraint in the schema and the `WorkOrder` model's `workOrderCategory()` relationship actually targets `list_options` (filtered `type=work_order_category`), not this table — see the Overview note.
- `parentCategory()` — belongs to [WorkOrderCategory](./work-order-category.md) (`parent_category_id`): the optional parent category

## Scopes

- `active(Builder $query)` — filters to `is_active = true`

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._

## Common Usage

```php
// List all active categories for a dropdown
$categories = WorkOrderCategory::active()->orderBy('name')->get();

// List top-level categories (no parent)
$topLevel = WorkOrderCategory::active()
    ->whereNull('parent_category_id')
    ->orderBy('name')
    ->get();

// List sub-categories of a given category
$subCategories = WorkOrderCategory::active()
    ->where('parent_category_id', $category->id)
    ->orderBy('name')
    ->get();

// Find all work orders in a category
$workOrders = $category->workOrders()->open()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
