---
model: CommissionCalculation
module: Commission
table: commission_calculations
connection: tenant
primary_source: modules/Commission/Models/CommissionCalculation.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Commission/Observers/CommissionCalculationObserver.php
  - modules/Commission/Providers/CommissionServiceProvider.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Commission/Models/CommissionRate.php
  - modules/Common/Models/User.php
  - modules/Commission/Models/Commission.php
  - modules/Commission/Models/RepAssociation.php
traits:
  - HasFactory
  - SoftDeletes
  - HasMoneyFields
related_models: [Commission, CommissionRate, LiabilityLine, RepAssociation, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, commission]
---

# CommissionCalculation

## Overview

The CommissionCalculation model is the core accounting record in the commission lifecycle. When a sale occurs (captured as a [LiabilityLine](../../liability/models/liability-line.md)), the system creates one `CommissionCalculation` per rep association to determine exactly how much commission is owed. Each record captures the calculation inputs — `sale_price`, `sale_basis`, `eligible_amt`, `contribution` (the rep's share percentage), `effective_date`, `role` (e.g. primary vs. secondary rep), and `type` (commission type enum) — as well as the running totals: `paid_amt` and `due_amt`.

The `CommissionCalculationObserver` automatically recalculates `paid_amt` and `due_amt` every time a `CommissionCalculation` is saved, by summing the `amt` of all related [Commission](./commission.md) payouts. This keeps the tracking columns in sync without manual intervention. The `due_amt` equals `eligible_amt` minus `paid_amt`, providing a real-time view of outstanding obligation.

All money columns (`sale_price`, `sale_basis`, `eligible_amt`, `paid_amt`, `due_amt`) are stored as integer cents and exposed as dollars via `HasMoneyFields`. The `type` and `role` columns are cast to dedicated Enums (`Type` and `Role`).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| liability_line_id | bigint | No | - | FK → liability_lines: the sale line this calculation is for |
| commission_rate_id | bigint | No | - | FK → commission_rates: the rate rule used for this calculation |
| user_id | bigint | No | - | FK → users: the rep whose commission is being calculated |
| rep_association_id | bigint | No | - | FK → rep_associations: the rep-to-sale association driving this calculation |
| role | varchar | No | - | Rep role on the sale (cast to `Role` enum) |
| type | varchar | No | - | Commission type (cast to `Type` enum) |
| effective_date | date | No | - | Date the commission rule is effective |
| sale_price | int | No | - | Full sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| contribution | decimal | No | - | Rep's contribution percentage share |
| sale_basis | int | No | - | Basis amount on which the commission rate is applied, in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| eligible_amt | int | No | - | Total eligible commission amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| paid_amt | int | No | 0 | Amount already paid out in cents — auto-updated by observer (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| due_amt | int | No | 0 | Amount still owed in cents — auto-updated by observer (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `liability_line_id` → `liability_lines.id`; `commission_rate_id` → `commission_rates.id`; `user_id` → `users.id`; `rep_association_id` → `rep_associations.id`

**Indexes:** regular indexes on `commission_rate_id`, `due_amt`, `effective_date`, `liability_line_id`, `rep_association_id`, `user_id`.

## Casts

- `effective_date` → `date`
- `type` → `Type::class` (`Modules\Commission\Enums\Type`)
- `role` → `Role::class` (`Modules\Commission\Enums\Role`)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['sale_price', 'sale_basis', 'eligible_amt', 'paid_amt', 'due_amt']` — all stored as integer cents, transparently converted via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for testing
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — calculations are soft-deleted, never hard-deleted
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `sale_price`, `sale_basis`, `eligible_amt`, `paid_amt`, `due_amt`

## Relationships

- `liabilityLine()` — belongs to [LiabilityLine](../../liability/models/liability-line.md) (`liability_line_id`): the sale line this calculation applies to
- `commissionRate()` — belongs to [CommissionRate](./commission-rate.md) (`commission_rate_id`): the rate rule used for this calculation
- `user()` — belongs to [User](../../../system/models/user.md) (`user_id`): the rep whose commission is being calculated
- `repAssociation()` — belongs to [RepAssociation](./rep-association.md) (`rep_association_id`): the rep-to-sale link driving this calculation
- `commissions()` — has many [Commission](./commission.md) (`commission_calculation_id`): the individual payout records generated from this calculation

## Scopes

_None._

## Events

_None._

## Observers

- `CommissionCalculationObserver` — registered in `CommissionServiceProvider::registerObservers()` (`CommissionCalculation::observe(CommissionCalculationObserver::class)`). Handles:
  - `saved` — calls `calculatePaidAndDueAmounts()` to recompute `paid_amt` and `due_amt` from related commissions and saves if changed

## Key Methods

- `calculatePaidAndDueAmounts(): void` — sums `amt` across all related `Commission` records to update `paid_amt`; derives `due_amt = eligible_amt - paid_amt`; only calls `save()` when either value has actually changed

## Common Usage

```php
// Retrieve a calculation and check outstanding balance
$calc = CommissionCalculation::find($id);
echo $calc->eligible_amt;  // float in dollars, e.g. 500.00
echo $calc->paid_amt;      // float in dollars, e.g. 250.00
echo $calc->due_amt;       // float in dollars, e.g. 250.00

// Manually trigger recalculation (normally done by observer on save)
$calc->calculatePaidAndDueAmounts();

// List all payout records for this calculation
$payouts = $calc->commissions;

// Query calculations with amounts still due
$outstanding = CommissionCalculation::where('due_amt', '>', 0)->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
