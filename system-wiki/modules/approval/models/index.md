---
title: Approval Module — Models
purpose: Index of model documentation for the Approval module
last_updated: 2026-06-14
---

# Approval Module — Models

Model documentation for `modules/Approval/Models/`. All 6 models use the **tenant** database connection.

## Internal Approval Workflow

| Model | Table | Description |
|-------|-------|-------------|
| [ApprovalRequest](./approval-request.md) | `approval_requests` | Central record for internal approval workflows; polymorphic pivot on any approvable entity |
| [ApprovalAction](./approval-action.md) | `approval_actions` | Immutable audit-trail event (submittal, approval, rejection, deletion) within an internal approval request |

## External Approval Workflow

| Model | Table | Description |
|-------|-------|-------------|
| [ExternalApprovalRequest](./external-approval-request.md) | `external_approval_requests` | Top-level record for sending documents to external parties for sign-off; polymorphic on any approvable entity |
| [ExternalApprovalApprover](./external-approval-approver.md) | `external_approval_approvers` | A recipient (external, staff, or ad-hoc) assigned to an external approval request, identified by a unique token |
| [ExternalApprovalFile](./external-approval-file.md) | `external_approval_files` | A document attached to an external approval request for review |
| [ExternalApprovalAction](./external-approval-action.md) | `external_approval_actions` | Polymorphic audit-trail event on an external request or file (view, approval, rejection, etc.) |

## Traits

Module-owned traits that enable these workflows on other models:

| Trait | Registry | Description |
|-------|----------|-------------|
| HasApprovals | [#hasapprovals](../../../system/traits/index.md#hasapprovals) | Internal approval workflow on any model |
| HasExternalApprovals | [#hasexternalapprovals](../../../system/traits/index.md#hasexternalapprovals) | External approval workflow on any model |

See [Approval Module Traits](../traits/index.md) for trait deep docs.
