---
title: Order Module
module: Order
last_updated: 2026-06-14
---

# Order Module

The Order module manages sales contracts between the cemetery and customers. An order captures what was sold (via line items), the total financial amounts, the payment arrangement (down payment and/or payment plan), and an approval workflow for posting the contract to accounting.

## Contents

- [Models](./models/index.md) — `Order`, `OrderLine`

## Key Concepts

- **Orders** move through `pending` → `posted` (or `voided`). Posting is gated by the approval workflow and requires a full payment arrangement and valid G/L accounts.
- **OrderLines** record what was purchased (via a polymorphic `purchasable` relationship) and generate `LiabilityLine` records for fulfillment tracking.
- Money amounts are stored as integer cents and exposed as dollars via the `HasMoneyFields` trait.
