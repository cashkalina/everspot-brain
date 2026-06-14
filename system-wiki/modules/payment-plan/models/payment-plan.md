---
model: PaymentPlan
module: PaymentPlan
table: payment_plans
connection: tenant
primary_source: modules/PaymentPlan/Models/PaymentPlan.php
source_paths:
  - app/Models/BaseModel.php
  - modules/PaymentPlan/Observers/PaymentPlanObserver.php
  - modules/PaymentPlan/Providers/PaymentPlanServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Customer/Models/Customer.php
  - modules/Order/Models/Order.php
  - modules/Common/Models/Note.php
  - modules/Autopay/Models/Autopay.php
  - modules/PaymentPlan/Models/PaymentPlanRestructure.php
traits:
  - HasByUserFields
  - HasFiles
  - HasModelNumbering
  - HasMoneyFields
  - HasSearch
  - HasTransactions
  - HasTransactionService
  - SoftDeletes
related_models: [Autopay, Cemetery, Customer, Note, Order, PaymentPlanRestructure, Transaction]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract]
---

# PaymentPlan

## Overview

PaymentPlan represents a financing arrangement that allows cemetery customers to pay for goods and services in installments over time. Each plan is tied to a [Cemetery](../../common/models/cemetery.md) and optionally to an [Order](../../order/models/order.md), and can be associated with one or more [Customer](../../customer/models/customer.md) records in different roles (primary, additional) via a pivot table.

The plan captures the complete financial structure of the installment agreement: the total amount financed, down payment, interest rate, payment frequency, and term. Running balance columns (`principal_balance`, `interest_balance`, `fee_balance`, `total_balance`) are maintained by the `UpdatePaymentPlanBalances` action whenever a transaction is recorded. Due-tracking columns (`amt_due`, `amt_past_due`, `days_past_due`, `next_due_date`, `date_last_current`) are updated by the `UpdatePaymentPlanDueTracking` action. All money columns are stored in cents as integers and converted transparently to dollars via the [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) trait.

Status flows through five states — `pending`, `active`, `pending-payoff`, `canceled`, `paid-in-full` — with lifecycle transitions driven by `activate()` / `inactivate()` / `onPendingPayoff()` / `onActive()` / `onPaidInFull()` actions. The model also supports autopay linkage (via morphMany to [Autopay](../../autopay/models/autopay.md)), late fee assessment, restructuring (tracked via [PaymentPlanRestructure](./payment-plan-restructure.md)), file attachments, and search indexing. Daily maintenance commands (interest accrual, late fees, past-due tracking, etc.) operate against this model in batch.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery this plan belongs to |
| order_id | bigint | Yes | - | FK → orders: the associated order (if any) |
| model_no | varchar | Yes | - | User-facing plan number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| date | date | No | - | Plan origination date |
| status | varchar | No | - | Plan status (`pending`, `active`, `pending-payoff`, `canceled`, `paid-in-full`) |
| down_payment | int | No | - | Down payment amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| amount_financed | int | No | - | Total amount financed in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| interest_rate | decimal | No | - | Annual interest rate as a decimal (e.g. `0.05` = 5%) |
| term | int | No | - | Number of payment periods |
| frequency | varchar | No | - | Payment frequency (`weekly`, `bi-weekly`, `monthly`, `quarterly`, `semi-annually`, `annually`) |
| payment_amt | int | No | - | Regular payment amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| enable_late_fee | tinyint | No | 0 | Whether late fees are enabled |
| grace_period | int | Yes | - | Grace period in days before a late fee is assessed |
| late_fee_amt | int | Yes | - | Late fee amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| activated_date | date | Yes | - | Date the plan was activated |
| restructured_date | date | Yes | - | Date the plan was most recently restructured |
| first_due_date | date | No | - | First scheduled payment due date |
| last_due_date | date | Yes | - | Last scheduled payment due date |
| late_fee_last_due_date | date | Yes | - | Date through which late fees have been assessed |
| next_due_date | date | Yes | - | Next upcoming payment due date |
| closed_date | date | Yes | - | Date the plan was closed (pending-payoff or canceled) |
| amt_due | int | No | 0 | Current amount due in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| amt_past_due | int | No | 0 | Amount past due in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| days_past_due | int | No | 0 | Number of days the plan is past due |
| date_last_current | date | No | - | Date the plan was last current (no past-due amount) |
| late_fee_assessed | tinyint | No | 0 | Whether a late fee has been assessed for the current cycle |
| principal_balance | int | No | - | Outstanding principal balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| interest_balance | int | No | - | Outstanding interest balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| fee_balance | int | No | - | Outstanding fee balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| total_balance | int | No | - | Total outstanding balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `model_no` (`payment_plans_model_no_unique`)

