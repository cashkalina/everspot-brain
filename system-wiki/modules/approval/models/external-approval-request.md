---
model: ExternalApprovalRequest
module: Approval
table: external_approval_requests
connection: tenant
primary_source: modules/Approval/Models/ExternalApprovalRequest.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Approval/Models/ExternalApprovalApprover.php
  - modules/Approval/Models/ExternalApprovalFile.php
  - modules/Approval/Models/ExternalApprovalAction.php
  - modules/Common/Models/ListOption.php
  - modules/Approval/Observers/ExternalApprovalRequestObserver.php
  - modules/Approval/Providers/ApprovalServiceProvider.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [ExternalApprovalAction, ExternalApprovalApprover, ExternalApprovalFile, ListOption]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, integration]
---

# ExternalApprovalRequest

## Overview

`ExternalApprovalRequest` is the top-level record for Everspot's external approval workflow — the mechanism by which staff send documents to external parties (or internal staff acting via a public portal) for review and sign-off. Any model using the [HasExternalApprovals](../../../system/traits/index.md#hasexternalapprovals) trait can be the `approvable` entity, linked via a polymorphic `morphTo` relationship.

A request is associated with an approval type ([ListOption](../../common/models/list-option.md)), zero or more [ExternalApprovalApprover](./external-approval-approver.md) recipients, and one or more [ExternalApprovalFile](./external-approval-file.md) documents. Status progresses through `pending`, `partially_approved`, `approved`, `rejected`, `expired`, and `cancelled`. The `require_all_approvers` flag controls whether unanimous approval or a single approval suffices. Status recalculation is triggered by the `ExternalApprovalActionObserver` whenever an approval or rejection action is recorded.

