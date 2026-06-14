---
model: PaymentPlanRestructure
module: PaymentPlan
table: payment_plan_restructures
connection: tenant
primary_source: modules/PaymentPlan/Models/PaymentPlanRestructure.php
source_paths:
  - modules/PaymentPlan/Models/PaymentPlan.php
  - modules/Common/Models/User.php
traits:
  - SoftDeletes
related_models: [PaymentPlan, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract]
---

# PaymentPlanRestructure

## Overview

PaymentPlanRestructure records a single restructuring event for a [PaymentPlan](./payment-plan.md). When a payment plan's terms are modified (e.g., interest rate, payment amount, or term length changed to accommodate a customer's circumstances), a restructure record is appended with the full before-and-after term snapshots, the effective date, an optional reason, and a reference to the [User](../../common/models/user.md) who performed the restructuring.

This model is an audit trail rather than an active operational record. The running history of restructures is queryable via `PaymentPlan::paymentPlanRestructures()`. The plan itself tracks only the most recent `restructured_date`; the full history lives here. Soft deletes are included for data integrity.

Note: `PaymentPlanRestructure` extends `Model` directly (not `BaseModel`), so it does not carry the standard BaseModel traits (HasExternalIds, HasIcon, HasModelDefinition, HasModificationRules, LogsActivity) or user-audit stamps.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| payment_plan_id | bigint | No | - | FK → payment_plans: the plan that was restructured |
| effective_date | date | No | - | Date the new terms take effect |
| old_terms | json | Yes | - | Snapshot of plan terms before restructuring |
| new_terms | json | Yes | - | Snapshot of plan terms after restructuring |
| reason | text | Yes | - | Free-text reason for the restructure |
| user_id | bigint | Yes | - | FK → users: the user who performed the restructure |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Indexes:** `payment_plan_id` (`payment_plan_restructures_payment_plan_id_index`); FK-backing index on `user_id` (`payment_plan_restructures_user_id_foreign`).

**Foreign keys:** `payment_plan_id` → `payment_plans.id`; `user_id` → `users.id`

## Casts

- `effective_date` → `date`
- `old_terms` → `array`
- `new_terms` → `array`

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — restructure records are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `paymentPlan()` — belongs to [PaymentPlan](./payment-plan.md): the plan this event restructured
- `user()` — belongs to [User](../../common/models/user.md): the user who performed the restructure

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._

## Common Usage

```php
// Retrieve restructure history for a plan
$history = $plan->paymentPlanRestructures()->orderBy('effective_date')->get();

// Inspect a restructure event
foreach ($history as $event) {
    echo $event->effective_date->toDateString();
    echo ' by ' . $event->user?->full_name;
    echo ' — reason: ' . $event->reason;
    // compare $event->old_terms vs $event->new_terms arrays
}

// Create a restructure record (typically done by an action class)
$plan->paymentPlanRestructures()->create([
    'effective_date' => today(),
    'old_terms'      => ['term' => 12, 'payment_amt' => 43125],
    'new_terms'      => ['term' => 18, 'payment_amt' => 28750],
    'reason'         => 'Customer hardship — extended term',
    'user_id'        => auth()->id(),
]);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
