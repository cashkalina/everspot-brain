---
model: ExternalApprovalAction
module: Approval
table: external_approval_actions
connection: tenant
primary_source: modules/Approval/Models/ExternalApprovalAction.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Approval/Models/ExternalApprovalApprover.php
  - modules/Approval/Models/ExternalApprovalRequest.php
  - modules/Approval/Models/ExternalApprovalFile.php
  - modules/Approval/Observers/ExternalApprovalActionObserver.php
  - modules/Approval/Providers/ApprovalServiceProvider.php
traits: []
related_models: [ExternalApprovalApprover, ExternalApprovalFile, ExternalApprovalRequest]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, integration]
---

# ExternalApprovalAction

## Overview

`ExternalApprovalAction` is the audit-trail record for every event that occurs within an external approval workflow. It is a **polymorphic** log: the `actionable` morphTo relationship can point to either an [ExternalApprovalRequest](./external-approval-request.md) (request-level events such as `created`, `notified`, `viewed`, `approved`, `rejected`, `staff-approved`, `staff-rejected`, `expired`, `cancelled`) or an [ExternalApprovalFile](./external-approval-file.md) (per-file events such as `viewed` and `approved`).

Actions are **insert-only** — the model declares `const UPDATED_AT = null` and sets `$timestamps = ['created_at']`, so no `updated_at` column exists. The `ExternalApprovalActionObserver` listens for `created` events: when a new action targets an `ExternalApprovalRequest` and is an approval or rejection, it triggers `checkAndUpdateStatus()` on that request to recalculate overall approval state.

The static `record()` factory method is the canonical way to create actions throughout the module; it captures IP address and user agent alongside the event data.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| actionable_type | varchar | No | - | Polymorphic type (ExternalApprovalRequest or ExternalApprovalFile class name) |
| actionable_id | bigint | No | - | Polymorphic ID of the actionable entity |
| action | enum | No | - | Action taken: `created`, `notified`, `viewed`, `approved`, `rejected`, `staff-approved`, `staff-rejected`, `expired`, `cancelled` |
| external_approval_approver_id | bigint | Yes | - | FK → external_approval_approvers: the approver who performed the action (null for system actions) |
| user_message | text | Yes | - | Optional message from the approver |
| ip_address | varchar | Yes | - | IP address of the actor at time of action |
| user_agent | text | Yes | - | User agent string of the actor |
| created_at | timestamp | Yes | - | Creation timestamp (no updated_at; insert-only) |

**Primary key:** `id`

**Foreign keys:** `external_approval_approver_id` → `external_approval_approvers.id`

**Indexes:** composite index `ext_appr_actions_actionable_idx` on (`actionable_type`, `actionable_id`); single-column indexes on `action`, `actionable_id`, `actionable_type`, `created_at`; FK-backing index on `external_approval_approver_id`.

**Note:** No `updated_at` column — `const UPDATED_AT = null`.

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants:**
```php
const ACTIONS = [
    'created'       => ['label' => 'Created',        'color' => 'secondary', 'icon' => 'plus'],
    'notified'      => ['label' => 'Notified',        'color' => 'info',      'icon' => 'envelope'],
    'viewed'        => ['label' => 'Viewed',           'color' => 'primary',   'icon' => 'eye'],
    'approved'      => ['label' => 'Approved',         'color' => 'success',   'icon' => 'check'],
    'rejected'      => ['label' => 'Rejected',         'color' => 'danger',    'icon' => 'times'],
    'staff-approved'=> ['label' => 'Staff Approved',   'color' => 'success',   'icon' => 'shield-check'],
    'staff-rejected'=> ['label' => 'Staff Rejected',   'color' => 'danger',    'icon' => 'shield-x'],
    'expired'       => ['label' => 'Expired',          'color' => 'warning',   'icon' => 'clock'],
    'cancelled'     => ['label' => 'Cancelled',        'color' => 'dark',      'icon' => 'x-circle'],
];
```

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `actionable()` — morphTo: the entity this action was performed on ([ExternalApprovalRequest](./external-approval-request.md) or [ExternalApprovalFile](./external-approval-file.md))
- `approver()` — belongs to [ExternalApprovalApprover](./external-approval-approver.md) (`external_approval_approver_id`): the approver who performed the action; `null` for system-generated actions

## Scopes

- `forRequest(Builder $query, ExternalApprovalRequest $request)` — filters to actions where `actionable` is the given request
- `forFile(Builder $query, ExternalApprovalFile $file)` — filters to actions where `actionable` is the given file
- `byApprover(Builder $query, ExternalApprovalApprover $approver)` — filters by `external_approval_approver_id`
- `ofType(Builder $query, string $action)` — filters by the `action` column value

## Events

_None defined on the model._

## Observers

- `ExternalApprovalActionObserver` — registered in `ApprovalServiceProvider::registerObservers()` (`ExternalApprovalAction::observe(ExternalApprovalActionObserver::class)`). Handles:
  - `created` — if the action targets an `ExternalApprovalRequest` and is an approval/rejection type (`approved`, `rejected`, `staff-approved`, `staff-rejected`), calls `$request->checkAndUpdateStatus()` to recalculate the overall request status

## Key Methods

- `record(Model $actionable, string $action, ?ExternalApprovalApprover $approver = null, ?string $userMessage = null): self` *(static)* — canonical factory; creates and persists an action, capturing IP and user agent from the current HTTP request
- `getActionLabel(): string` — human-readable label for the `action` value (from `ACTIONS` constant)
- `getActionColor(): string` — Bootstrap color class for the `action` value
- `getActionIcon(): string` — Bootstrap icon name for the `action` value
- `isSystemAction(): bool` — returns `true` for system-generated actions (`created`, `expired`, `cancelled`) that have no approver

## Common Usage

```php
// Create an action via the canonical static factory:
ExternalApprovalAction::record(
    $externalApprovalRequest,
    'notified',
    $approver,
    null
);

// Record a file view action:
ExternalApprovalAction::record($file, 'viewed', $approver);

// Scope to all actions on a specific request:
$actions = ExternalApprovalAction::forRequest($request)->get();

// Scope to actions by a specific approver:
$approverActions = ExternalApprovalAction::byApprover($approver)
    ->ofType('approved')
    ->get();

// Display helpers:
echo $action->getActionLabel();  // 'Approved'
echo $action->getActionColor();  // 'success'
echo $action->isSystemAction();  // false
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