**Indexes:** `activated_date`, `amt_due`, `amt_past_due`, `cemetery_id`, `days_past_due`, `enable_late_fee`, `late_fee_assessed`, `next_due_date`, `order_id`, `payment_amt`, `restructured_date`, `status`, `total_balance`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `order_id` → `orders.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

## Casts

- `date` → `date`
- `first_due_date` → `date`
- `last_due_date` → `date`
- `late_fee_last_due_date` → `date`
- `next_due_date` → `date`
- `closed_date` → `date`
- `activated_date` → `date`
- `restructured_date` → `date`
- `date_last_current` → `TimezonedDateTime::class` (from `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `enable_late_fee`, `amt_due`, `amt_past_due`, `days_past_due`, `late_fee_assessed` all default to `0` at the database level. Observer sets initial balance fields on `creating`.

**Constants / static config:**
```php
const STATUSES = [
    'pending'        => ['label' => 'Pending',        'color' => 'warning'],
    'active'         => ['label' => 'Active',          'color' => 'success'],
    'pending-payoff' => ['label' => 'Pending Payoff',  'color' => 'info'],
    'canceled'       => ['label' => 'Canceled',        'color' => 'danger'],
    'paid-in-full'   => ['label' => 'Paid in Full',    'color' => 'secondary'],
];

const FREQUENCIES = [
    'weekly'         => 'Weekly',
    'bi-weekly'      => 'Bi-Weekly',
    'monthly'        => 'Monthly',
    'quarterly'      => 'Quarterly',
    'semi-annually'  => 'Semi-Annually',
    'annually'       => 'Annually',
];

public $moneyAttributes = [
    'payment_amt', 'late_fee_amt', 'interest_balance', 'fee_balance',
    'principal_balance', 'total_balance', 'down_payment', 'amount_financed',
    'amt_due', 'amt_past_due',
];
```

## Accessors & Mutators

- `getFormattedFrequencyAttribute(): ?string` — human-readable frequency label from `FREQUENCIES` (e.g. `'bi-weekly'` → `'Bi-Weekly'`)
- `getPerFrequencyAttribute(): ?string` — per-period label (e.g. `'monthly'` → `'Per Month'`)
- `getFrequencyUnitAttribute(): ?string` — period unit label (e.g. `'monthly'` → `'Month'`)
- `getFormattedTermFrequencyAttribute(): string` — combined term + frequency description (e.g. `'12 monthly payments'`)
- `getFormattedInterestRateAttribute(): string` — interest rate as a percentage string with trailing-zero cleanup (e.g. `'5.00%'`)
- `getPaymentsTotalAttribute(): float` — sum of all non-financing, non-interest transactions (dollar value, converted from cents)
- `getPaymentsTotalAfterRestructureAttribute(): float` — same sum restricted to transactions on or after `restructured_date` (when applicable)
- `getAmountDueAttribute(): float` — alias for `amt_due` (dollar value via HasMoneyFields conversion)
- `getTotalPrincipalPaidAttribute(): float` — `amount_financed` minus `principal_balance` (dollars)
- `getPaymentsRemainingAttribute(): int` — remaining payment count via `CalculateTerm` action
- `getNextAutopayDateAttribute(): ?Carbon` — next active autopay date (earliest `next_date` from active autopays)
- `getNextPaymentAmountAttribute(): float` — `payment_amt` capped at `calculateMaxPaymentAmount()` to prevent overpayment

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backed by `created_by` / `updated_by` / `deleted_by` columns
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments for plan documents (implements `HasMedia`)
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` for the plan
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for all columns in `$moneyAttributes`
- [HasSearch](../../../system/traits/index.md#hassearch) — Scout search indexing; `addToSearchData()` exposes primary customer name and order number
- [HasTransactions](../../../system/traits/index.md#hastransactions) — polymorphic `transactions()` and `payments()` morphMany relationships via `transactionable`
- [HasTransactionService](../../../system/traits/index.md#hastransactionservice) — provides `createCharge()`, `createCredit()`, `createFinancingTransfer()`, `createInterest()` and other transaction factory helpers via `TransactionService`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — payment plans are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery this plan belongs to
- `order()` — belongs to [Order](../../order/models/order.md): the associated sales order
- `customers()` — belongs-to-many [Customer](../../customer/models/customer.md) with pivot `role`: all customers associated with this plan
- `additionalCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) (pivot `role = 'additional'`): non-primary customers
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): plan notes
- `autopays()` — morphMany [Autopay](../../autopay/models/autopay.md) (`autopayable`): automatic payment configurations for this plan
- `paymentPlanRestructures()` — has many [PaymentPlanRestructure](./payment-plan-restructure.md): restructuring history

