---
model: CommissionCategory
module: Commission
table: commission_categories
connection: tenant
primary_source: modules/Commission/Models/CommissionCategory.php
source_paths:
  - app/Models/BaseModel.php
traits:
  - SoftDeletes
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, commission, admin]
---

# CommissionCategory

## Overview

The CommissionCategory model is a simple reference-data model that defines named categories for organizing commission structures. A category provides a classification label (its `name`) that can be used to group or distinguish commission plans, rates, or calculations within the system.

The model is intentionally minimal: it has a single fillable attribute (`name`) and carries soft deletes for safe archival. No relationships to other Commission module models are defined on this class — it acts as a lookup/enum-style record that other parts of the commission module reference by convention rather than explicit Eloquent relationships declared here.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Category name |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** _None._

**Indexes:** primary key only.

## Casts

_None._

## Attributes

**Fillable:** `['name']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — categories are soft-deleted, never hard-deleted

## Relationships

_None._

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
// Create a commission category
$category = CommissionCategory::create(['name' => 'Pre-Need Sales']);

// List all active categories
$categories = CommissionCategory::all();

// Soft-delete a category
$category->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
