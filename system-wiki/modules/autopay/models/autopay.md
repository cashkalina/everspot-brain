---
model: Autopay
module: Autopay
table: autopays
connection: tenant
primary_source: modules/Autopay/Models/Autopay.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Autopay/Providers/AutopayServiceProvider.php
  - app/Providers/EventServiceProvider.php
  - modules/Customer/Models/Customer.php
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Models/PaymentMethod.php
traits:
  - HasByUserFields
  - HasModelNumbering
  - HasMoneyFields
  - SoftDeletes
related_models: [Customer, Payment, PaymentMethod]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction]
---

# Autopay

## Overview

The Autopay model represents a recurring automatic-payment configuration attached to a customer and a payment method. It schedules periodic charges against a linked `PaymentMethod` at a defined `frequency` (weekly through annually), with a `start_date`, optional `end_date`, and computed `next_date` and `last_date` fields that track schedule state.

Each autopay is polymorphically associated with a parent entity (the "autopayable") — typically a `PaymentPlan` or similar funding arrangement — via the `autopayable_type` / `autopayable_id` morph. The `amt` column stores the recurring charge amount in cents (exposed as dollars via `HasMoneyFields`); a `match_parent` flag causes the amount to be resolved dynamically from the autopayable's own calculation instead of using the fixed `amt`. A `waive_processing_fees` flag suppresses processing-fee calculation for this autopay.

Processing fees are calculated lazily and cached in `$processingFeeData`: the `processing_fee` and `amt_with_fee` virtual attributes expose the fee amount and total. The `process()` method delegates the actual charge execution to `ProcessAutopay`. Dates are advanced after each successful run by `incrementDates()`, which sets `last_date = today()` and computes the next scheduled date using frequency-specific logic (with leap-year and month-end clamping). The `model_no` unique index supports external reference. Soft deletes preserve historical autopay records.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| autopayable_type | varchar | No | - | Morph type for the parent entity |
| autopayable_id | bigint | No | - | Morph ID for the parent entity |
| customer_id | bigint | No | - | FK → customers |
| payment_method_id | bigint | No | - | FK → payment_methods |
| model_no | varchar | Yes | - | User-facing autopay number — unique (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| start_date | date | No | - | First scheduled payment date |
| end_date | date | Yes | - | Final scheduled payment date (optional) |
| next_date | date | Yes | - | Next scheduled payment date; null when autopay is inactive |
| last_date | date | Yes | - | Date of the most recent payment run |
| amt | int | No | - | Recurring charge amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| frequency | varchar | No | - | Recurrence interval (`weekly`, `bi-weekly`, `monthly`, `quarterly`, `semi-annually`, `annually`) |
| is_active | tinyint | No | 1 | Whether this autopay is active |
| match_parent | tinyint | No | 0 | When true, amount is resolved from the autopayable rather than `amt` |
| waive_processing_fees | tinyint | No | 0 | When true, processing fees are not added |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `model_no`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`; `customer_id` → `customers.id`; `payment_method_id` → `payment_methods.id`

**Indexes:** composite index on (`autopayable_type`, `autopayable_id`); single-column indexes on `customer_id`, `next_date`; FK-backing indexes on `created_by`, `deleted_by`, `payment_method_id`, `updated_by`.

## Casts

- `start_date` → `date`
- `end_date` → `date`
- `next_date` → `date`
- `last_date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `is_active` → `1` (database default), `match_parent` → `0`, `waive_processing_fees` → `0`.

**Money attributes (cents storage, dollars access):** `amt` — declared in `$moneyAttributes` for [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

**Constants:**
```php
const FREQUENCIES = [
    'weekly'         => 'Weekly',
    'bi-weekly'      => 'Bi-Weekly',
    'monthly'        => 'Monthly',
    'quarterly'      => 'Quarterly',
    'semi-annually'  => 'Semi-Annually',
    'annually'       => 'Annually',
];
```

**Protected state:** `$processingFeeData` — nullable array; caches the result of processing fee calculation for the lifetime of the model instance.

## Accessors & Mutators

- `getFormattedFrequencyAttribute(): ?string` — looks up the `frequency` key in `FREQUENCIES`; returns the human-readable label (e.g. `'Monthly'`) or `null` if the frequency is unknown
- `getStatusBadgeAttribute(): string` — HTML badge: green "Active" when `is_active = true`, yellow "Inactive" otherwise
- `getProcessingFeeAttribute(): float` — virtual; returns the fee amount from the lazily computed `getProcessingFeeData()` result
- `getAmtWithFeeAttribute(): float` — virtual; returns `base_amount + fee_amount` from `getProcessingFeeData()`

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the unique user-facing `model_no`
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `amt`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — autopays are soft-deleted, preserving payment schedule history

## Relationships

- `autopayable()` — morphTo: the parent entity that owns this autopay (e.g. a `PaymentPlan`)
- `customer()` — belongs to [Customer](../../customer/models/customer.md): the customer being charged
- `paymentMethod()` — belongs to [PaymentMethod](../../transaction/models/payment-method.md) (with trashed): the payment method; fetched with `withTrashed()` so deleted payment methods remain accessible

## Scopes

- `active(Builder $query)` — filters to autopays where `is_active = true` AND `next_date` is not null

## Events

_None._

## Observers

_None registered._ `AutopayServiceProvider` registers no observers (`registerPolicies()` only).

## Key Methods

- `process(): ?Payment` — executes the autopay via `ProcessAutopay` action; returns the resulting `Payment` model or `null`
- `inactivate(): void` — sets `is_active = false` and `next_date = null`, then saves
- `calculatePaymentAmount(): float` — returns the charge amount: if `match_parent` is true, delegates to `$this->autopayable->calculateAutopayMatchPaymentAmount()`; otherwise delegates to `$this->autopayable->verifyPaymentAmount($this->amt)`
- `getNextDate(?Carbon $nextDateOverride = null): Carbon` — computes the next scheduled date from the current `next_date` (or an override) according to `frequency`, with month-end clamping and leap-year handling; throws `UnknownAutopayFrequency` for unknown frequencies
- `incrementDates(): void` — sets `last_date = today()` and advances `next_date` via `getNextDate()`; saves
- `hasProcessingFee(): bool` — returns `true` when processing fees are enabled and the fee amount is greater than zero
- `getModelTitleSuffix(): ?string` — returns `"{customer full name} ({autopayable identifier})"` for use in model numbering display

## Common Usage

```php
// Create an autopay for a customer on a payment plan
$autopay = Autopay::create([
    'customer_id'       => $customer->id,
    'payment_method_id' => $method->id,
    'autopayable_type'  => PaymentPlan::class,
    'autopayable_id'    => $plan->id,
    'start_date'        => today(),
    'amt'               => 5000,  // $50.00 in cents
    'frequency'         => 'monthly',
    'is_active'         => true,
]);

// Run a scheduled payment
$payment = $autopay->process();

// Advance dates after a successful run
$autopay->incrementDates();

// Check fees before processing
if ($autopay->hasProcessingFee()) {
    $total = $autopay->amt_with_fee;  // base + fee in dollars
}

// Find all active upcoming autopays
$dueToday = Autopay::active()->where('next_date', today())->get();

// Deactivate an autopay
$autopay->inactivate();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