Relationships contributed by traits:
- `transactions()` — morphMany [Transaction](../../transaction/models/transaction.md) (via [HasTransactions](../../../system/traits/index.md#hastransactions))
- `payments()` — morphMany [Transaction](../../transaction/models/transaction.md) scoped to payment type (via [HasTransactions](../../../system/traits/index.md#hastransactions))

## Scopes

- `scopeActiveAsOf($query, $date): Builder` — returns plans that were activated on or before `$date` and not yet closed (or in `pending-payoff` status)
- `scopeOpen($query): Builder` — returns plans in `active` or `pending-payoff` status

## Events

_None defined on the model._ Lifecycle behavior is handled by `PaymentPlanObserver` (see Observers).

## Observers

- `PaymentPlanObserver` — registered in `PaymentPlanServiceProvider::registerObservers()` (`PaymentPlan::observe(PaymentPlanObserver::class)`). Handles:
  - `creating` — initializes balances: sets `interest_balance = 0`, `fee_balance = 0`, `principal_balance = amount_financed`, `total_balance` (sum); sets `next_due_date` and `date_last_current` from `first_due_date`
  - `created` — fires `analytics()->track('Payment Plan Created')`; runs `UpdatePaymentPlanDueTracking`
  - `deleting` — wraps deletion in a DB transaction; runs `PreDeletePaymentPlan` checks

## Key Methods

- `primaryCustomer(): ?Customer` — returns the customer from `customers` collection where `pivot.role = 'primary'` (not a scope — loads via collection)
- `transactionUpdated($transaction): void` — called by the transaction service after a transaction changes; triggers `UpdatePaymentPlanBalances`
- `assessLateFee(): Transaction` — DB transaction: creates a charge for `late_fee_amt` with memo `'Automatic Late Fee'` and sets `late_fee_assessed = 1`
- `createMatchAutopay($customerId, $paymentMethodId): Autopay` — creates a match-parent autopay using current plan frequency and `next_due_date`
- `calculateEstimatedPayoffDate(float $paymentAmount, string $frequency, Carbon $startDate, ?Carbon $endDate = null): ?Carbon` — delegates to `CalculateEstimatedPayoffDate` action
- `calculatePayoffForDays($days): float` — delegates to `CalculatePayoffForDays` action
- `calculateMaxPaymentAmount(): float` — returns `calculatePayoffForDays(0)` (immediate payoff amount)
- `verifyPaymentAmount($amount): float` — clamps `$amount` between 0 and `calculateMaxPaymentAmount()`
- `calculateAutopayMatchPaymentAmount(): float` — returns the verified amount due (max of `amt_due` and `payment_amt`, capped at payoff)
- `getNextAutopayFeeEstimate(): ?array` — returns processing fee breakdown for the active autopay's next charge (or `null` if no active autopay or fee not enabled)
- `activate(): void` — runs `ActivatePaymentPlan` action
- `inactivate(): void` — runs `InactivatePaymentPlan` action
- `inactivateAutopays(): void` — deactivates all active autopays on this plan
- `onPendingPayoff(): void` — sets `closed_date = today()` and saves
- `onActive(): void` — clears `closed_date` and saves
- `onPaidInFull(): void` — inactivates autopays, clears `next_due_date`, saves, and runs `ReportPIFDateToLiabilityLines`
- `wasRestructured(): bool` — returns `true` if `restructured_date` is not null
- `canBeRestructured(): bool` — delegates to the modification strategy
- `isPastDue(): bool` — returns `true` if `days_past_due > 0`
- `hasAutopay(): bool` — returns `true` if there is at least one active autopay
- `hasNonFinalizedPayments(): bool` — returns `true` if any payment is in `pending` or `processing` status
- `addToSearchData(): array` — provides `primary_customer_full_name` and `order_model_no` for search indexing

## Common Usage

```php
// Create a payment plan
$plan = PaymentPlan::create([
    'cemetery_id'     => $cemetery->id,
    'order_id'        => $order->id,
    'date'            => today(),
    'status'          => 'pending',
    'amount_financed' => 500000,  // $5,000.00 in cents
    'interest_rate'   => 0.05,
    'term'            => 12,
    'frequency'       => 'monthly',
    'payment_amt'     => 43125,   // cents
    'down_payment'    => 0,
    'first_due_date'  => now()->addMonth(),
]);

// Activate the plan
$plan->activate();

// Assess a late fee
$lateFeeTransaction = $plan->assessLateFee();

// Check payment status
if ($plan->isPastDue()) {
    // handle past-due notification
}

// Get estimated payoff date
$payoffDate = $plan->calculateEstimatedPayoffDate(
    $plan->payment_amt,
    $plan->frequency,
    today()
);

// Query active plans as of a specific date
$active = PaymentPlan::activeAsOf('2026-01-01')->get();

// Open plans only
$open = PaymentPlan::open()->with('customers')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
