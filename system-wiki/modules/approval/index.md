---
title: Approval Module
purpose: Overview of the Approval module and its documentation
last_updated: 2026-06-14
---

# Approval Module

The Approval module provides two parallel approval workflows for Everspot:

1. **Internal approval** — staff-to-staff workflow where records are submitted, approved, or rejected by Everspot users. Any model can participate via the `HasApprovals` trait.

2. **External approval** — document-review workflow where staff send files to external parties (customers, attorneys, family members) or internal staff via a public portal. Any model can participate via the `HasExternalApprovals` trait.

Both workflows are polymorphic: the approval record is linked to the "approvable" entity (e.g., an order, contract, or interment record) through a `morphTo` relationship.

## Contents

| Directory | Contents |
|-----------|----------|
| [models/](./models/index.md) | 6 model docs (ApprovalRequest, ApprovalAction, ExternalApprovalRequest, ExternalApprovalApprover, ExternalApprovalFile, ExternalApprovalAction) |
| [traits/](./traits/index.md) | 2 trait docs (HasApprovals, HasExternalApprovals) |

## Source location

`modules/Approval/` in the Everspot repository.
