---
model: Transaction
module: Transaction
table: transactions
connection: tenant
sti: base
sti_subtypes: [Payment, Refund]
primary_source: modules/Transaction/Models/Transaction.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Transaction/Observers/TransactionObserver.php
  - modules/Transaction/Providers/TransactionServiceProvider.php
  - modules/Customer/Models/Customer.php
  - modules/Transaction/Models/PaymentMethod.php
  - modules/Transaction/Models/DepositBatch.php
  - modules/Accounting/Models/JournalEntry.php
traits:
  - HasByUserFields
  - HasModelNumbering
  - HasMoneyFields
  - HasSearch
  - HasSyncables
related_models: [Customer, DepositBatch, JournalEntry, PaymentMethod, Transaction]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction, core]
---

# Transaction

## Overview

Transaction is the central financial record in Everspot, representing every monetary movement in the system — payments, refunds, charges, credits, interest entries, processing fees, cancellation credits, and financing transfers. It serves as the STI base for the `transactions` table, with [Payment](./payment.md) and [Refund](./refund.md) as concrete subtypes that apply a global type scope and carry their own observers.

Every transaction is polymorphically attached to the entity it belongs to — an Order, a PaymentPlan, or another transactionable — via the `transactionable` morph. A second morph, `postable`, tracks which entity triggered the accounting posting. Transactions link to a Customer and optionally to a PaymentMethod (for live credit-card or ACH payments) and a DepositBatch (for cash/check reconciliation batches).

Money amounts are stored in cents (integer) across five amount columns (`amt`, `principal_amt`, `fee_amt`, `interest_amt`, `basis_amt`). Transparent dollar-to-cents conversion is provided by the [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) trait. Transaction posting to the accounting ledger is handled by the `post()` method via a `PostingStrategyFactory`. Reversals create a new transaction linked by `reversing_transaction_id`; refunds create a new Refund linked by the same mechanism.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| transactionable_type | varchar | No | - | Morph type: the entity this transaction belongs to (e.g. Order, PaymentPlan) |
| transactionable_id | bigint | No | - | Morph id: FK to the transactionable entity |
| payment_method_id | bigint | Yes | - | FK → payment_methods: the stored payment method used (null for cash/check) |
| customer_id | bigint | Yes | - | FK → customers: the customer this transaction belongs to |
| model_no | varchar | Yes | - | User-facing transaction number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| date | date | No | - | Transaction date |
| type | varchar | No | - | STI discriminator: payment, refund, charge, credit, interest, processing-fee, cancellation-credit, financing-transfer |
| status | varchar | No | - | Lifecycle status: pending, processing, action-required, posted, failed, refunded, reversed |
| method | varchar | Yes | - | Payment method type: cash, check, credit-card, ach, other |
| amt | int | No | - | Total transaction amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| principal_amt | int | No | - | Principal portion in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| fee_amt | int | No | - | Processing fee portion in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| interest_amt | int | No | - | Interest portion in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| basis_amt | int | Yes | - | Basis amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| rate | decimal | Yes | - | Interest or fee rate as a decimal (e.g. 0.05 = 5%) |
| memo | text | Yes | - | Optional transaction memo/note |
| check_no | varchar | Yes | - | Check number for check payments |
| is_deposited | tinyint | No | 0 | Whether this transaction has been included in a deposit batch |
| deposit_batch_id | bigint | Yes | - | FK → deposit_batches: the batch this was deposited in |
| is_posted | tinyint | No | 0 | Whether this transaction has been posted to the accounting ledger |
| postable_type | varchar | Yes | - | Morph type: entity that triggered the accounting posting |
| postable_id | bigint | Yes | - | Morph id: FK to the postable entity |
| is_reversal | tinyint | No | 0 | Whether this transaction is itself a reversal of another |
| reversing_transaction_id | bigint | Yes | - | FK → transactions: the transaction this one reverses |
| related_transaction_id | bigint | Yes | - | FK → transactions: a related transaction (e.g. processing fee linked to a payment) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp (via TimezonedDateTime cast) |
| updated_at | timestamp | Yes | - | Last update timestamp (via TimezonedDateTime cast) |

**Primary key:** `id`

