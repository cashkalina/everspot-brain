---
trait: HasExternalIds
owning_module: Common
source_paths:
  - modules/Common/Traits/HasExternalIds.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasExternalIds

**Source:** `modules/Common/Traits/HasExternalIds.php`
**Registry entry:** [system/traits/index.md#hasexternalids](../../../system/traits/index.md#hasexternalids)

## Purpose

Attaches a polymorphic collection of external identifiers to a model. Each `ExternalId` row pairs a `system` string (e.g. `'quickbooks'`, `'stripe'`, `'default'`) with an `external_id` value, allowing a single Everspot record to have multiple external IDs from different source systems without adding per-system columns.

Provides upsert, delete, and lookup helpers keyed by system name.

## Contributed Columns

No columns are added to the using model's table. External IDs live in the `external_ids` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `externalIds()` | `MorphMany` | `Modules\Common\Models\ExternalId` | All external ID records for this model, across all systems. |

## Contributed Scopes

None on the using model (scopes for filtering by system are on the `ExternalId` model itself via `forSystem()`).

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `addExternalId()` | `(string $externalId, ?string $system = 'default'): ExternalId` | Upserts an external ID for the given system (`updateOrCreate` on `system`). |
| `addOrDeleteExternalId()` | `(?string $externalId, ?string $system = 'default'): ?ExternalId` | Adds the external ID if non-empty; deletes the existing one for the system if `$externalId` is empty or null. Returns the ExternalId or `null`. |
| `getExternalId()` | `(string $system = 'default'): ?string` | Returns the `external_id` string for the given system, or `null` if none exists. |
| `hasExternalId()` | `(?string $system = null): bool` | Returns `true` if `getExternalId($system)` is non-null. |

## Configuration / Contract

No interface required. The `ExternalId` model and its `external_ids` table must exist (part of the Common module's schema). `BaseModel` uses this trait, so all concrete Everspot models that extend `BaseModel` inherit it.

## Used By

Applied on `BaseModel` (inherited by all concrete models). Directly importable in models that do not extend BaseModel. Discoverable by grepping `traits:` frontmatter for `HasExternalIds`, or `use HasExternalIds` in Everspot source.
