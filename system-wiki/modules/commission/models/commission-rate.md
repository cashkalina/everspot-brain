---
model: CommissionRate
module: Commission
table: commission_rates
connection: tenant
primary_source: modules/Commission/Models/CommissionRate.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Commission/Observers/CommissionRateObserver.php
  - modules/Commission/Providers/CommissionServiceProvider.php
  - modules/Commission/Models/CommissionPlan.php
  - modules/Commission/Pivots/CommissionPlanCommissionRatePivot.php
traits:
  - HasFactory
  - SoftDeletes
  - HasMoneyFields
  - HasByUserFields
related_models: [CommissionPlan]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, commission, admin]
---

# CommissionRate

## Overview

The CommissionRate model defines a commission calculation rule — how much commission is earned, under what conditions, and when/how it is paid. A rate record encodes the commission structure: whether it pays a fixed dollar amount (`enable_fixed_dollar` / `fixed_dollar`), a percentage of revenue (`enable_pct_revenue` / `pct_revenue`), or both; whether new commissions are enabled (`enable_new_commission`); whether chargebacks apply (`enable_chargebacks`); the basis on which the calculation is made (`basis`); the timing of payment (`paid_at` / `paid_on`); and optional `criteria` (stored as a JSON array) for any additional conditional logic.

CommissionRates are attached to [CommissionPlan](./commission-plan.md)s via the `commission_plan_commission_rate` pivot table (with date-range effectivity on the pivot). When a rate is saved, the `CommissionRateObserver` automatically dispatches a `RecalculateCommissionsForPlans` job for all plans that use this rate, ensuring that any changes to the rate rule cascade to recalculate outstanding commission calculations.

The `paid_at` and `paid_on` columns are cast to the `PaidAt` and `PaidOn` enums respectively. The `fixed_dollar` column is stored as integer cents and converted via `HasMoneyFields`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Rate rule name |
| paid_at | varchar | No | - | When the commission is paid (cast to `PaidAt` enum) |
| paid_on | varchar | No | - | What the commission is paid on (cast to `PaidOn` enum) |
| basis | varchar | No | - | Calculation basis (e.g. sale price, profit) |
| criteria | json | No | - | JSON array of additional criteria conditions |
| enable_new_commission | tinyint | No | - | Whether new commissions are enabled for this rate |
| enable_chargebacks | tinyint | No | - | Whether chargebacks apply for this rate |
| enable_fixed_dollar | tinyint | No | - | Whether a fixed dollar amount is paid |
| enable_pct_revenue | tinyint | No | - | Whether a percentage of revenue is paid |
| fixed_dollar | int | No | 0 | Fixed dollar amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| pct_revenue | decimal | No | - | Percentage of revenue to pay as commission |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Pivot table:** `commission_plan_commission_rate` (with `effective_start_date`, `effective_end_date`).

## Casts

- `paid_at` → `PaidAt::class` (`Modules\Commission\Enums\PaidAt`)
- `paid_on` → `PaidOn::class` (`Modules\Commission\Enums\PaidOn`)
- `criteria` → `array`
- `enable_new_commission` → `boolean`
- `enable_chargebacks` → `boolean`
- `enable_fixed_dollar` → `boolean`
- `enable_pct_revenue` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** (not explicitly set — inherits BaseModel default)
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['fixed_dollar']` — stored as integer cents, exposed as dollars via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for testing
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — rates are soft-deleted, never hard-deleted
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `fixed_dollar`
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps

## Relationships

- `commissionPlans()` — belongs-to-many [CommissionPlan](./commission-plan.md) via `commission_plan_commission_rate` (using `CommissionPlanCommissionRatePivot`), with pivot columns `effective_start_date`, `effective_end_date`: the plans that use this rate

## Scopes

_None._

## Events

_None._

## Observers

- `CommissionRateObserver` — registered in `CommissionServiceProvider::registerObservers()` (`CommissionRate::observe(CommissionRateObserver::class)`). Handles:
  - `saved` — collects IDs of all related `commissionPlans` and dispatches `RecalculateCommissionsForPlans` job to propagate rate changes through affected calculations

## Key Methods

- `commissionPlansByDate(Carbon $date): BelongsToMany` — returns the `commissionPlans()` relationship scoped to plans with pivot `effective_start_date <= $date` and (`effective_end_date` is null or `effective_end_date >= $date`); used for point-in-time plan resolution

## Common Usage

```php
// Create a fixed-dollar commission rate
$rate = CommissionRate::create([
    'name'                 => 'Flat $100 Pre-Need',
    'paid_at'              => PaidAt::Collection,
    'paid_on'              => PaidOn::Sale,
    'basis'                => 'sale_price',
    'criteria'             => [],
    'enable_new_commission'=> true,
    'enable_chargebacks'   => false,
    'enable_fixed_dollar'  => true,
    'enable_pct_revenue'   => false,
    'fixed_dollar'         => 100.00, // stored as 10000 cents
    'pct_revenue'          => 0,
]);

// Retrieve all plans using this rate on a specific date
$plans = $rate->commissionPlansByDate(now())->get();

// After updating a rate, the observer auto-dispatches recalculation
$rate->update(['fixed_dollar' => 150.00]);
// → RecalculateCommissionsForPlans dispatched for affected plan IDs
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
