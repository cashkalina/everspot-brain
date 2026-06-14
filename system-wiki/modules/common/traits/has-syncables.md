---
trait: HasSyncables
owning_module: Common
source_paths:
  - modules/Common/Traits/HasSyncables.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasSyncables

**Source:** `modules/Common/Traits/HasSyncables.php`
**Registry entry:** [system/traits/index.md#hassyncables](../../../system/traits/index.md#hassyncables)

## Purpose

Links a model to external-integration sync records (`Syncable` model) through a polymorphic many relationship. Each `Syncable` row maps one Everspot model instance to one integration (e.g. QuickBooks) and optionally one external model type, recording the external ID and sync state.

The trait provides both singular (`syncable()`) and plural (`syncables()`) morphic relationships, plus helpers to look up the sync record for a specific integration or integration+type combination.

## Contributed Columns

No columns are added to the using model's table. Sync records live in the `syncables` pivot table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `syncable()` | `MorphOne` | `Modules\Common\Models\Syncable` | The single primary sync record for this model (first integration found). |
| `syncables()` | `MorphMany` | `Modules\Common\Models\Syncable` | All sync records for this model, across all integrations. |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `syncableForIntegration()` | `(Integration $integration): ?Syncable` | Returns the first `Syncable` matching the given integration. |
| `syncableForIntegrationAndType()` | `(Integration $integration, string $type): ?Syncable` | Returns the `Syncable` matching both integration and `external_model_type`. |
| `hasSyncableForIntegration()` | `(Integration $integration): bool` | Returns `true` if a `Syncable` row exists for this model and the given integration. |

## Configuration / Contract

No interface required. The using model simply adds `use HasSyncables;`. The `Syncable` model and its `syncables` table must exist (part of the Common module's schema).

## Used By

Discoverable by grepping `traits:` frontmatter for `HasSyncables` across model docs, or `use HasSyncables` in Everspot source.
