---
model: Transaction
module: Transaction
table: transactions
connection: tenant
sti: base
sti_subtypes: [Payment, Refund]
source_paths:
  - modules/Transaction/Models/Transaction.php
  - app/Models/BaseModel.php
  - modules/Common/Traits/HasExternalIds.php
  - modules/Common/Traits/HasIcon.php
  - modules/Common/Traits/HasModificationRules.php
  - modules/Common/Traits/HasByUserFields.php
  - modules/Common/Traits/HasModelNumbering.php
  - modules/Common/Traits/HasMoneyFields.php
  - modules/Common/Traits/HasSearch.php
  - modules/Common/Traits/HasSyncables.php
related: [PaymentMethod, Customer, DepositBatch, Refund]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-13
completeness: complete
deprecated: false
tags: [financial, transaction, core, sti-base]
---

# Transaction

**Primary source:** `modules/Transaction/Models/Transaction.php`

## Overview

The Transaction model is the base model for all financial transactions in the Everspot system. It uses Single Table Inheritance (STI) to represent different transaction types including payments, refunds, credits, charges, processing fees, financing transfers, cancellation credits, and interest transactions.

All transaction subtypes share the `transactions` table in the tenant database and are discriminated by the `type` column. The model provides comprehensive financial tracking with support for complex scenarios including reversals, refunds, posting to various account types, and integration with payment processors.

The model implements rich money handling through the `HasMoneyFields` trait, automatic model numbering for user-facing transaction IDs, and audit tracking through the `HasByUserFields` trait. It supports both manual transactions (cash, check) and live payment processor transactions (credit card, ACH).

## Connection & Table

Tenant · `transactions`

## Schema

<!-- Rendered from schema/tenant.json -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| transactionable_type | varchar | No | - | Polymorphic type for parent entity |
| transactionable_id | bigint | No | - | Polymorphic ID for parent entity |
| payment_method_id | bigint | Yes | - | Foreign key to payment_methods |
| customer_id | bigint | Yes | - | Foreign key to customers |
| model_no | varchar | Yes | - | User-facing transaction number |
| date | date | No | - | Transaction date |
| type | varchar | No | - | STI discriminator (payment, refund, credit, etc.) |
| status | varchar | No | - | Transaction status (pending, processing, posted, failed, etc.) |
| method | varchar | Yes | - | Payment method (cash, check, credit-card, ach, other) |
| amt | int | No | - | Total transaction amount in cents |
| principal_amt | int | No | - | Principal portion in cents |
| fee_amt | int | No | - | Fee portion in cents |
| interest_amt | int | No | - | Interest portion in cents |
| basis_amt | int | Yes | - | Basis amount for calculations in cents |
| rate | decimal | Yes | - | Interest or fee rate |
| memo | text | Yes | - | Transaction memo/notes |
| check_no | varchar | Yes | - | Check number for check payments |
| is_deposited | tinyint | No | 0 | Whether transaction is deposited |
| deposit_batch_id | bigint | Yes | - | Foreign key to deposit_batches |
| is_posted | tinyint | No | 0 | Whether transaction is posted to accounting |
| postable_type | varchar | Yes | - | Polymorphic type for posting target |
| postable_id | bigint | Yes | - | Polymorphic ID for posting target |
| is_reversal | tinyint | No | 0 | Whether this transaction reverses another |
| reversing_transaction_id | bigint | Yes | - | ID of transaction this reverses |
| related_transaction_id | bigint | Yes | - | ID of related transaction |
| created_by | bigint | Yes | - | User who created the transaction |
| updated_by | bigint | Yes | - | User who last updated the transaction |
| deleted_by | bigint | Yes | - | User who soft-deleted the transaction |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

## Properties / Casts

**Constants:**
```php
const TYPES = [
    'financing-transfer' => 'Financing Transfer',
    'processing-fee' => 'Processing Fee',
    'cancellation-credit' => 'Cancellation Credit',
    'charge' => 'Charge',
    'payment' => 'Payment',
    'refund' => 'Refund',
    'credit' => 'Credit',
    'interest' => 'Interest',
];

const STATUSES = [
    'pending' => ['label' => 'Pending', 'color' => 'warning'],
    'processing' => ['label' => 'Processing', 'color' => 'info'],
    'action-required' => ['label' => 'Action Required', 'color' => 'warning'],
    'posted' => ['label' => 'Posted', 'color' => 'success'],
    'failed' => ['label' => 'Failed', 'color' => 'danger'],
    'refunded' => ['label' => 'Refunded', 'color' => 'secondary'],
    'reversed' => ['label' => 'Reversed', 'color' => 'secondary'],
];

const METHODS = [
    'cash' => 'Cash',
    'check' => 'Check',
    'credit-card' => 'Credit Card',
    'ach' => 'ACH (Bank Account)',
    'other' => 'Other',
];

const liveMethods = ['credit-card', 'ach'];
```

**Money Attributes:**
- `moneyAttributes` = `['amt', 'principal_amt', 'fee_amt', 'interest_amt', 'basis_amt']`

