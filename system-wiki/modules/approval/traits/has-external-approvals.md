---
trait: HasExternalApprovals
owning_module: Approval
source_paths:
  - modules/Approval/Traits/HasExternalApprovals.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasExternalApprovals

**Source:** `modules/Approval/Traits/HasExternalApprovals.php`
**Registry entry:** [system/traits/index.md#hasexternalapprovals](../../../system/traits/index.md#hasexternalapprovals)

## Purpose

Adds an external approval workflow to a model, distinct from the internal `HasApprovals` trait. External approvals involve outside parties (e.g. beneficiaries, family members) approving a record via an external link or portal. Backed by the polymorphic `ExternalApprovalRequest` model.

Provides relationship access to approval requests, status checks, access to available approval type options (from `ListOption`), configuration resolution via `ExternalApprovalConfigFactory`, and helpers for retrieving approvers from named relationships.

## Contributed Columns

No columns are added to the using model's table. External approval request records live in the `external_approval_requests` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `externalApprovalRequests()` | `MorphMany` | `Modules\Approval\Models\ExternalApprovalRequest` | All external approval request records for this model. |

## Contributed Scopes

None (scopes like `active()` and `pending()` are on `ExternalApprovalRequest` itself).

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `activeExternalApprovalRequests()` | `(): Builder` | Approval requests scoped to `active()`. |
| `pendingExternalApprovalRequests()` | `(): Builder` | Approval requests scoped to `pending()`. |
| `hasExternalApprovals()` | `(): bool` | `true` if `$this->externalApprovalRequests` (eager-loaded collection) is non-empty. Requires the relation to have been loaded via `LoadExternalApprovalData`. |
| `hasPendingExternalApprovals()` | `(): bool` | `true` if `pendingExternalApprovalRequests()->count() > 0`. |
| `getAvailableExternalApprovalTypes()` | `(): Collection` | Returns `ListOption` rows for `external_approval_type_<model_snake_case>` type; empty Collection if the type is not registered. |
| `getExternalApprovalConfig()` | `(?ListOption $approvalType = null): BaseExternalApprovalConfig` | Resolves and returns the configuration for this model and optional approval type via `ExternalApprovalConfigFactory`. |
| `getApproversFromRelation()` | `(string $relationName): Collection` | Returns a Collection of models from the named relationship (handles both single model and collection results). Returns empty Collection if the relation does not exist. |

## Configuration / Contract

No interface required on the model. The `ExternalApprovalRequest` model and its table must exist. Approval types are registered via `ListOption` rows (type `external_approval_type_<model_key>`). Configuration classes must be resolvable by `ExternalApprovalConfigFactory` for the model class.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasExternalApprovals` across model docs, or `use HasExternalApprovals` in Everspot source.
