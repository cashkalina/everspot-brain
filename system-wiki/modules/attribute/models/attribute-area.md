---
model: AttributeArea
module: Attribute
table: attribute_areas
connection: tenant
primary_source: modules/Attribute/Models/AttributeArea.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Attribute/Models/EntityAttribute.php
traits:
  - SoftDeletes
related_models: [EntityAttribute]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# AttributeArea

## Overview

The AttributeArea model defines a logical grouping region for custom attributes within the Everspot EAV system. Each area represents a named section of the attribute UI for a specific model class (identified by the fully-qualified PHP class name in `model_class`), optionally scoped to a `location_id` for multi-location deployments. Within an area, `sort_order` controls the display sequence, and `is_active` gates its visibility.

Areas act as the bridge between the flat attribute definition ([Attribute](./attribute.md)) and the model-specific placement of those attributes: an [EntityAttribute](./entity-attribute.md) row belongs to an area and a model class, connecting the attribute definition to the display context. The `code` column is a unique string identifier for the area that is used for programmatic lookup (e.g. in `scopeForAreaCode` on `AttributeValue`).

Soft deletes are applied so that retired areas retain their historical `entity_attribute` and `attribute_value` records without orphaning them.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_class | varchar | No | - | Fully-qualified PHP class name this area belongs to |
| name | varchar | No | - | Human-readable area name |
| code | varchar | No | - | Unique string code for programmatic lookup |
| description | text | Yes | - | Optional description of the area's purpose |
| location_id | int | Yes | - | Optional FK → location: scope to a specific location |
| sort_order | int | No | 0 | Display sort order within the model class |
| is_active | tinyint | No | 1 | Whether this area is active |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `attribute_areas_code_unique` on `code`

**Indexes:** `attribute_areas_model_class_index` on `model_class`

## Casts

- `is_active` → `boolean`
- `location_id` → `integer`
- `sort_order` → `integer`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['model_class', 'name', 'code', 'description', 'location_id', 'sort_order', 'is_active']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ (column defaults `sort_order = 0` and `is_active = 1` are enforced at the DB level)

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — areas are soft-deleted, never hard-deleted

## Relationships

- `entityAttributes()` — has many [EntityAttribute](./entity-attribute.md): all entity-attribute bindings that belong to this area

## Scopes

- `scopeForModelClass($query, $modelClass): Builder` — filters to areas whose `model_class` matches the given class name
- `scopeForLocation($query, $locationId): Builder` — filters to areas scoped to the given location id
- `scopeActive($query): Builder` — filters to `is_active = true`
- `scopeOrdered($query): Builder` — orders results by `sort_order` ascending

## Events

_None defined on the model._

## Observers

_None registered._

## Key Methods

_None beyond standard Eloquent and the scopes listed above._

## Common Usage

```php
// Find all active attribute areas for the Customer model
$areas = AttributeArea::forModelClass(\Modules\Customer\Models\Customer::class)
    ->active()
    ->ordered()
    ->get();

// Find a specific area by code
$area = AttributeArea::where('code', 'customer-details')->firstOrFail();

// Get all entity-attribute bindings in this area
$bindings = $area->entityAttributes()->with('attribute')->ordered()->get();

// Scope to a specific location
$locationAreas = AttributeArea::forModelClass($modelClass)
    ->forLocation($locationId)
    ->active()
    ->ordered()
    ->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
