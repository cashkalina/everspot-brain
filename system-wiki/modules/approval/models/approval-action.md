---
model: ApprovalAction
module: Approval
table: approval_actions
connection: tenant
primary_source: modules/Approval/Models/ApprovalAction.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Approval/Models/ApprovalRequest.php
  - modules/Common/Models/User.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Approval/Observers/ApprovalActionObserver.php
  - modules/Approval/Providers/ApprovalServiceProvider.php
traits: []
related_models: [ApprovalRequest, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# ApprovalAction

## Overview

`ApprovalAction` records a single event in an internal approval workflow — a submittal, approval, rejection, or deletion performed by a staff member on a given [ApprovalRequest](./approval-request.md). Each action captures who performed it (`performed_by`), when (`performed_at`), the action type, and an optional explanatory message.

When an `ApprovalAction` is created, the `ApprovalActionObserver` immediately delegates to the parent request's lifecycle handler (`onSubmittal`, `onApproval`, `onRejection`, or `onDeletion`), which transitions the request's status and dispatches the appropriate domain event. Actions are never updated or deleted — they form an immutable audit trail for the request.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| approval_request_id | bigint | No | - | FK → approval_requests: the parent request this action belongs to |
| type | varchar | No | - | Action type: `submittal`, `approval`, `rejection`, or `deletion` |
| performed_by | bigint | No | - | FK → users: the staff member who performed the action |
| performed_at | datetime | No | - | Timestamp of the action (timezone-aware) |
| message | text | Yes | - | Optional message or comment from the performer |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `approval_request_id` → `approval_requests.id`; `performed_by` → `users.id`

**Indexes:** `approval_actions_approval_request_id_index` on `approval_request_id`; FK-backing index on `performed_by`.

## Casts

- `performed_at` → `TimezonedDateTime::class` — timezone-aware handling of the action timestamp (see `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)

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

_None._

## Relationships

- `approvalRequest()` — belongs to [ApprovalRequest](./approval-request.md) (`approval_request_id`): the parent internal approval request this action belongs to
- `performedBy()` — belongs to [User](../../../system/models/user.md) (`performed_by`): the staff member who performed the action

## Scopes

- `mostRecent(Builder $query)` — orders by `performed_at` descending (latest first)

## Events

_None defined on the model._

## Observers

- `ApprovalActionObserver` — registered in `ApprovalServiceProvider::registerObservers()` (`ApprovalAction::observe(ApprovalActionObserver::class)`). Handles:
  - `created` — routes the action to the parent request's appropriate lifecycle handler (`onSubmittal`, `onApproval`, `onRejection`, or `onDeletion`) based on `type`; those handlers transition the request status and dispatch domain events (`ApprovalSubmitted`, `ApprovalApproved`, `ApprovalRejected`, `ApprovalDeleted`)
  - `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs

## Key Methods

- `hasMessage(): bool` — returns `true` if `message` is non-null and non-empty
- `isSubmittal(): bool` — returns `true` if `type == 'submittal'`
- `isApproval(): bool` — returns `true` if `type == 'approval'`
- `isRejection(): bool` — returns `true` if `type == 'rejection'`
- `isDeletion(): bool` — returns `true` if `type == 'deletion'`
- `getColor(): string` — returns the Bootstrap color class for this action type (resolved via `ApprovalRequest::STATUSES`)
- `getTypeIcon(): string` — returns a Bootstrap icon class (`bi-*`) appropriate to the action type
- `getPastTenseVerb(): string` — returns the past-tense label for the action type (`submitted`, `approved`, `rejected`, `deleted`)

## Common Usage

```php
// Actions are created via ApprovalRequest::createAction(), not directly:
$result = $approvalRequest->createAction('submittal', 'Ready for review.');
$result = $approvalRequest->createAction('approval');
$result = $approvalRequest->createAction('rejection', 'Missing documentation.');

// Retrieve the most recent action on a request
$latest = $approvalRequest->approvalActions()->mostRecent()->first();

// Check action properties
if ($action->isApproval()) {
    echo $action->getTypeIcon();   // 'bi-check-circle'
    echo $action->getColor();      // 'success'
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
