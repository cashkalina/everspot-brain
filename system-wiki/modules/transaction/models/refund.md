---
model: Refund
module: Transaction
table: transactions
connection: tenant
sti: subtype
sti_base: Transaction
sti_discriminator: type=refund
primary_source: modules/Transaction/Models/Refund.php
source_paths:
  - modules/Transaction/Models/Transaction.php
  - modules/Transaction/Observers/RefundObserver.php
  - modules/Transaction/Providers/TransactionServiceProvider.php
traits:
  - HasModelNumbering
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction]
---

# Refund

## Overview

Refund is the STI subtype for refund transactions — money returned to a customer after a payment has been made. It extends [Transaction](./transaction.md) and shares the `transactions` table, automatically scoped to rows where `type = 'refund'` via a global `TransactionByTypeScope`.

A Refund is always created in relation to an existing [Payment](./payment.md): the `reversing_transaction_id` on the Refund points to the Payment being refunded. Refunds can be issued manually or automatically when the payment method supports it (`isAutomaticRefundEligible()` on the source payment). The refund creation flow is initiated via `Transaction::refund()` on the Payment, which calls the transactionable's `createRefund()` method.

The `RefundObserver` mirrors the Payment observer pattern, calling `transactionUpdated()` on save/delete/restore to keep the owning transactionable synchronized. Like Payment, Refund re-declares [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) to enable refund-specific `model_no` generation.

## Schema

**See [Transaction](./transaction.md) for the full shared-table schema.** (Subtypes do not render the schema table.)

## STI Details

- **Base model:** [Transaction](./transaction.md)
- **Discriminator:** `type=refund`
- **Global scope:** `TransactionByTypeScope('refund')` — automatically applies `WHERE type = 'refund'` to all queries
- **Boot method:** adds the global scope via `static::addGlobalScope(new TransactionByTypeScope('refund'))`

## Casts

Inherits all casts from [Transaction](./transaction.md). No Refund-specific casts.

## Attributes

**Guarded:** `[]` — all fields are mass-assignable (inherited from Transaction)

No Refund-specific `$fillable`, `$hidden`, `$visible`, or `$appends` beyond the base.

## Accessors & Mutators

_None beyond base Transaction._

## Traits

- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates refund-specific user-facing `model_no` values (re-declared on the subtype to enable refund-specific numbering configuration)

## Relationships

**Inherited from [Transaction](./transaction.md):**
- `transactionable()` — morphTo: the parent entity (Order, PaymentPlan, etc.)
- `postable()` — morphTo: the entity that triggered posting
- `paymentMethod()` — belongs to [PaymentMethod](./payment-method.md): the payment method used for the original payment
- `customer()` — belongs to [Customer](../../customer/models/customer.md): the customer being refunded
- `depositBatch()` — belongs to [DepositBatch](./deposit-batch.md): the deposit batch (if applicable)
- `reversingTransaction()` — belongs to [Transaction](./transaction.md) (`reversing_transaction_id`): the original Payment that this Refund was issued against
- `reversedByTransaction()` — has one [Transaction](./transaction.md): a further reversal of this Refund (if any)
- `relatedTransaction()` — belongs to [Transaction](./transaction.md): related transaction
- `relatedTransactions()` — has many [Transaction](./transaction.md): child related transactions
- `processingFee()` — has one [Transaction](./transaction.md) (`type=processing-fee`): associated processing fee
- `journalEntries()` — has many JournalEntry: accounting ledger entries

No Refund-specific relationships.

## Scopes

**Global scope (auto-applied):** `TransactionByTypeScope('refund')` — all queries automatically include `WHERE type = 'refund'`.

Inherits all query scopes from [Transaction](./transaction.md): `active()`, `notReversed()`, `notReversal()`, `notReversedOrReversal()`, `ofType()`, `hideZeroDollarTransactions()`.

## Events

- `RefundFailed` — dispatched when this Refund fails (in `Transaction::onFailed()`)
- `RefundRequiresAction` — dispatched when user action is needed (in `Transaction::onRequiresAction()`)

## Observers

- `RefundObserver` — registered in `TransactionServiceProvider::registerObservers()` (`Refund::observe(RefundObserver::class)`). Handles:
  - `saved` — calls `$refund->transactionUpdated()` to notify the transactionable parent
  - `deleted` — calls `$refund->transactionUpdated()`
  - `restored` — calls `$refund->transactionUpdated()`
  - `forceDeleted` — calls `$refund->transactionUpdated()`
  - `creating`, `created`, `updated` — no-op stubs

## Key Methods

Inherits all key methods from [Transaction](./transaction.md), including `post()`, `isLive()`, `transactionUpdated()`.

No Refund-specific public methods beyond the base.

## Common Usage

```php
// All refunds for a customer (automatically scoped to type=refund)
$refunds = Refund::where('customer_id', $customer->id)->get();

// Get the original payment that was refunded
$originalPayment = $refund->reversingTransaction; // a Transaction (or cast as Payment)

// Get all refunds for a payment (accessed via Payment's relationship)
$allRefunds = $payment->refunds;

// Post a refund to the accounting ledger
$refund->post();

// Posted refunds only
$postedRefunds = Refund::active()->get();

// Exclude refunds that were themselves reversed
$validRefunds = Refund::notReversed()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
