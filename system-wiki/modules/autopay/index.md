---
title: Autopay Module
purpose: Overview of the Autopay module and its documentation
last_updated: 2026-06-14
---

# Autopay Module

The Autopay module manages recurring automatic-payment configurations for customers. Autopays are attached to a polymorphic parent entity (typically a `PaymentPlan`) and charge a customer's payment method on a defined frequency (weekly through annually). The module includes console commands for processing due autopays and inactivating expired ones.

## Models

- [Autopay](./models/autopay.md) — a recurring payment schedule, with frequency-based date advancement and processing-fee calculation.

## Module-owned traits

_None._

## Related modules

- [Customer](../customer/index.md) — the customer being charged
- [Transaction](../transaction/index.md) — `PaymentMethod` used for charging; `Payment` produced by `process()`
- [PaymentPlan](../payment-plan/index.md) — the typical `autopayable` parent entity