**Foreign keys:** `customer_id` → `customers.id`; `payment_method_id` → `payment_methods.id`; `deposit_batch_id` → `deposit_batches.id`; `reversing_transaction_id` → `transactions.id`; `related_transaction_id` → `transactions.id` (cascade delete); `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** Composite index on (`transactionable_type`, `transactionable_id`); single-column indexes on `type`, `status`, `customer_id`, `payment_method_id`, `deposit_batch_id`, `related_transaction_id`, `reversing_transaction_id`; unique index on `model_no`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Note:** There is no `deleted_at` column — the Transaction model does not use SoftDeletes. The `deleted_by` column is contributed by [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) but soft-delete support is not active on this model.

## Casts

- `date` → `date`
- `is_reversal` → `boolean`
- `created_at` → `TimezonedDateTime::class` — timezone-aware timestamp handling
- `updated_at` → `TimezonedDateTime::class` — timezone-aware timestamp handling

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
const TYPES = [
    'financing-transfer' => 'Financing Transfer',
    'processing-fee'     => 'Processing Fee',
    'cancellation-credit'=> 'Cancellation Credit',
    'charge'             => 'Charge',
    'payment'            => 'Payment',
    'refund'             => 'Refund',
    'credit'             => 'Credit',
    'interest'           => 'Interest',
];

const STATUSES = [
    'pending'         => ['label' => 'Pending',          'color' => 'warning'],
    'processing'      => ['label' => 'Processing',       'color' => 'info'],
    'action-required' => ['label' => 'Action Required',  'color' => 'warning'],
    'posted'          => ['label' => 'Posted',           'color' => 'success'],
    'failed'          => ['label' => 'Failed',           'color' => 'danger'],
    'refunded'        => ['label' => 'Refunded',         'color' => 'secondary'],
    'reversed'        => ['label' => 'Reversed',         'color' => 'secondary'],
];

const METHODS = [
    'cash'        => 'Cash',
    'check'       => 'Check',
    'credit-card' => 'Credit Card',
    'ach'         => 'ACH (Bank Account)',
    'other'       => 'Other',
];

const liveMethods = ['credit-card', 'ach'];

public array $moneyAttributes = ['amt', 'principal_amt', 'fee_amt', 'interest_amt', 'basis_amt'];
```

## Accessors & Mutators

