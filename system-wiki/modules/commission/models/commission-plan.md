---
model: CommissionPlan
module: Commission
table: commission_plans
connection: tenant
primary_source: modules/Commission/Models/CommissionPlan.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/User.php
  - modules/Commission/Models/CommissionRate.php
  - modules/Commission/Pivots/CommissionPlanUserPivot.php
  - modules/Commission/Pivots/CommissionPlanCommissionRatePivot.php
traits:
  - HasFactory
  - SoftDeletes
  - HasByUserFields
related_models: [CommissionRate, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, commission, admin]
---

# CommissionPlan

## Overview

The CommissionPlan model represents a named commission plan that associates sales representatives ([User](../../../system/models/user.md)) with one or more [CommissionRate](./commission-rate.md) rules, both with date-range effectivity. A plan is the top-level configuration object in the commission module: you create a plan, assign reps to it (with `effective_start_date` / `effective_end_date` on the pivot), and attach rate rules to it (also with date-range effectivity on the pivot).

Both the user and commission-rate associations use custom pivot classes — `CommissionPlanUserPivot` and `CommissionPlanCommissionRatePivot` respectively — which carry `effective_start_date` / `effective_end_date` columns and dispatch recalculation jobs (`RecalculateCommissionsForUsers`, `RecalculateCommissionsForPlans`) whenever the pivot is saved or deleted.

The model provides date-filtered relationship methods (`usersByDate` and `commissionRatesByDate`) that scope the pivot to records effective on a given date, supporting point-in-time plan resolution.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Plan name |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Pivot tables:** `commission_plan_user` (with `effective_start_date`, `effective_end_date`); `commission_plan_commission_rate` (with `effective_start_date`, `effective_end_date`).

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for testing
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — plans are soft-deleted, never hard-deleted
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps

## Relationships

- `users()` — belongs-to-many [User](../../../system/models/user.md) via `commission_plan_user` (using `CommissionPlanUserPivot`), with pivot columns `id`, `effective_start_date`, `effective_end_date`: all reps assigned to this plan
- `commissionRates()` — belongs-to-many [CommissionRate](./commission-rate.md) via `commission_plan_commission_rate` (using `CommissionPlanCommissionRatePivot`), with pivot columns `effective_start_date`, `effective_end_date`: rate rules attached to this plan

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `usersByDate(Carbon $date): BelongsToMany` — returns the `users()` relationship scoped to reps whose pivot `effective_start_date <= $date` and (`effective_end_date` is null or `effective_end_date >= $date`); used for point-in-time plan membership resolution
- `commissionRatesByDate(Carbon $date): BelongsToMany` — returns the `commissionRates()` relationship scoped to rates effective on `$date`; used for point-in-time rate lookup

## Common Usage

```php
// Create a plan
$plan = CommissionPlan::create(['name' => 'Standard Pre-Need Plan']);

// Assign a rep with date range
$plan->users()->attach($rep->id, [
    'effective_start_date' => '2026-01-01',
    'effective_end_date'   => null,
]);

// Attach a rate rule
$plan->commissionRates()->attach($rate->id, [
    'effective_start_date' => '2026-01-01',
    'effective_end_date'   => null,
]);

// Resolve reps effective on a specific date
$activeReps = $plan->usersByDate(now())->get();

// Resolve rates effective on a specific date
$activeRates = $plan->commissionRatesByDate(now())->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
