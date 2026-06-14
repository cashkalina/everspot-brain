---
model: ExternalApprovalApprover
module: Approval
table: external_approval_approvers
connection: tenant
primary_source: modules/Approval/Models/ExternalApprovalApprover.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Approval/Models/ExternalApprovalRequest.php
  - modules/Approval/Models/ExternalApprovalAction.php
  - modules/Approval/Models/ExternalApprovalFile.php
  - modules/Common/Models/User.php
  - modules/Approval/Observers/ExternalApprovalApproverObserver.php
  - modules/Approval/Providers/ApprovalServiceProvider.php
traits: []
related_models: [ExternalApprovalAction, ExternalApprovalRequest, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, integration]
---

# ExternalApprovalApprover

## Overview

`ExternalApprovalApprover` represents a single person invited to approve or reject an [ExternalApprovalRequest](./external-approval-request.md). Each approver is given a unique, securely-generated `token` that grants them access to the approval portal without requiring an Everspot login.

Approvers come in three forms: **external** (members of the public or outside parties identified only by name and email), **staff** (linked to a [User](../../../system/models/user.md) via the `relatedModel` polymorphic relationship), or **ad-hoc** (no `related_model_type`, added directly). The `isExternal()`, `isStaff()`, and `isAdhoc()` helpers distinguish these cases.

An approver's status (`pending`, `notified`, `viewed`, `approved`, `rejected`, `no_response_needed`) is **derived from their [ExternalApprovalAction](./external-approval-action.md) records** — it is not stored in the database. The `getStatus()` method computes the current status by inspecting loaded action data. The `ExternalApprovalApproverObserver` auto-generates the `token` on first save.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| external_approval_request_id | bigint | No | - | FK → external_approval_requests: the request this approver belongs to |
| related_model_type | varchar | Yes | - | Polymorphic type of linked staff model (null for external/ad-hoc approvers) |
| related_model_id | bigint | Yes | - | Polymorphic ID of linked staff model |
| first_name | varchar | No | - | Approver's first name |
| last_name | varchar | No | - | Approver's last name |
| email | varchar | No | - | Approver's email address |
| token | varchar | No | - | Unique random token for portal access (auto-generated on creation) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Unique constraint:** `external_approval_approvers_token_unique` on `token`

**Foreign keys:** `external_approval_request_id` → `external_approval_requests.id`

**Indexes:** composite index `ext_appr_approvers_related_idx` on (`related_model_type`, `related_model_id`); single-column indexes on `email`, `related_model_type`; FK-backing index on `external_approval_request_id`.

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
const STATUSES = [
    'approved'           => ['label' => 'Approved',           'color' => 'success'],
    'rejected'           => ['label' => 'Rejected',           'color' => 'danger'],
    'no_response_needed' => ['label' => 'No Response Needed', 'color' => 'secondary'],
    'viewed'             => ['label' => 'Viewed',             'color' => 'info'],
    'notified'           => ['label' => 'Notified',           'color' => 'primary'],
    'pending'            => ['label' => 'Pending',            'color' => 'warning'],
];

