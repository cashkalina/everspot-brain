---
title: Cancellation Module
module: Cancellation
last_updated: 2026-06-14
---

# Cancellation Module

The Cancellation module records the reversal of prior sales, returning goods to inventory and voiding financial liability. Cancellations progress through a `pending → posted → voided` lifecycle and integrate with the approval workflow.

## Contents

- [Models](./models/index.md)
  - [Cancellation](./models/cancellation.md) — the cancellation header with financial totals
  - [CancellationLine](./models/cancellation-line.md) — individual item lines within a cancellation

## Key Concepts

- `Cancellation` stores totals (`sub_total`, `tax_total`, `total`) in **cents** — the `HasMoneyFields` trait provides transparent dollar conversion.
- `CancellationLine` also uses `HasMoneyFields` for `sale_price`, `tax`, and `total`.
- The `CancellationObserver` dispatches `CancellationSaved` on every save; `CancellationLineObserver` propagates events upward to the parent cancellation.
- Approval integration: `onApprovalRequestApproval()` runs `PostCancellation`; quick-approve label is `'Post Cancellation'`.
- `CancellationLine.is_property` distinguishes property reversals (plots, crypts) from merchandise/service reversals.
- Commission reversal is handled via the polymorphic `repAssociations()` relationship on `Cancellation`.
