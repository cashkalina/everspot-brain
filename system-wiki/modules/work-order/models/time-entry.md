---
model: TimeEntry
module: WorkOrder
table: time_entries
connection: tenant
primary_source: modules/WorkOrder/Models/TimeEntry.php
source_paths:
  - app/Models/BaseModel.php
  - modules/WorkOrder/Observers/TimeEntryObserver.php
  - modules/WorkOrder/Providers/WorkOrderServiceProvider.php
  - modules/Common/Models/User.php
  - modules/Common/Scopes/MostRecentDateSort.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, service]
---

# TimeEntry

## Overview

The TimeEntry model records a single block of time logged against a time-trackable parent entity — most commonly a [WorkOrder](./work-order.md). It is a polymorphic child model: the `timeable_type` / `timeable_id` pair identifies the parent (e.g. a `WorkOrder`), allowing any model that uses the `HasTimeEntries` trait to accumulate time entries.

Each time entry captures the date the work was performed, the amount of time (in hours, stored as a decimal), a free-text description, and the user who performed the work (`performed_by`). A global scope (`MostRecentDateSort`) automatically orders all queries by `date` descending, so the most recent entries appear first without callers needing to specify an order.

When a time entry is created, saved, or deleted, the `TimeEntryObserver` calls the corresponding lifecycle hook (`onCreate`, `onSave`, `onDelete`) on the model, which in turn calls `calculateTotalTime()` on the parent `timeable` to keep the parent's aggregate `time_spent` column synchronized. The model carries soft deletes and audit user stamps via traits.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| timeable_type | varchar | No | - | Polymorphic parent model class name |
| timeable_id | bigint | No | - | Polymorphic parent model id |
| date | date | Yes | - | Date the work was performed |
| amount | decimal | No | - | Time logged in hours |
| description | text | Yes | - | Description of the work performed |
| performed_by | bigint | No | - | FK → users: the user who performed the work |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `performed_by`, `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** composite index on (`timeable_type`, `timeable_id`); single-column index on `performed_by`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `date` — the date work was performed

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — time entries are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `timeable()` — morphTo: the parent entity this time entry belongs to (e.g. a [WorkOrder](./work-order.md))
- `performedBy()` — belongs to [User](../../common/models/user.md) (`performed_by`): the user who performed the work

## Scopes

- **Global scope: `MostRecentDateSort`** — automatically applied via `booted()`; orders all queries by `date` descending so the most recent entries appear first

## Events

- `booted()` — registers the `MostRecentDateSort` global scope via `addGlobalScope()`

## Observers

- `TimeEntryObserver` — registered in `WorkOrderServiceProvider::registerObservers()` (`TimeEntry::observe(TimeEntryObserver::class)`). Handles:
  - `saved` — calls `$timeEntry->onSave()` on the model instance, which notifies the parent `timeable` and recalculates `time_spent`
  - `created` — calls `$timeEntry->onCreate()` on the model instance
  - `deleted` — calls `$timeEntry->onDelete()` on the model instance, triggering `calculateTotalTime()` on the parent to decrement `time_spent`

## Key Methods

- `onCreate(): void` — calls `onTimeEntryCreate($this)` on the parent `timeable` if the method exists, then calls `calculateTotalTime()` on the parent; typically invoked by `TimeEntryObserver::created()`
- `onSave(): void` — calls `onTimeEntrySave($this)` on the parent `timeable` if the method exists, then calls `calculateTotalTime()` on the parent; typically invoked by `TimeEntryObserver::saved()`
- `onDelete(): void` — calls `onTimeEntryDelete($this)` on the parent `timeable` if the method exists, then calls `calculateTotalTime()` on the parent; typically invoked by `TimeEntryObserver::deleted()`

## Common Usage

```php
// Log time against a work order (via WorkOrder's HasTimeEntries relationship)
$workOrder->timeEntries()->create([
    'date'         => today(),
    'amount'       => 1.5,   // hours
    'performed_by' => $user->id,
    'description'  => 'Removed monument debris',
]);

// List all time entries for a work order (automatically sorted most recent first)
$entries = $workOrder->timeEntries()->withTrashed()->get();

// Direct model query (global MostRecentDateSort applies)
$recentEntries = TimeEntry::where('timeable_type', WorkOrder::class)
    ->where('timeable_id', $workOrder->id)
    ->get();

// The parent's time_spent is updated automatically by the observer.
// After any create/save/delete, $workOrder->fresh()->time_spent reflects the new total.
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