// Disables BaseModel's default 'pending' status behavior:
protected static $defaultStatus = null;
```

## Accessors & Mutators

- `getStatusAttribute(): string` — virtual accessor computing the derived status; delegates to `getStatus()`; required for BaseModel `status_badge` compatibility

## Traits

_None._

## Relationships

- `externalApprovalRequest()` — belongs to [ExternalApprovalRequest](./external-approval-request.md) (`external_approval_request_id`): the request this approver is assigned to
- `relatedModel()` — morphTo: the linked internal model (typically [User](../../../system/models/user.md) for staff approvers; `null` for external/ad-hoc)
- `actions()` — has many [ExternalApprovalAction](./external-approval-action.md) (`external_approval_approver_id`): all actions performed by this approver

## Scopes

_None._

## Events

_None defined on the model._

## Observers

- `ExternalApprovalApproverObserver` — registered in `ApprovalServiceProvider::registerObservers()` (`ExternalApprovalApprover::observe(ExternalApprovalApproverObserver::class)`). Handles:
  - `saving` — auto-generates a unique 64-character `token` if the approver does not yet have one; retries up to 10 times to ensure uniqueness; throws `\RuntimeException` after exhausting attempts

## Key Methods

- `getStatus(): string` — derives the approver's current status by inspecting loaded `actions` for the parent request; priority order: rejected → approved → no_response_needed (if request is inactive) → viewed → notified → pending
- `getStatusLabel(): string` — human-readable label for the current status (from `STATUSES`)
- `getStatusColor(): string` — Bootstrap color class for the current status
- `canApprove(): bool` — `true` if the request can be approved and the approver has not yet responded
- `canReject(): bool` — `true` if the request can be rejected and the approver has not yet responded
- `canApproveRequest(): bool` — full gate check: request must be approvable, approver must not have responded, all required files must be viewed, all files requiring individual approval must be approved
- `canRejectRequest(): bool` — full gate check: request must be rejectable and approver must not have responded
- `approve(?string $message = null): void` — records an `approved` [ExternalApprovalAction](./external-approval-action.md) for this approver (no-op if `canApprove()` returns false)
- `reject(?string $message = null): void` — records a `rejected` [ExternalApprovalAction](./external-approval-action.md) for this approver (no-op if `canReject()` returns false)
- `recordView(): void` — records a `viewed` action if no view has been recorded within the configurable throttle window (`approval.file_view_throttle_minutes`, default 30 minutes)
- `sendNotification(): void` — records a `notified` action and dispatches `ExternalApprovalRequestSent` to trigger the email notification
- `hasBeenNotified(): bool` — `true` if any `notified` action exists for this approver on the request
- `hasViewed(): bool` — `true` if any `viewed` action exists for this approver on the request
- `hasApproved(): bool` — `true` if any `approved` or `staff-approved` action exists
- `hasRejected(): bool` — `true` if any `rejected` or `staff-rejected` action exists
- `hasViewedAllRequiredFiles(): bool` — checks that all files with `require_view = true` have been viewed by this approver
- `hasApprovedAllRequiredFiles(): bool` — checks that all files with `require_individual_approval = true` have been approved by this approver (returns `true` if no such files exist)
- `getFullName(): string` — trims and joins `first_name` and `last_name`
- `getDisplayName(): string` — full name, falling back to `email` if both name parts are empty
- `generateToken(): string` — generates a random 64-character string; called by the observer
- `getAccessUrl(): string` — returns the public portal URL (`external-approvals.show`) for this approver's token
- `isExternal(): bool` — `true` if approver is not staff (no linked User)
- `isStaff(): bool` — `true` if `related_model_type` is the User class
- `isAdhoc(): bool` — `true` if `related_model_type` is `null`
- `getNotifiedAt(): ?Carbon` — timestamp of the first `notified` action
- `getViewedAt(): ?Carbon` — timestamp of the first `viewed` action
- `getApprovedAt(): ?Carbon` — timestamp of the first `approved`/`staff-approved` action
- `getRejectedAt(): ?Carbon` — timestamp of the first `rejected`/`staff-rejected` action

## Common Usage

```php
// Approve a request as an approver (via portal token):
$approver = ExternalApprovalApprover::where('token', $token)->firstOrFail();
$approver->approve('Looks good to me.');

// Reject with a message:
$approver->reject('Address does not match our records.');

// Record a portal view (throttled):
$approver->recordView();

// Send the initial notification email:
$approver->sendNotification();

// Check gate before allowing action in the UI:
if ($approver->canApproveRequest()) {
    // show approve button
}

// Derived status for display:
$status = $approver->getStatus();         // 'approved', 'pending', etc.
$color  = $approver->getStatusColor();    // 'success', 'warning', etc.

// Full name or email fallback:
echo $approver->getDisplayName();         // 'Jane Smith' or 'jane@example.com'

// Portal access URL for the email link:
$url = $approver->getAccessUrl();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