- `getFormattedTypeAttribute(): string` — human-readable type label from `TYPES` constant (e.g. `'payment'` → `'Payment'`)
- `getFormattedRateAttribute(): ?string` — rate as a formatted percentage string (e.g. `'5.00%'`), trimming trailing zeros; `null` if no rate
- `getFormattedMethodAttribute(): ?string` — human-readable method label from `METHODS` constant; `null` if no method set

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` for transaction records
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for all five amount columns declared in `$moneyAttributes`
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; searchable column is `model_no`
- [HasSyncables](../../../system/traits/index.md#hassyncables) — links transactions to external-integration records (e.g. payment processor references)

## Relationships

- `transactionable()` — morphTo: the parent entity that owns this transaction (may be Order, PaymentPlan, or other transactionable types)
- `postable()` — morphTo: the entity that triggered the accounting posting (polymorphic)
- `paymentMethod()` — belongs to [PaymentMethod](./payment-method.md) (`payment_method_id`, with trashed): the stored payment method used for live payments
- `customer()` — belongs to [Customer](../../customer/models/customer.md) (`customer_id`): the customer this transaction belongs to
- `depositBatch()` — belongs to [DepositBatch](./deposit-batch.md) (`deposit_batch_id`): the deposit batch this was included in
- `reversingTransaction()` — belongs to [Transaction](./transaction.md) (`reversing_transaction_id`): the transaction that this one reversed (self-referential)
- `reversedByTransaction()` — has one [Transaction](./transaction.md) (`reversing_transaction_id`): the reversal transaction created for this one (self-referential)
- `relatedTransaction()` — belongs to [Transaction](./transaction.md) (`related_transaction_id`): a related transaction (e.g. a processing fee linked to a payment)
- `relatedTransactions()` — has many [Transaction](./transaction.md) (`related_transaction_id`): child transactions related to this one (e.g. processing fees)
- `processingFee()` — has one [Transaction](./transaction.md) where `type = 'processing-fee'` (`related_transaction_id`): the associated processing-fee transaction
- `journalEntries()` — has many JournalEntry (`journalable_id`, morph-constrained to Transaction/Payment/Refund types): accounting ledger entries for this transaction

## Scopes

- `active(Builder $query)` — filters to `status IN ('processing', 'posted')`
- `notReversed(Builder $query)` — excludes transactions that have a reversal (`reversedByTransaction`)
- `notReversal(Builder $query)` — excludes transactions where `is_reversal = false` (i.e. excludes reversal transactions themselves)
- `notReversedOrReversal(Builder $query)` — combines `notReversed()` and `notReversal()`: excludes all reversal-related transactions
- `ofType(Builder $query, string $type)` — filters by a specific `type` value
- `hideZeroDollarTransactions(Builder $query)` — excludes transactions where `amt = 0`

## Events

- Dispatches `PaymentSuccessful` when a Payment transitions from `pending` to `posted` (handled in `onPosted()`)
- Dispatches `PaymentFailed` when a Payment fails; dispatches `RefundFailed` when a Refund fails (handled in `onFailed()`)
- Dispatches `PaymentRequiresAction` / `RefundRequiresAction` when action is needed (handled in `onRequiresAction()`)

These dispatch methods are defined on Transaction but are type-checked with `instanceof` — they only fire for the relevant STI subtype.

## Observers

- `TransactionObserver` — registered in `TransactionServiceProvider::registerObservers()` (`Transaction::observe(TransactionObserver::class)`). Handles:
  - `saved` — calls `$transaction->transactionUpdated()` to notify the transactionable parent
  - `deleted` — calls `$transaction->transactionUpdated()`
  - `restored` — calls `$transaction->transactionUpdated()`
  - `forceDeleted` — calls `$transaction->transactionUpdated()`
  - `creating`, `created`, `updated` — no-op stubs

## Key Methods

- `post(): void` — posts the transaction to the accounting ledger via `PostingStrategyFactory::create($this)->post()`
- `reverse(bool $withStatusChange = true): Transaction` — creates a reversal transaction via the transactionable's `reverseTransaction()`; optionally transitions this transaction to `reversed` status; wrapped in a DB transaction
- `refund(bool $withStatusChange = true): Refund` — creates a Refund transaction via the transactionable's `createRefund()`; optionally transitions this transaction to `refunded` status; wrapped in a DB transaction
- `transactionUpdated(): void` — notifies the `transactionable` parent by calling `transactionable->transactionUpdated($this)` if the method exists
- `canBeReversed(): bool` — true if posted, not already reversed/reversing, and type is one of payment/charge/credit/processing-fee
- `canBeRefunded(): bool` — true if posted, not already reversed/reversing, and type is `payment`
- `isLive(): bool` — true if `method` is `credit-card` or `ach`
- `isAutomaticRefundEligible(): bool` — true if refundable, live, and the payment processor supports live payments
- `isReversedOrReversal(): bool` — true if `is_reversal` is set or a `reversedByTransaction` exists
- `shouldBeNegative(string $field): bool` — returns true for amount fields on credit/payment/cancellation-credit types (used by HasMoneyFields for sign convention)
- `onPosted(string $oldStatus): void` — dispatches `PaymentSuccessful` when a Payment transitions from pending to posted
- `onFailed(): void` — dispatches `PaymentFailed` or `RefundFailed` based on runtime type
- `onRequiresAction(): void` — dispatches `PaymentRequiresAction` or `RefundRequiresAction` based on runtime type
- `getReceiptUrl(): ?string` — returns the URL for the PDF receipt template for this transaction
- `getModelFullTitle(): ?string` — returns the type label plus model title (e.g. "Payment #TXN-001")
- `getModelFullTitleNoSuffix(): ?string` — same as `getModelFullTitle()` but without the title suffix
- `getAppRouteByType(string $type, mixed $id = null): ?string` *(static)* — resolves the show-route for the transaction by delegating to the transactionable's own route resolver

## STI Details

This model is the **base** of an STI hierarchy. It owns and renders the full shared-table schema above. The `type` column is the discriminator; subtypes automatically scope to their value via `TransactionByTypeScope`.

Subtypes:
- [Payment](./payment.md) — `type=payment`
- [Refund](./refund.md) — `type=refund`

Other `type` values (`charge`, `credit`, `interest`, `processing-fee`, `cancellation-credit`, `financing-transfer`) are stored using the base Transaction class directly — there are no dedicated model classes for them.

## Common Usage

```php
// Access all transactions for a customer
$transactions = $customer->transactions;

// Access only posted transactions (scoped)
$posted = Transaction::active()->where('customer_id', $customer->id)->get();

// Exclude reversals and reversed transactions
$clean = Transaction::notReversedOrReversal()->get();

// Filter by type (for non-STI types without a subtype class)
$charges = Transaction::ofType('charge')->get();

// Post a transaction to the ledger
$transaction->post();

// Reverse a transaction
$reversal = $transaction->reverse();

// Refund a payment (returns a Refund instance)
$refund = $payment->refund();

// Check if a transaction can be reversed
if ($transaction->canBeReversed()) {
    $transaction->reverse();
}

// Access the parent transactionable
$order = $transaction->transactionable; // e.g. an Order
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
