---
model: Payment
module: Transaction
table: transactions
connection: tenant
source_paths:
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Models/Transaction.php
  - app/Models/BaseModel.php
  - modules/Common/Traits/HasModelNumbering.php
  - modules/Transaction/Scopes/TransactionByTypeScope.php
related: [Transaction, Refund]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-12
completeness: partial
deprecated: false
tags: [financial, transaction, core]
---

# Payment

**Primary source:** `modules/Transaction/Models/Payment.php`

## Overview

The Payment model represents customer payment transactions in the Everspot system. It extends the Transaction model and applies a global scope to filter only payment-type transactions from the shared transactions table. Payments are central to the financial operations of the cemetery management system, tracking all incoming payments from customers for services, products, and other obligations.

The Payment model uses Single Table Inheritance (STI) via the Transaction parent class, sharing the transactions table with other transaction types (charges, refunds, credits, etc.) while providing payment-specific behavior and relationships. Each payment can be reversed or refunded, supports multiple payment methods (cash, check, credit card, ACH), and integrates with the accounting system through journal entries.

Payments flow through multiple statuses (pending, processing, posted, failed, etc.) and can trigger events for successful completion, failure, or required user action. The model supports both manual payment entry and live payment processing through integrated payment gateways.

## Connection & Table

Tenant · `transactions`

## Schema

**Note:** Schema extraction pending - see schema/tenant.json blocker. The Payment model uses the `transactions` table with a type column set to 'payment' via global scope.

<!-- Schema will be rendered from schema/tenant.json when Phase 3 is complete -->

Expected key columns based on code analysis:
- `id` — Primary key
- `type` — Transaction type discriminator (set to 'payment' for this model)
- `status` — Payment status (pending, processing, posted, failed, etc.)
- `method` — Payment method (cash, check, credit-card, ach, other)
- `amt` — Total payment amount (money field)
- `principal_amt` — Principal portion of payment
- `fee_amt` — Fee portion of payment
- `interest_amt` — Interest portion of payment
- `date` — Payment date
- `model_no` — Auto-generated payment number
- `customer_id` — Foreign key to Customer
- `payment_method_id` — Foreign key to PaymentMethod
- `transactionable_type` — Polymorphic relation type
- `transactionable_id` — Polymorphic relation ID
- `postable_type` — Polymorphic posting target type
- `postable_id` — Polymorphic posting target ID
- `reversing_transaction_id` — Foreign key to Transaction (for reversals)
- `related_transaction_id` — Foreign key to related Transaction
- `deposit_batch_id` — Foreign key to DepositBatch
- `is_reversal` — Boolean flag for reversal transactions
- `created_at`, `updated_at` — Timestamps (with timezone casting)

## Properties / Casts

### Inherited from Transaction

**Money Attributes:**
- `moneyAttributes` = `['amt', 'principal_amt', 'fee_amt', 'interest_amt', 'basis_amt']` — Fields treated as money values via HasMoneyFields trait

**Casts:**
- `date` → `date`
- `is_reversal` → `boolean`
- `created_at` → `TimezonedDateTime` (timezone-aware datetime)
- `updated_at` → `TimezonedDateTime` (timezone-aware datetime)

**Searchable:**
- `searchableColumns` = `['model_no']` — Model number is searchable via HasSearch trait

**Protected:**
- `$guarded = []` — All fields are mass-assignable (use with caution)

## Relationships

### Defined in Payment
- `refunds()` — has many [Refund](./refund.md): all refunds issued against this payment, keyed by `reversing_transaction_id`

### Inherited from Transaction
- `transactionable()` — morph to (polymorphic): the parent entity this payment belongs to (Order, PaymentPlan, etc.)
- `postable()` — morph to (polymorphic): the entity this payment posts against
- `paymentMethod()` — belongs to [PaymentMethod](./payment-method.md): the payment method used (with trashed)
- `customer()` — belongs to Customer: the customer making the payment
- `depositBatch()` — belongs to [DepositBatch](./deposit-batch.md): the deposit batch containing this payment
- `reversingTransaction()` — belongs to [Transaction](./transaction.md): the transaction that reverses this payment (if reversed)
- `reversedByTransaction()` — has one [Transaction](./transaction.md): the reversal transaction created from this payment
- `relatedTransaction()` — belongs to [Transaction](./transaction.md): a related transaction
- `relatedTransactions()` — has many [Transaction](./transaction.md): transactions related to this one
- `processingFee()` — has one [Transaction](./transaction.md): processing fee transaction for this payment
- `journalEntries()` — has many JournalEntry: accounting entries for this payment

