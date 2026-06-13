---
model: Payment
module: Transaction
table: transactions
connection: tenant
sti: subtype
sti_base: Transaction
sti_discriminator: type=payment
source_paths:
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Models/Transaction.php
  - app/Models/BaseModel.php
  - modules/Common/Traits/HasByUserFields.php
  - modules/Common/Traits/HasModelNumbering.php
  - modules/Common/Traits/HasMoneyFields.php
  - modules/Common/Traits/HasSearch.php
  - modules/Common/Traits/HasSyncables.php
related: [Transaction, Refund, Customer, PaymentMethod]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-13
completeness: complete
deprecated: false
tags: [financial, payment, transaction, sti-subtype]
---

# Payment

**Primary source:** `modules/Transaction/Models/Payment.php`

## Overview

The Payment model represents customer payment transactions in the Everspot system. It is a specialized subtype of the Transaction model using Single Table Inheritance (STI), sharing the `transactions` table with other transaction types.

Payments are automatically scoped to records where `type = 'payment'` through a global scope. This model extends the base Transaction functionality with payment-specific behavior including refund creation, payment processor integration, and payment-specific event handling.

The model supports various payment methods including cash, check, credit card, and ACH. Live payment methods (credit card, ACH) integrate with payment processors for real-time processing, while manual methods (cash, check) are recorded for offline processing.

## Connection & Table

Tenant · `transactions` (shared via STI)

**See [Transaction](./transaction.md) for full schema.**

## STI Details

- **Base model:** [Transaction](./transaction.md)
- **Discriminator:** `type=payment`
- **Global scope:** Automatically filters to `WHERE type = 'payment'`
- **Boot behavior:** Sets `type` attribute to `'payment'` on new instances

## Properties / Casts

Inherits all properties and casts from [Transaction](./transaction.md):
- Money attributes for financial calculations
- Date casting for transaction dates
- Timezone-aware timestamp handling
- Model numbering for user-facing payment IDs

**Guarded:**
- `[]` — All fields are mass-assignable

**Definition Class:**
- `$definitionClass` = `\Modules\Transaction\Definitions\Payment::class`

## Relationships

**Inherited from Transaction:**
- `transactionable()` — MorphTo: The parent entity this payment belongs to (e.g., Contract, Account)
- `postable()` — MorphTo: The accounting target where this payment posts
- `paymentMethod()` — BelongsTo [PaymentMethod](./payment-method.md): The payment method used
- `customer()` — BelongsTo [Customer](../../customer/models/customer.md): The customer making the payment
- `depositBatch()` — BelongsTo [DepositBatch](./deposit-batch.md): The deposit batch this payment is included in
- `reversingTransaction()` — BelongsTo [Transaction](./transaction.md): The transaction this payment reverses
- `reversedByTransaction()` — HasOne [Transaction](./transaction.md): The reversal transaction for this payment
- `relatedTransaction()` — BelongsTo [Transaction](./transaction.md): A related transaction
- `relatedTransactions()` — HasMany [Transaction](./transaction.md): Child related transactions
- `processingFee()` — HasOne [Transaction](./transaction.md): The processing fee associated with this payment
- `journalEntries()` — HasMany JournalEntry: Accounting journal entries

**Payment-specific:**
- `refunds()` — HasMany [Refund](./refund.md): Refund transactions created from this payment

## Key Methods

**Inherited from Transaction:**
- `post(): void` — Posts payment to accounting
- `reverse($withStatusChange = true): Transaction` — Creates a reversal transaction
- `refund($withStatusChange = true): Refund` — Creates a refund for this payment
- `canBeRefunded(): bool` — Checks if payment can be refunded
- `isLive(): bool` — Returns true if using live payment processor
- `isAutomaticRefundEligible(): bool` — Checks if can be automatically refunded
- `getReceiptUrl(): ?string` — Returns URL for payment receipt PDF
- `getFormattedTypeAttribute(): string` — Returns "Payment"
- `getFormattedMethodAttribute(): ?string` — Returns formatted payment method name

See [Transaction](./transaction.md) for complete inherited method documentation.

## Scopes / Events / Observers

**Global Scope:**
- `TransactionByTypeScope('payment')` — Automatically applies `WHERE type = 'payment'` to all queries

**Inherited Scopes:**
- `active($query)` — Payments with status 'processing' or 'posted'
- `notReversed($query)` — Excludes reversed payments
- `notReversal($query)` — Excludes reversal payments
- `hideZeroDollarTransactions($query)` — Excludes zero-amount payments

**Events Dispatched:**
- `PaymentSuccessful` — When payment is successfully posted (status changes from 'pending' to 'posted')
- `PaymentFailed` — When payment processing fails
- `PaymentRequiresAction` — When payment requires user action (e.g., 3D Secure)

**Boot Method:**
Sets `type` to `'payment'` automatically when creating new Payment instances.

## Common Usage

```php
// Create a payment
$payment = Payment::create([
    'transactionable_type' => Contract::class,
    'transactionable_id' => $contract->id,
    'customer_id' => $customer->id,
    'payment_method_id' => $paymentMethod->id,
    'date' => now(),
    'status' => 'pending',
    'method' => 'credit-card',
    'amt' => 10000, // $100.00 in cents
    'principal_amt' => 10000,
]);
// Note: 'type' is automatically set to 'payment' by boot method

// Query all payments (automatically scoped)
$allPayments = Payment::all(); // WHERE type = 'payment'

// Query active payments
$activePayments = Payment::active()->get();

// Process a live payment
if ($payment->isLive()) {
    $payment->post(); // Triggers payment processor
}

// Create a refund
if ($payment->canBeRefunded()) {
    $refund = $payment->refund();
    // Creates Refund model, updates payment status to 'refunded'
}

// Get all refunds for a payment
$refunds = $payment->refunds;

// Check if automatic refund is possible
if ($payment->isAutomaticRefundEligible()) {
    // Can refund via payment processor
}

// Get payment receipt
$receiptUrl = $payment->getReceiptUrl();

// Access formatted values
echo $payment->formatted_type; // "Payment"
echo $payment->formatted_method; // "Credit Card"
echo $payment->model_no; // "PMT-00123"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
