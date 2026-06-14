---
trait: HasByUserFields
owning_module: Common
source_paths:
  - modules/Common/Traits/HasByUserFields.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasByUserFields

**Source:** `modules/Common/Traits/HasByUserFields.php`
**Registry entry:** [system/traits/index.md#hasbyuserfields](../../../system/traits/index.md#hasbyuserfields)

## Purpose

Adds audit user stamps to a model: automatically records which authenticated user created, last updated, and (if the model uses soft deletes) soft-deleted a record. On `creating`, sets `created_by` to `Auth::id()` if not already set; on `updating`, sets `updated_by`; on `deleted`, sets `deleted_by` and calls `saveQuietly()` to persist it without triggering another event cycle.

`deleted_by` is only populated and included in the field array when the model also uses `SoftDeletes` (detected via `class_uses_recursive`).

## Contributed Columns

These columns are physically present on every table whose model uses this trait. Model docs carry a provenance marker `(via HasByUserFields — see trait doc)` in their Schema table.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `created_by` | bigint | Yes | FK → `users.id` — user who created the record |
| `updated_by` | bigint | Yes | FK → `users.id` — user who last updated the record |
| `deleted_by` | bigint | Yes | FK → `users.id` — user who soft-deleted the record (only on models that also use `SoftDeletes`) |

## Contributed Casts

None. The `_by` columns are plain bigint foreign keys.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `createdBy()` | `BelongsTo` | `Modules\Common\Models\User` | User who created the record |
| `updatedBy()` | `BelongsTo` | `Modules\Common\Models\User` | User who last updated the record |
| `deletedBy()` | `BelongsTo` | `Modules\Common\Models\User` | User who soft-deleted the record |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getByUserFieldsArray()` | `(): array` | Returns the audit field names in play for this model instance (`created_by`, `updated_by`, plus `deleted_by` if soft-delete is active). |
| `hasCreatedBy()` | `(): bool` | Whether `created_by` is in the fields array. |
| `hasUpdatedBy()` | `(): bool` | Whether `updated_by` is in the fields array. |
| `hasDeletedBy()` | `(): bool` | Whether `deleted_by` is in the fields array (requires `SoftDeletes`). |
| `modelHasSoftDelete()` | `(): bool` | Returns `true` if the using model also uses `SoftDeletes`. |

## Boot Behavior

`bootHasByUserFields()` registers three Eloquent model event hooks:

- **`creating`** — sets `created_by = Auth::id()` when `hasCreatedBy()` is true and `created_by` is not already set.
- **`updating`** — sets `updated_by = Auth::id()` when `hasUpdatedBy()` is true and `updated_by` is not already set.
- **`deleted`** — sets `deleted_by = Auth::id()` when `hasDeletedBy()` is true and `deleted_by` is not already set; persists via `saveQuietly()`.

## Configuration / Contract

No interface required. The trait detects `SoftDeletes` automatically at runtime via `class_uses_recursive`. No properties need to be defined on the using model.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasByUserFields` across model docs, or `use HasByUserFields` in Everspot source.
