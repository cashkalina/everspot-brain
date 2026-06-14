---
trait: SoftDeletes
owning_module: framework
framework: Illuminate\Database\Eloquent\SoftDeletes
source_paths:
  - vendor/laravel/framework/src/Illuminate/Database/Eloquent/SoftDeletes.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# SoftDeletes

**Namespace:** `Illuminate\Database\Eloquent\SoftDeletes`
**Package:** Laravel Framework (`laravel/framework`)
**Registry entry:** [index.md#softdeletes](./index.md#softdeletes)

## Purpose

Laravel's standard soft-delete mechanism. Instead of issuing a `DELETE` statement, Eloquent sets a `deleted_at` timestamp on the row. All subsequent queries automatically exclude soft-deleted rows via a global scope. Soft-deleted rows can be restored (`restore()`), force-deleted (`forceDelete()`), or included in queries with `withTrashed()`.

In Everspot, soft-deletes are the default deletion pattern for most domain models. Hard deletes are used only for low-level pivot/log records.

## Contributed Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `deleted_at` | timestamp | Yes | Null when the record is active; set to the deletion timestamp when soft-deleted. Model docs carry `(via SoftDeletes — see trait doc)` in their Schema table. |

## Contributed Casts

| Attribute | Cast |
|-----------|------|
| `deleted_at` | `datetime` (applied by the framework automatically for this column) |

## Contributed Relationships

None.

## Contributed Scopes / Global Scopes

- **Global scope `SoftDeletingScope`** — automatically applied to all queries on the model; restricts results to rows where `deleted_at IS NULL` unless `withTrashed()` or `onlyTrashed()` is used.

| Scope | Description |
|-------|-------------|
| `withTrashed()` | Include soft-deleted rows in results. |
| `onlyTrashed()` | Return only soft-deleted rows. |
| `withoutTrashed()` | Explicitly exclude soft-deleted rows (default behavior). |

## Contributed Methods

| Method | Description |
|--------|-------------|
| `delete()` | Sets `deleted_at` and saves (instead of issuing SQL DELETE). |
| `restore()` | Sets `deleted_at` to null and saves, restoring the record. |
| `forceDelete()` | Issues an actual SQL DELETE, permanently removing the row. |
| `trashed()` | Returns `true` if `deleted_at` is not null (record is soft-deleted). |
| `isForceDeleting()` | Returns `true` during a `forceDelete()` operation. |

## Configuration / Contract

The model's database table must have a `deleted_at` timestamp column (nullable). No interface is required.

## Used By

Discoverable by grepping `traits:` frontmatter for `SoftDeletes` across model docs, or `use SoftDeletes` / `use Illuminate\Database\Eloquent\SoftDeletes` in Everspot source.
