---
model: Payment
module: Transaction
table: transactions
connection: tenant
sti: subtype
sti_base: Transaction
sti_discriminator: type=payment
primary_source: modules/Transaction/Models/Payment.php
source_paths:
  - modules/Transaction/Models/Transaction.php
  - modules/Transaction/Observers/PaymentObserver.php
  - modules/Transaction/Providers/TransactionServiceProvider.php
  - modules/Transaction/Models/Refund.php
traits:
  - HasModelNumbering
related_models: [Refund]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction, payment]
---

# Payment

## Overview

Payment is the STI subtype for customer payment transactions. It extends [Transaction](./transaction.md) and shares the `transactions` table, automatically scoped to rows where `type = 'payment'` via a global `TransactionByTypeScope`. Every Payment is a concrete financial event where a customer renders money — by cash, check, credit card, or ACH.

Payment adds one subtype-specific relationship: `refunds()`, which exposes all [Refund](./refund.md) records linked to this payment via `reversing_transaction_id`. This makes it straightforward to enumerate all refunds issued against a given payment. The `refund()` method (defined on the base Transaction) creates a new Refund and transitions the Payment to `refunded` status.

The `PaymentObserver` handles the `saved`/`deleted`/`restored`/`forceDeleted` lifecycle events for Payment records, calling `transactionUpdated()` to propagate changes to the owning transactionable entity (e.g. an Order or PaymentPlan). Payment also uses `HasModelNumbering` to generate payment-specific `model_no` values.

## Schema

**See [Transaction](./transaction.md) for the full shared-table schema.** (Subtypes do not render the schema table.)

## STI Details

- **Base model:** [Transaction](./transaction.md)
- **Discriminator:** `type=payment`
- **Global scope:** `TransactionByTypeScope('payment')` — automatically applies `WHERE type = 'payment'` to all queries
- **Boot method:** adds the global scope via `static::addGlobalScope(new TransactionByTypeScope('payment'))`

## Casts

Inherits all casts from [Transaction](./transaction.md). No Payment-specific casts.

## Attributes

**Guarded:** `[]` — all fields are mass-assignable (inherited from Transaction)

No Payment-specific `$fillable`, `$hidden`, `$visible`, or `$appends` beyond the base.

## Accessors & Mutators

_None beyond base Transaction._

## Traits

- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates payment-specific user-facing `model_no` values (re-declared on the subtype to enable payment-specific numbering configuration)

## Relationships

**Inherited from [Transaction](./transaction.md):**
- `transactionable()` — morphTo: the parent entity (Order, PaymentPlan, etc.)
- `postable()` — morphTo: the entity that triggered posting
- `paymentMethod()` — belongs to [PaymentMethod](./payment-method.md): the stored payment method used
- `customer()` — belongs to [Customer](../../customer/models/customer.md): the paying customer
- `depositBatch()` — belongs to [DepositBatch](./deposit-batch.md): the deposit batch (if applicable)
- `reversingTransaction()` — belongs to [Transaction](./transaction.md): the transaction this one reversed
- `reversedByTransaction()` — has one [Transaction](./transaction.md): the reversal created for this one
- `relatedTransaction()` — belongs to [Transaction](./transaction.md): related transaction (e.g. processing fee link)
- `relatedTransactions()` — has many [Transaction](./transaction.md): child related transactions
- `processingFee()` — has one [Transaction](./transaction.md) (`type=processing-fee`): the associated processing fee
- `journalEntries()` — has many JournalEntry: accounting ledger entries

**Payment-specific:**
- `refunds()` — has many [Refund](./refund.md) (`reversing_transaction_id`): all refunds issued against this payment

## Scopes

**Global scope (auto-applied):** `TransactionByTypeScope('payment')` — all queries automatically include `WHERE type = 'payment'`.

Inherits all query scopes from [Transaction](./transaction.md): `active()`, `notReversed()`, `notReversal()`, `notReversedOrReversal()`, `ofType()`, `hideZeroDollarTransactions()`.

## Events

- `PaymentSuccessful` — dispatched when this Payment transitions from `pending` to `posted` (in `Transaction::onPosted()`)
- `PaymentFailed` — dispatched when this Payment fails (in `Transaction::onFailed()`)
- `PaymentRequiresAction` — dispatched when user action is needed (in `Transaction::onRequiresAction()`)

## Observers

- `PaymentObserver` — registered in `TransactionServiceProvider::registerObservers()` (`Payment::observe(PaymentObserver::class)`). Handles:
  - `saved` — calls `$payment->transactionUpdated()` to notify the transactionable parent
  - `deleted` — calls `$payment->transactionUpdated()`
  - `restored` — calls `$payment->transactionUpdated()`
  - `forceDeleted` — calls `$payment->transactionUpdated()`
  - `creating`, `created`, `updated` — no-op stubs

## Key Methods

Inherits all key methods from [Transaction](./transaction.md), including `post()`, `reverse()`, `refund()`, `canBeReversed()`, `canBeRefunded()`, `isLive()`, `isAutomaticRefundEligible()`.

No Payment-specific public methods beyond the base.

## Common Usage

```php
// All payments for a customer (automatically scoped to type=payment)
$payments = Payment::where('customer_id', $customer->id)->get();

// Most recent posted payment
$latest = Payment::active()->where('customer_id', $customer->id)
    ->orderBy('date', 'desc')->first();

// Get all refunds for a payment
$refunds = $payment->refunds;

// Create a refund (returns a Refund instance, transitions payment to 'refunded')
$refund = $payment->refund();

// Create a refund without status transition
$refund = $payment->refund(withStatusChange: false);

// Post a payment to the accounting ledger
$payment->post();

// Check if a live payment can be auto-refunded
if ($payment->isAutomaticRefundEligible()) {
    $payment->refund();
}

// Reverse a payment (creates a reversal transaction)
$reversal = $payment->reverse();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
