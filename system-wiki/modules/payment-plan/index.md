---
title: PaymentPlan Module
module: PaymentPlan
last_updated: 2026-06-14
---

# PaymentPlan Module

The PaymentPlan module manages installment financing arrangements that allow cemetery customers to pay for goods and services over time. It handles the full plan lifecycle from creation through activation, payment processing, restructuring, and payoff or cancellation.

## Models

See [models/index.md](./models/index.md) for the full model list.

| Model | Table | Description |
|-------|-------|-------------|
| [PaymentPlan](./models/payment-plan.md) | `payment_plans` | Installment financing plan |
| [PaymentPlanRestructure](./models/payment-plan-restructure.md) | `payment_plan_restructures` | Restructuring event audit record |

## Key Concepts

- **Status lifecycle** — Plans flow through: `pending` → `active` → (`pending-payoff` | `canceled` | `paid-in-full`). Transitions are driven by action classes (`ActivatePaymentPlan`, `InactivatePaymentPlan`) and lifecycle methods (`onPendingPayoff()`, `onActive()`, `onPaidInFull()`).
- **Money storage** — All balance and amount columns are stored as integer cents. [HasMoneyFields](../../system/traits/index.md#hasmoneyfields) provides transparent conversion to dollars for application code.
- **Balance maintenance** — Running balances are updated by `UpdatePaymentPlanBalances` (called via `transactionUpdated()`) and due-tracking by `UpdatePaymentPlanDueTracking` (called by the observer on `created` and by daily maintenance commands).
- **Daily maintenance** — Artisan commands registered in `PaymentPlanServiceProvider` handle interest accrual, late fees, past-due tracking, amount-due calculation, and autopay processing as scheduled tasks.
- **Restructuring** — When plan terms change, the old and new terms are snapshotted in a [PaymentPlanRestructure](./models/payment-plan-restructure.md) record. The plan's `restructured_date` is updated and balance calculations are scoped accordingly.
- **Autopay** — Plans can have one or more [Autopay](../autopay/models/autopay.md) records (morphMany via `autopayable`). The match-autopay pattern (`createMatchAutopay()`) keeps the autopay amount synchronized with the plan's regular payment.
