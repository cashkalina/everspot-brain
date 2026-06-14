---
title: Delivery Module
module: Delivery
last_updated: 2026-06-14
---

# Delivery Module

The Delivery module tracks the transfer of goods from inventory to their destination — either directly to a customer or into constructive/storage receipt. Deliveries progress through a `pending → posted → voided` lifecycle and integrate with the approval workflow.

## Contents

- [Models](./models/index.md)
  - [Delivery](./models/delivery.md) — the delivery header record
  - [DeliveryLine](./models/delivery-line.md) — individual item lines within a delivery

## Key Concepts

- A `Delivery` is either direct-to-customer (`is_constructive = false`) or to storage (`is_constructive = true`).
- `DeliveryLine` records link to `LiabilityLine` items — the specific goods being delivered.
- The `DeliveryLineObserver` calls `liabilityLine->updatedDelivery()` on every save/delete/restore to keep liability tracking in sync.
- The `DeliveryObserver` runs `PreDeleteDelivery` in a transaction on delete.
- Approval integration: `onApprovalRequestApproval()` posts the delivery; quick-approve label is `'Post Delivery'`.
