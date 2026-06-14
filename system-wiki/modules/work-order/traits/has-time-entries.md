---
trait: HasTimeEntries
owning_module: WorkOrder
source_paths:
  - modules/WorkOrder/Traits/HasTimeEntries.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasTimeEntries

**Source:** `modules/WorkOrder/Traits/HasTimeEntries.php`
**Registry entry:** [system/traits/index.md#hastimeentries](../../../system/traits/index.md#hastimeentries)

## Purpose

Attaches time-tracking capability to a model via the polymorphic `TimeEntry` model. Time entries record individual time logs against a model instance (e.g. a `WorkOrder`). Provides access to all time entries and a method to recalculate and persist the total time spent.

## Contributed Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `time_spent` | — | Yes | Total time spent (sum of all `TimeEntry.amount` values). Present only when the using model's table has a `time_spent` column. Model docs carry `(via HasTimeEntries — see trait doc)` if applicable. |

_The trait checks for `time_spent` in `getTableColumns()` before writing it, so it is safe to use on models that do not have the column (the recalculation is simply skipped)._

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `timeEntries()` | `MorphMany` | `Modules\WorkOrder\Models\TimeEntry` | All time entry records for this model instance (via `timeable` morph). |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `calculateTotalTime()` | `(): void` | Sums all `TimeEntry.amount` values for this model and saves the total to `time_spent` if the column exists and the value has changed. Calls `$this->save()` (not quiet) when an update is needed. |

## Configuration / Contract

No interface required. The WorkOrder module tables (`time_entries`) must exist. The using model's table may optionally include a `time_spent` column to store the aggregate; if absent, `calculateTotalTime()` is a no-op.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasTimeEntries` across model docs, or `use HasTimeEntries` in Everspot source.