**Casts:**
- `date` → `date`
- `is_reversal` → `boolean`
- `created_at` → `TimezonedDateTime::class`
- `updated_at` → `TimezonedDateTime::class`

**Searchable:**
- `searchableColumns` = `['model_no']`

**Guarded:**
- `[]` — All fields are mass-assignable

## Relationships

- `transactionable()` — MorphTo: The parent entity this transaction belongs to (e.g., Contract, Account)
- `postable()` — MorphTo: The accounting target where this transaction posts
- `paymentMethod()` — BelongsTo [PaymentMethod](./payment-method.md): The payment method used for this transaction (with trashed)
- `customer()` — BelongsTo [Customer](../../customer/models/customer.md): The customer associated with this transaction
- `depositBatch()` — BelongsTo [DepositBatch](./deposit-batch.md): The deposit batch this transaction is included in
- `reversingTransaction()` — BelongsTo Transaction: The transaction this one reverses
- `reversedByTransaction()` — HasOne Transaction: The reversal transaction for this transaction
- `relatedTransaction()` — BelongsTo Transaction: A related transaction (e.g., parent payment)
- `relatedTransactions()` — HasMany Transaction: Child related transactions
- `processingFee()` — HasOne Transaction: The processing fee transaction associated with this transaction
- `journalEntries()` — HasMany JournalEntry: Accounting journal entries for this transaction

## Key Methods

- `getModelFullTitle(): ?string` — Returns formatted transaction title with type and identifier
- `getModelFullTitleNoSuffix(): ?string` — Returns formatted transaction title without suffix
- `canBeReversed(): bool` — Checks if transaction can be reversed (posted, not already reversed, eligible type)
- `canBeRefunded(): bool` — Checks if transaction can be refunded (payments only, posted, not reversed)
- `isLive(): bool` — Returns true if transaction uses live payment processor (credit-card or ach)
- `isReversedOrReversal(): bool` — Checks if transaction is a reversal or has been reversed
- `isAutomaticRefundEligible(): bool` — Checks if can be automatically refunded via payment processor
- `reverse($withStatusChange = true): Transaction` — Creates a reversal transaction and optionally updates status
- `refund($withStatusChange = true): Refund` — Creates a refund transaction and optionally updates status
- `post(): void` — Posts transaction to accounting using appropriate posting strategy
- `transactionUpdated(): void` — Notifies parent entity of transaction update
- `getReceiptUrl(): ?string` — Returns URL for transaction receipt PDF
- `shouldBeNegative($field): bool` — Determines if a money field should be stored as negative
- `getFormattedTypeAttribute(): string` — Returns human-readable transaction type
- `getFormattedMethodAttribute(): ?string` — Returns human-readable payment method
- `getFormattedRateAttribute(): ?string` — Returns formatted interest/fee rate as percentage
- `onPosted($oldStatus): void` — Event handler when transaction is posted
- `onFailed(): void` — Event handler when transaction fails
- `onRequiresAction(): void` — Event handler when transaction requires action

## Scopes / Events / Observers

**Query Scopes:**
- `active($query)` — Filters to transactions with status 'processing' or 'posted'
- `notReversed($query)` — Excludes transactions that have been reversed
- `notReversal($query)` — Excludes reversal transactions (is_reversal = false)
- `notReversedOrReversal($query)` — Combines notReversed and notReversal
- `ofType($query, string $type)` — Filters to specific transaction type
- `hideZeroDollarTransactions($query)` — Excludes transactions with zero amount

**Events Dispatched:**
- `PaymentSuccessful` — When payment is successfully posted
- `PaymentFailed` — When payment processing fails
- `PaymentRequiresAction` — When payment requires user action
- `RefundFailed` — When refund processing fails
- `RefundRequiresAction` — When refund requires user action

## STI Subtypes

This model is the base for an STI hierarchy. Subtypes share this table and schema:
- [Payment](./payment.md) — `type=payment`
- [Refund](./refund.md) — `type=refund`

Other transaction types (credit, charge, processing-fee, etc.) use the base Transaction model directly without specific subclasses.

## Common Usage

```php
// Query all transactions
$transactions = Transaction::all();

// Query specific type using base model
$charges = Transaction::ofType('charge')->get();

// Query using subtype model (automatically scoped)
$payments = Payment::all(); // WHERE type = 'payment'

// Create a charge transaction
$charge = Transaction::create([
    'type' => 'charge',
    'transactionable_type' => Contract::class,
    'transactionable_id' => $contract->id,
    'customer_id' => $customer->id,
    'date' => now(),
    'status' => 'pending',
    'amt' => 10000, // $100.00 in cents
    'principal_amt' => 10000,
]);

// Post transaction to accounting
$transaction->post();

// Reverse a transaction
if ($transaction->canBeReversed()) {
    $reversal = $transaction->reverse();
}

// Refund a payment
if ($payment->canBeRefunded()) {
    $refund = $payment->refund();
}

// Check transaction status
if ($transaction->isReversedOrReversal()) {
    // Handle reversed transaction
}

// Get formatted display values
echo $transaction->formatted_type; // "Payment"
echo $transaction->formatted_method; // "Credit Card"
echo $transaction->formatted_rate; // "5.50%"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
