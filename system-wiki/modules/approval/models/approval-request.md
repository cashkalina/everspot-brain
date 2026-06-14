---
model: ApprovalRequest
module: Approval
table: approval_requests
connection: tenant
primary_source: modules/Approval/Models/ApprovalRequest.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Approval/Models/ApprovalAction.php
  - modules/Common/Models/User.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Approval/Observers/ApprovalRequestObserver.php
  - modules/Approval/Providers/ApprovalServiceProvider.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [ApprovalAction, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# ApprovalRequest

## Overview

`ApprovalRequest` is the central record in Everspot's internal approval workflow. It is a **polymorphic pivot** model: any approvable entity (order, contract, interment record, etc.) can have a single active `ApprovalRequest` at a time, linked via the `approvable` morphTo relationship. Models participate in this workflow by using the [HasApprovals](../../../system/traits/index.md#hasapprovals) trait.

The request tracks a `status` (`submitted`, `approved`, `rejected`, `deleted`) and an `is_record_locked` flag. When the status is `submitted`, the parent record is locked against further edits. A request moves through statuses exclusively via [ApprovalAction](./approval-action.md) creation — direct status mutation is handled internally by the `onSubmittal`, `onApproval`, `onRejection`, and `onDeletion` lifecycle methods, which also dispatch the corresponding domain events (`ApprovalSubmitted`, `ApprovalApproved`, `ApprovalRejected`, `ApprovalDeleted`).

The `ApprovalRequestObserver` enforces a business rule on `saving`: an approvable entity may not have more than one active approval request at a time.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| approvable_type | varchar | No | - | Polymorphic type (morph class name of the approvable entity) |
| approvable_id | bigint | No | - | Polymorphic ID of the approvable entity |
| status | varchar | No | - | Current status: `submitted`, `approved`, `rejected`, or `deleted` |
| is_record_locked | tinyint | No | 0 | Whether the approvable entity is locked due to an active submission |
| approved_by | bigint | Yes | - | FK → users: the staff member who approved the request |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp (timezone-aware cast) |
| updated_at | timestamp | Yes | - | Last update timestamp (timezone-aware cast) |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `approved_by` → `users.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** composite index on (`approvable_type`, `approvable_id`); single-column indexes on `status`, `approved_by`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `created_at` → `TimezonedDateTime::class` — timezone-aware creation timestamp
- `updated_at` → `TimezonedDateTime::class` — timezone-aware update timestamp

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** _None._ (no `$guarded` declared; inherits BaseModel behavior — mass-assignment is unrestricted)
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
const STATUSES = [
    'submitted' => ['label' => 'Submitted', 'color' => 'info'],
    'approved'  => ['label' => 'Approved',  'color' => 'success'],
    'rejected'  => ['label' => 'Rejected',  'color' => 'danger'],
    'deleted'   => ['label' => 'Deleted',   'color' => 'secondary'],
];

protected static $defaultStatus = 'submitted';
```

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — approval requests are soft-deleted (`deleted_at`) on the `onDeletion` lifecycle path, never hard-deleted

## Relationships

- `approvable()` — morphTo: the parent entity under review (any model using [HasApprovals](../../../system/traits/index.md#hasapprovals))
- `approvalActions()` — has many [ApprovalAction](./approval-action.md): the ordered history of actions taken on this request
- `approvedBy()` — belongs to [User](../../../system/models/user.md) (`approved_by`): the staff member who approved the request

## Scopes

- `active(Builder $query)` — filters to requests whose status is **not** `approved` or `deleted` (i.e., `submitted` or `rejected`)
- `inactive(Builder $query)` — filters to requests with status `approved` or `deleted`

## Events

- Dispatches `ApprovalSubmitted` (on submittal action creation) via `onSubmittal()`
- Dispatches `ApprovalApproved` (on approval action creation) via `onApproval()`
- Dispatches `ApprovalRejected` (on rejection action creation) via `onRejection()`
- Dispatches `ApprovalDeleted` (on deletion action creation) via `onDeletion()`

These events are dispatched from within the lifecycle methods called by the `ApprovalActionObserver::created` hook.

## Observers

- `ApprovalRequestObserver` — registered in `ApprovalServiceProvider::registerObservers()` (`ApprovalRequest::observe(ApprovalRequestObserver::class)`). Handles:
  - `saving` — enforces uniqueness: if this request is active, checks that the approvable entity has no other active `ApprovalRequest`; returns `false` to abort if one is found
  - `creating`, `created`, `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs

## Key Methods

- `createAction(string $type, ?string $message = null)` — creates an [ApprovalAction](./approval-action.md) of the given type for the authenticated user; wraps in a DB transaction; delegates lifecycle transition to the observer; returns a redirect response (success or error)
- `canSubmit(): void` — calls `canSubmitApproval()` on the approvable if it exists; throws `CannotExecuteAction` on failure
- `canApprove(): void` — calls `canApproveApproval()` on the approvable; throws `CannotExecuteAction` if not in `submitted` status
- `canReject(): void` — calls `canRejectApproval()` on the approvable; throws `CannotExecuteAction` if not in `submitted` status
- `canDelete(): void` — calls `canDeleteApproval()` on the approvable; throws `CannotExecuteAction` if not active
- `mostRecentAction()` — returns the most recent [ApprovalAction](./approval-action.md) (via `mostRecent` scope)
- `getLastSubmitter()` — returns the [User](../../../system/models/user.md) who most recently submitted the request (from the latest `submittal` action)
- `onSubmittal(ApprovalAction $action)` — transitions status to `submitted`, locks the record, saves, dispatches `ApprovalSubmitted`
- `onApproval(ApprovalAction $action)` — transitions status to `approved`, unlocks, sets `approved_by`, saves, dispatches `ApprovalApproved`
- `onRejection(ApprovalAction $action)` — transitions status to `rejected`, unlocks, saves, dispatches `ApprovalRejected`
- `onDeletion(ApprovalAction $action)` — transitions status to `deleted`, unlocks, saves, soft-deletes the request, dispatches `ApprovalDeleted`
- `shouldRecordBeLocked(): bool` — returns `true` when status is `submitted`
- `handleLocking(): void` — sets `is_record_locked` to reflect `shouldRecordBeLocked()`
- `isActive(): bool` — `true` if status is not `approved` or `deleted`
- `isInactive(): bool` — `true` if status is `approved` or `deleted`
- `isSubmitted(): bool` — `true` if status is `submitted` _(derived from status check — not a persisted field)_
- `getColor(): string` — Bootstrap color class for current status from `STATUSES`
- `getTypeVerb(string $type): string` — human verb for an action type (`submit`, `approve`, `reject`, `delete`)

## Common Usage

```php
// Typically accessed via the approvable model's HasApprovals trait:
$approvalRequest = $order->approvalRequest;

// Submit for approval (from a controller):
return $approvalRequest->createAction('submittal', 'Ready for manager review.');

// Approve (from a policy-guarded action):
return $approvalRequest->createAction('approval');

// Reject with feedback:
return $approvalRequest->createAction('rejection', 'Missing purchase order number.');

// Delete/cancel an active request:
return $approvalRequest->createAction('deletion', 'No longer needed.');

// Query active requests globally:
$pending = ApprovalRequest::active()->get();

// Check lock state:
if ($approvalRequest->isActive()) {
    // record is locked; edits are blocked by HasApprovals::isLocked()
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