Staff can bypass the normal approver flow via `staff-approved` / `staff-rejected` actions, which take precedence over individual approver responses. An artisan command (`ExpireExternalApprovalRequestsCommand`) handles scheduled expiry.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| approvable_type | varchar | No | - | Polymorphic type of the entity being approved |
| approvable_id | bigint | No | - | Polymorphic ID of the entity being approved |
| approval_type_id | bigint | No | - | FK → list_options: the type/category of approval |
| status | enum | No | - | Current status: `pending`, `partially_approved`, `approved`, `rejected`, `expired`, `cancelled` |
| require_all_approvers | tinyint | No | 0 | Whether all approvers must approve (vs. any single approver) |
| message | text | Yes | - | Optional message shown to approvers in the portal |
| expires_at | timestamp | Yes | - | When the request expires (null = no expiry) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `approval_type_id` → `list_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** composite index on (`approvable_type`, `approvable_id`); single-column indexes on `status`, `expires_at`, `created_at`, `approval_type_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `require_all_approvers` → `boolean`
- `expires_at` → `datetime`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants:**
```php
const STATUSES = [
    'pending'            => ['label' => 'Pending',            'color' => 'info'],
    'partially_approved' => ['label' => 'Partially Approved', 'color' => 'warning'],
    'approved'           => ['label' => 'Approved',           'color' => 'success'],
    'rejected'           => ['label' => 'Rejected',           'color' => 'danger'],
    'expired'            => ['label' => 'Expired',            'color' => 'secondary'],
    'cancelled'          => ['label' => 'Cancelled',          'color' => 'dark'],
];
```

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — external approval requests are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `approvable()` — morphTo: the entity being approved (any model using [HasExternalApprovals](../../../system/traits/index.md#hasexternalapprovals))
- `approvalType()` — belongs to [ListOption](../../common/models/list-option.md) (`approval_type_id`): the approval category/type
- `approvers()` — has many [ExternalApprovalApprover](./external-approval-approver.md): recipients who can approve or reject
- `files()` — has many [ExternalApprovalFile](./external-approval-file.md): documents attached for review
- `actions()` — morphMany [ExternalApprovalAction](./external-approval-action.md) (`actionable`): the full event log for this request

## Scopes

- `active(Builder $query)` — filters to status `pending` or `partially_approved`
- `pending(Builder $query)` — filters to status `pending`
- `expired(Builder $query)` — filters to status `expired`
- `expiring(Builder $query, int $days = 7)` — filters to pending requests expiring within the next `$days` days and not yet past expiry

## Events

- Dispatches `ExternalApprovalRequestExpired` on `expire()` (when the request transitions to `expired`)

## Observers

- `ExternalApprovalRequestObserver` — registered in `ApprovalServiceProvider::registerObservers()` (`ExternalApprovalRequest::observe(ExternalApprovalRequestObserver::class)`). Handles:
  - `creating` — no-op stub

## Key Methods

- `isActive(): bool` — `true` if status is `pending` or `partially_approved`
- `canBeApproved(): bool` — delegates to `isActive()`; used to gate approver actions
- `canBeRejected(): bool` — delegates to `isActive()`
- `isPastExpirationDate(): bool` — `true` if `expires_at` is set and in the past
- `isCancelled(): bool` — `true` if status is `cancelled` _(derived from status check)_
- `checkAndUpdateStatus(): void` — recalculates and persists the overall request status from loaded action data; staff overrides (`staff-approved`, `staff-rejected`) take precedence, then any rejection, then approval count vs. `require_all_approvers` rule; no-op if already `expired` or `cancelled`
- `expire(): void` — transitions to `expired` and dispatches `ExternalApprovalRequestExpired`; no-op if already resolved
- `cancel(?string $reason = null): void` — transitions to `cancelled` and records a `cancelled` action; no-op if already cancelled
- `recordAction(string $action, ?ExternalApprovalApprover $approver = null, ?string $message = null): void` — creates an [ExternalApprovalAction](./external-approval-action.md) on this request via the static factory
- `getApprovalTypeDisplay(): string` — returns the approval type [ListOption](../../common/models/list-option.md) name (or `'Unknown'`)
- `getApprovedCount(): int` — count of unique approvers who have approved (from loaded actions; excludes staff-override actions)
- `getRejectedCount(): int` — count of unique approvers who have rejected
- `getPendingCount(): int` — total approvers minus responded approvers
- `getProgressPercentage(): int` — percentage of approvals received; 100 if `requiresAnyApprover()` and at least one approved
- `requiresAllApprovers(): bool` — returns `require_all_approvers`
- `requiresAnyApprover(): bool` — inverse of `requiresAllApprovers()`
- `hasStaffApproval(): bool` — `true` if a `staff-approved` action exists for this request
- `hasStaffRejection(): bool` — `true` if a `staff-rejected` action exists for this request
- `getApprovedAt(): ?Carbon` — timestamp of the first approval or staff-approval action
- `getRejectedAt(): ?Carbon` — timestamp of the first rejection or staff-rejection action
- `getDecidingAction(): ?ExternalApprovalAction` — the most recent approval, rejection, or staff override action
- `getColor(): string` — Bootstrap color class for the current status

## Common Usage

```php
// Access via the approvable model's HasExternalApprovals trait:
$requests = $order->externalApprovalRequests;

// Create a new external approval request:
$request = ExternalApprovalRequest::create([
    'approvable_type'      => get_class($order),
    'approvable_id'        => $order->id,
    'approval_type_id'     => $approvalTypeOption->id,
    'require_all_approvers'=> true,
    'message'              => 'Please review and approve the attached order contract.',
    'expires_at'           => now()->addDays(7),
]);

// Add approvers:
$approver = $request->approvers()->create([
    'first_name' => 'Jane',
    'last_name'  => 'Smith',
    'email'      => 'jane@example.com',
]);
$approver->sendNotification();

// Attach files:
$file = $request->files()->create([
    'file_source'  => 'upload',
    'require_view' => true,
    'display_order'=> 1,
]);

// Staff override:
ExternalApprovalAction::record($request, 'staff-approved', null, 'Override — approved by manager.');

// Expiry check (called by artisan command):
if ($request->isPastExpirationDate()) {
    $request->expire();
}

// Cancel a request:
$request->cancel('Customer withdrew request.');

// Query active requests expiring soon:
$expiringSoon = ExternalApprovalRequest::expiring(3)->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
