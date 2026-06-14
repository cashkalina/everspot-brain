---
title: Transaction Module — Models
purpose: Index of all documented models in the Transaction module
last_updated: 2026-06-14
---

# Transaction Module — Models

This directory contains documentation for all 6 concrete Eloquent models in the Transaction module. Three models form an STI hierarchy sharing the `transactions` table; three are independent models on their own tables.

## STI Hierarchy — `transactions` table

| Model | Role | Discriminator | Doc |
|-------|------|---------------|-----|
| [Transaction](./transaction.md) | STI base | _(all types)_ | Complete |
| [Payment](./payment.md) | STI subtype | `type=payment` | Complete |
| [Refund](./refund.md) | STI subtype | `type=refund` | Complete |

**Note:** The `type` column also stores `charge`, `credit`, `interest`, `processing-fee`, `cancellation-credit`, and `financing-transfer` values, which use the base `Transaction` class directly (no dedicated subtype model).

## Independent Models

| Model | Table | Doc |
|-------|-------|-----|
| [DepositBatch](./deposit-batch.md) | `deposit_batches` | Complete |
| [PaymentMethod](./payment-method.md) | `payment_methods` | Complete |
| [PaymentMethodRequest](./payment-method-request.md) | `payment_method_requests` | Complete |

## Observer Registry

All observers are registered in `modules/Transaction/Providers/TransactionServiceProvider::registerObservers()`:

| Model | Observer | Key behavior |
|-------|----------|-------------|
| Transaction | `TransactionObserver` | `saved`/`deleted`/`restored`/`forceDeleted` → `transactionUpdated()` |
| Payment | `PaymentObserver` | `saved`/`deleted`/`restored`/`forceDeleted` → `transactionUpdated()` |
| Refund | `RefundObserver` | `saved`/`deleted`/`restored`/`forceDeleted` → `transactionUpdated()` |
| PaymentMethod | `PaymentMethodObserver` | `deleting` → `PreDeletePaymentMethod` action |
| PaymentMethodRequest | `PaymentMethodRequestObserver` | `creating` → sets token, expires_at, success_url |
| DepositBatch | _(none)_ | — |

## Traits Used

| Trait | Models |
|-------|--------|
| [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) | Transaction, DepositBatch, PaymentMethod, PaymentMethodRequest |
| [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) | Transaction, Payment, Refund |
| [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) | Transaction, DepositBatch |
| [HasSearch](../../../system/traits/index.md#hassearch) | Transaction |
| [HasSyncables](../../../system/traits/index.md#hassyncables) | Transaction, PaymentMethod, PaymentMethodRequest |
| [SoftDeletes](../../../system/traits/index.md#softdeletes) | PaymentMethod |
