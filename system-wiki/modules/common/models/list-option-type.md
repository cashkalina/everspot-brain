---
model: ListOptionType
module: Common
table: list_option_types
connection: tenant
primary_source: modules/Common/Models/ListOptionType.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/ListOption.php
traits:
  - SoftDeletes
related_models: [ListOption]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# ListOptionType

## Overview

The ListOptionType model defines the categories (types) of controlled-vocabulary options in the system. Each row gives a `key` (machine-readable identifier), a `name` (label), an optional `description`, and an `is_system` flag that marks built-in types managed by the application itself.

System types (`is_system = true`) cannot be deleted — a `deleting` hook in `boot()` throws a `RuntimeException` if deletion is attempted. Custom types (`is_system = false`) can be created, renamed, and removed by administrators.

ListOptionType rows are referenced by [ListOption](./list-option.md) via `list_option_type_id`, allowing `ListOption::getTypes()` to merge database-driven type definitions with the static fallback in `ListOption::$allowedTypes`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| key | varchar | No | - | Machine-readable type key |
| name | varchar | No | - | Human-readable type label |
| description | text | Yes | - | Optional description |
| is_system | tinyint | No | 0 | Whether this is a built-in system type (cannot be deleted) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

- `is_system` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['key', 'name', 'description', 'is_system']`

## Accessors & Mutators

- `getOptionsCountAttribute(): int` — returns the count of [ListOption](./list-option.md) rows associated with this type
- `getModelInferredName(): ?string` — returns `name`
- `getModelTitle(): ?string` — delegates to `getModelInferredName()`
- `getModelFullTitle(): ?string` — delegates to `getModelTitle()`

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — list option types are soft-deleted, never hard-deleted

## Relationships

- `listOptions()` — has many [ListOption](./list-option.md) (`list_option_type_id`): options belonging to this type

## Scopes

- `system(Builder $query): Builder` — filters to `is_system = true`
- `custom(Builder $query): Builder` — filters to `is_system = false`

## Events

- `boot()` — `deleting` hook: throws `RuntimeException` when attempting to delete a system type (`is_system = true`)

## Observers

_None registered._

## Key Methods

_None beyond scopes, accessors, and the boot hook._

## Common Usage

```php
// Get all custom (user-defined) types
$customTypes = ListOptionType::custom()->get();

// Get all system types
$systemTypes = ListOptionType::system()->get();

// Count options for a type
$type = ListOptionType::where('key', 'customer_type')->first();
echo $type->options_count;

// Attempting to delete a system type throws RuntimeException
try {
    $systemType->delete();
} catch (\RuntimeException $e) {
    // "System list option types cannot be deleted."
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
