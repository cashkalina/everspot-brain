---
model: Task
module: Task
table: tasks
connection: tenant
primary_source: modules/Task/Models/Task.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Task/Observers/TaskObserver.php
  - modules/Task/Providers/TaskServiceProvider.php
  - modules/Common/Models/User.php
traits:
  - HasFactory
  - HasByUserFields
related_models: [User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Task

## Overview

The Task model represents an actionable work item that can be attached to any entity in the Everspot system via a polymorphic `taskable` relationship. Tasks are the primary mechanism for tracking follow-up work, reminders, and to-dos across customers, orders, interments, opportunities, and any other module that adopts the pattern.

Each task carries a title, optional description and notes, a priority level (low/medium/high), a lifecycle status (not-started/in-progress/on-hold/completed), an optional due date, and an `assigned_to` user. The `completed` flag and `completed_at` timestamp record the moment a task is finished, allowing both boolean and datetime queries. Soft-delete columns (`deleted_at`, `deleted_by`) are present in the schema even though the model itself does not declare `SoftDeletes`; deletion behaviour is managed by the observer via the `PreDeleteTask` action.

Audit user stamps (`created_by`, `updated_by`, `deleted_by`) are contributed by the `HasByUserFields` trait. The observer fires analytics and dispatches assignment events whenever a task is saved.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| taskable_type | varchar | Yes | - | Polymorphic owner type |
| taskable_id | varchar | Yes | - | Polymorphic owner id |
| title | varchar | No | - | Task title |
| description | text | Yes | - | Optional long description |
| notes | text | Yes | - | Free-form notes |
| priority | varchar | No | medium | Task priority (`low`, `medium`, `high`) |
| status | varchar | No | - | Task lifecycle status (`not-started`, `in-progress`, `on-hold`, `completed`) |
| completed | tinyint | No | 0 | Boolean flag — whether the task is completed |
| due_date | date | Yes | - | Optional due date |
| assigned_to | bigint | No | - | FK → users: assigned user |
| completed_at | datetime | Yes | - | Timestamp when the task was completed (timezoned cast) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (managed by `PreDeleteTask` action; `SoftDeletes` trait not declared on model) |

**Primary key:** `id`

**Foreign keys:** `assigned_to` → `users.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `assigned_to`, `completed`, `due_date`, `priority`, `status`, `title` (single-column); composite index on (`taskable_type`, `taskable_id`); FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `due_date` → `date`
- `completed_at` → `TimezonedDateTime::class` — timezone-aware datetime cast (see `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ — `priority` defaults to `medium` at the database level; `status` defaults to `not-started` via `BaseModel::handleDefaultStatus()` on creating.

**Constants / static config:**
```php
const STATUSES = [
    'not-started' => ['label' => 'Not Started', 'color' => 'warning'],
    'in-progress' => ['label' => 'In Progress', 'color' => 'info'],
    'on-hold'     => ['label' => 'On Hold',     'color' => 'danger'],
    'completed'   => ['label' => 'Completed',   'color' => 'secondary'],
];

const PRIORITIES = [
    'low'    => 'Low',
    'medium' => 'Medium',
    'high'   => 'High',
];

protected static $defaultStatus = 'not-started';
```

## Accessors & Mutators

- `getPriorityBadgeAttribute(): string` — returns an HTML badge `<span>` for the task's priority (low/medium/high), colour-coded with Bootstrap soft-badge classes
- `getAssignedToAvatarAttribute(): ?string` — returns the avatar of the assigned user (delegates to `$this->assignedTo?->avatar`)

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — wires the custom `TaskFactory` via `newFactory()` for model factories
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backed by the `created_by` / `updated_by` / `deleted_by` columns

## Relationships

- `taskable()` — morphTo: the parent entity this task belongs to (may be Customer, Order, Opportunity, Interment, or any other taskable model)
- `assignedTo()` — belongs to [User](../../common/models/user.md) (`assigned_to`): the user responsible for completing this task

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle behaviour is handled by `TaskObserver` (see Observers).

## Observers

- `TaskObserver` — registered in `TaskServiceProvider::registerObservers()` (`Task::observe(TaskObserver::class)`). Handles:
  - `saved` — dispatches `TaskAssigned` or `TaskUnassigned` events via `DispatchEventForAssignmentChanges` whenever `assigned_to` changes
  - `created` — fires `analytics()->track('Task Created')`
  - `deleting` — wraps deletion in a DB transaction, runs `PreDeleteTask` action

## Key Methods

- `getModelInferredName(): ?string` — returns `$this->title`; used by `BaseModel` to generate human-readable titles for UI display and logging

## Common Usage

```php
// Attach a task to a customer
$task = Task::create([
    'taskable_type' => Customer::class,
    'taskable_id'   => $customer->id,
    'title'         => 'Follow up on quote',
    'priority'      => 'high',
    'assigned_to'   => $user->id,
    'due_date'      => now()->addDays(3),
]);

// Query all tasks for a customer
$tasks = $customer->tasks()->get();

// Mark complete
$task->update([
    'completed'    => true,
    'completed_at' => now(),
    'status'       => 'completed',
]);

// Filter by status (via BaseModel dynamic scope)
$open = Task::notStarted()->get();
$inProgress = Task::inProgress()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
