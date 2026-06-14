---
trait: HasApprovals
owning_module: Approval
source_paths:
  - modules/Approval/Traits/HasApprovals.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasApprovals

**Source:** `modules/Approval/Traits/HasApprovals.php`
**Registry entry:** [system/traits/index.md#hasapprovals](../../../system/traits/index.md#hasapprovals)

## Purpose

Adds an internal approval workflow to a model, backed by the polymorphic `ApprovalRequest` model. Models that need to go through an internal review-and-approve lifecycle use this trait. It provides relationship access to all approval requests, quick checks for active/inactive state, locking behavior (preventing edits while an active approval is pending, unless the user has `manageApprovals`), and a "quick approve" path for users with sufficient permissions.

## Contributed Columns

No columns are added to the using model's table. Approval request records live in the `approval_requests` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `approvalRequests()` | `MorphMany` | `Modules\Approval\Models\ApprovalRequest` | All approval request records for this model instance. |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `activeApprovalRequest()` | `(): ?ApprovalRequest` | Returns the first active approval request (using the `active()` scope on `ApprovalRequest`), or `null`. |
| `createApprovalRequest()` | `(): ApprovalRequest` | Creates a new approval request for this model. |
| `hasApprovals()` | `(): bool` | `true` if any approval request exists. |
| `hasNoApprovals()` | `(): bool` | Inverse of `hasApprovals()`. |
| `hasActiveApproval()` | `(): bool` | `true` if at least one active approval request exists. |
| `hasInactiveApprovals()` | `(): bool` | `true` if at least one inactive approval request exists. |
| `hasNoActiveApprovals()` | `(): bool` | Inverse of `hasActiveApproval()`. |
| `hasNoInactiveApprovals()` | `(): bool` | Inverse of `hasInactiveApprovals()`. |
| `isLockedByApproval()` | `(): bool` | `true` if an active approval with `is_record_locked = true` exists and the current user lacks the `manageApprovals` gate. |
| `canBeQuickApproved()` | `(): bool` | `true` if the model can be submitted for approval (`canBeSubmittedForApproval()`) AND the current user has both `update` and `manageApprovals` permissions. |
| `getQuickApproveActionName()` | `(): string` | Returns the display name for the quick-approve action (default: `'Approve & Post'`). Override per model. |

## Configuration / Contract

No interface required. The model should also implement `canBeSubmittedForApproval()` (which comes from `HasModificationRules` via `BaseModel`). The `ApprovalRequest` model and its table must exist. Laravel's `Gate` facade must be configured with a `manageApprovals` policy for the model.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasApprovals` across model docs, or `use HasApprovals` in Everspot source.
