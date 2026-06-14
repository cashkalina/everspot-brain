---
title: Trust Module — Model Index
module: Trust
last_updated: 2026-06-14
---

# Trust Module — Models

This directory contains documentation for all concrete Eloquent models in the Trust module (`modules/Trust/Models/`). The Trust module manages pre-need trust fund accounting — tracking per-contract obligations, approval workflows, and posted transactions against cemetery trust accounts.

## Models

| Model | Table | Description |
|-------|-------|-------------|
| [TrustAccount](./trust-account.md) | `trust_accounts` | Cemetery trust fund account (merch or perpetual care) |
| [TrustAccountTransaction](./trust-account-transaction.md) | `trust_account_transactions` | Posted transaction batch against a trust account |
| [TrustAccountTransactionApplication](./trust-account-transaction-application.md) | `trust_account_transaction_applications` | Links one transaction against another (net-application accounting) |
| [TrustApplicationStrategy](./trust-application-strategy.md) | `trust_application_strategies` | Configuration strategy for how trust funds are spread and weighted during application |
| [TrustApproval](./trust-approval.md) | `trust_approvals` | Pending or processed approval record staging element batches for posting |
| [TrustArrangement](./trust-arrangement.md) | `trust_arrangements` | Per-contract trust obligation linking an arrangeable entity to a trust account |
| [TrustElement](./trust-element.md) | `trust_elements` | Atomic deposit/withdrawal line item in the trust processing pipeline |
| [TrustTransactionType](./trust-transaction-type.md) | `trust_transaction_types` | Configurable transaction type with field configs and application strategies |
| [TrustingSchedule](./trusting-schedule.md) | `trusting_schedules` | Rules for computing the trust obligation amount for a product/service |
| [TrustingScheduleGroup](./trusting-schedule-group.md) | `trusting_schedule_groups` | Organizational container grouping related trusting schedules |

## Key Relationships

The Trust module data model forms a clear hierarchy:

```
TrustingScheduleGroup
  └── TrustingSchedule ─── TrustAccount (where funds are collected)
                               │
                         TrustArrangement (per-contract, polymorphic parent)
                               │
                         TrustElement (atomic deposit/withdrawal triggers)
                               │
                         TrustApproval (staging batch for posting)
                               │
                         TrustAccountTransaction (posted ledger entry)
                               │
                         TrustAccountTransactionApplication (cross-transaction netting)
```

`TrustTransactionType` and `TrustApplicationStrategy` are configuration records that govern how transactions are classified and how amounts are distributed.

## Module Traits

The Trust module owns the `HasTrusting` trait, which enables other models to participate as trust arrangeables. See the [trait registry](../../../system/traits/index.md#hastrusting) and the [trait deep doc](../traits/has-trusting.md).
