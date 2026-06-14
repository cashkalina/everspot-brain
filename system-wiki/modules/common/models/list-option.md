---
model: ListOption
module: Common
table: list_options
connection: tenant
primary_source: modules/Common/Models/ListOption.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/ListOptionObserver.php
  - modules/Common/Models/ListOptionType.php
traits:
  - SoftDeletes
related_models: [ListOptionType]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# ListOption

## Overview

The ListOption model is the system-wide controlled-vocabulary store. Nearly every enumerated field in Everspot — customer titles, suffixes, customer types, interment types, opportunity stages, veteran branches, ranks, awards, and many more — is backed by a `list_option` row of the appropriate `type`.

Each option has a `type` string (e.g. `'customer_type'`), a `key` (machine-readable slug), a `name` (display label), and lock flags (`lock_edit`, `lock_delete`) that protect system-defined options from being renamed or removed by end users. The `list_option_type_id` column optionally links to a [ListOptionType](./list-option-type.md) row for options that have a dynamic type definition in the database.

The static `$allowedTypes` map on the class documents all built-in type keys and their labels, while `getTypes()` merges database-driven types for dynamic extensibility. Soft deletes allow options to be deactivated without removing historical references. Lifecycle events are handled by `ListOptionObserver`, registered in `CommonServiceProvider`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| type | varchar | No | - | List option type key (e.g. `customer_type`) |
| list_option_type_id | bigint | Yes | - | FK → list_option_types: dynamic type definition |
| key | varchar | No | - | Machine-readable option key (slug) |
| name | varchar | No | - | Human-readable option label |
| lock_edit | tinyint | No | 0 | When 1, prevents editing by end users |
| lock_delete | tinyint | No | 0 | When 1, prevents deletion by end users |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `list_option_type_id` → `list_option_types.id`

**Indexes:** FK-backing index on `list_option_type_id`.

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['type', 'list_option_type_id', 'name', 'key', 'lock_delete', 'lock_edit']`

**Static data:**
```php
public static $allowedTypes = [
    'certificate_type', 'crm_source', 'customer_relation', 'customer_type',
    'department', 'interment_type', 'name_suffix', 'name_title',
    'opportunity_stage', 'opportunity_type', 'order_type', 'service_type',
    'sex', 'veteran_award', 'veteran_branch', 'veteran_discharge_status',
    'veteran_rank', 'veteran_service_status', 'veteran_war',
    'work_order_category', /* ... media_collection_* and external_approval_type_* types */
];
```

## Accessors & Mutators

- `getFormattedTypeAttribute(): string` — human-readable type label; prefers `listOptionType->name` relationship, falls back to `$allowedTypes[$this->type]` or raw `type`
- `getModelInferredName(): ?string` — `"{formatted_type} - {name}"`
- `getModelTitle(): ?string` — delegates to `getModelInferredName()`
- `getModelFullTitle(): ?string` — delegates to `getModelTitle()`

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — list options are soft-deleted, never hard-deleted

## Relationships

- `listOptionType()` — belongs to [ListOptionType](./list-option-type.md) (`list_option_type_id`): the dynamic type definition for this option

## Scopes

- `type($query, $type): Builder` — filters by `type` column value

## Events

_None._

## Observers

- `ListOptionObserver` — registered in `CommonServiceProvider::registerObservers()` (`ListOption::observe(ListOptionObserver::class)`). Handles:
  - `saving` — validates/normalizes option data
  - `created`, `updated`, `deleted`, `restored`, `forceDeleted` — cache invalidation and side effects

## Key Methods

- `getTypes(): array` *(static)* — merges database `ListOptionType` rows with the static `$allowedTypes` fallback; returns a keyed array with `label`, `enableCreate`, `enableUpdate`, `enableDelete` per type
- `getTypeData(string $type): array` *(static)* — returns the type config array for a specific type key
- `getPreventCreateTypes(): array` *(static)* — override point to prevent creation of options for specific types (default: `[]`)
- `getPreventUpdateTypes(): array` *(static)* — override point for types whose options cannot be edited (default: `[]`)
- `getPreventDeleteTypes(): array` *(static)* — override point for types whose options cannot be deleted (default: `[]`)

## Common Usage

```php
// Get all customer type options
$customerTypes = ListOption::type('customer_type')->get();

// Find a specific option by key
$military = ListOption::type('veteran_branch')
    ->where('key', 'veteran_branch-army')
    ->first();

// Get all type metadata for the UI
$typeMeta = ListOption::getTypes();

// Soft delete an option
$option->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