## Key Methods

### Payment-Specific Methods
None defined directly on Payment — inherits all functionality from Transaction.

### Inherited from Transaction

**Status Checks:**
- `isPosted(): bool` — Check if payment has posted status
- `canBeReversed(): bool` — Check if payment can be reversed (posted, not already reversed/reversing, type is 'payment')
- `canBeRefunded(): bool` — Check if payment can be refunded
- `isAutomaticRefundEligible(): bool` — Check if payment qualifies for automatic refund via payment processor
- `isLive(): bool` — Check if payment uses live payment method (credit-card or ach)
- `isReversedOrReversal(): bool` — Check if payment is a reversal or has been reversed

**Actions:**
- `post(): void` — Post the payment using appropriate posting strategy
- `reverse($withStatusChange = true): Transaction` — Create a reversal transaction for this payment
- `refund($withStatusChange = true): Refund` — Create a refund transaction for this payment
- `transactionUpdated(): void` — Notify parent entity (transactionable) of payment update

**Formatting:**
- `getFormattedTypeAttribute(): string` — Get human-readable payment type
- `getFormattedMethodAttribute(): ?string` — Get human-readable payment method
- `getFormattedRateAttribute(): ?string` — Get formatted interest rate percentage
- `getReceiptUrl(): ?string` — Get URL for payment receipt PDF
- `shouldBeNegative($field): bool` — Determine if a money field should display as negative

**Lifecycle Hooks:**
- `onPosted($oldStatus): void` — Fires PaymentSuccessful event when payment posts
- `onFailed(): void` — Fires PaymentFailed event on failure
- `onRequiresAction(): void` — Fires PaymentRequiresAction event when action needed

## Scopes / Events / Observers

### Global Scopes
- `TransactionByTypeScope('payment')` — Automatically filters all queries to only return transactions where `type = 'payment'`

### Query Scopes (Inherited)
- `active($query)` — Filter to active payments (status: processing or posted)
- `notReversed($query)` — Exclude reversed payments
- `notReversal($query)` — Exclude reversal payments
- `notReversedOrReversal($query)` — Exclude both reversed and reversal payments
- `ofType($query, string $type)` — Filter by transaction type
- `hideZeroDollarTransactions($query)` — Exclude zero-amount payments

### Events Dispatched
- `PaymentSuccessful` — Dispatched when payment transitions to 'posted' status from 'pending' (non-reversal only)
- `PaymentFailed` — Dispatched when payment enters 'failed' status
- `PaymentRequiresAction` — Dispatched when payment status becomes 'action-required'

### Model Events
- `created` — Auto-generates model_no via HasModelNumbering trait

## Common Usage

```php
// Create a new payment
$payment = Payment::create([
    'customer_id' => $customer->id,
    'transactionable_type' => Order::class,
    'transactionable_id' => $order->id,
    'payment_method_id' => $paymentMethod->id,
    'method' => 'credit-card',
    'amt' => 500.00,
    'date' => now(),
    'status' => 'pending',
]);

// Post a payment
$payment->post();

// Check if payment can be refunded
if ($payment->canBeRefunded()) {
    $refund = $payment->refund();
}

// Reverse a payment
if ($payment->canBeReversed()) {
    $reversal = $payment->reverse();
}

// Find all payments for a customer
$payments = Payment::where('customer_id', $customerId)
    ->active()
    ->notReversedOrReversal()
    ->get();

// Get payment with refunds
$payment = Payment::with('refunds')->find($id);

// Check payment status
if ($payment->isLive() && $payment->isAutomaticRefundEligible()) {
    // Can process automatic refund via payment gateway
}

// Access related entities
$customer = $payment->customer;
$paymentMethod = $payment->paymentMethod;
$order = $payment->transactionable; // polymorphic
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
