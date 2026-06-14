---
model: Subscription
module: Subscription
table: subscriptions
connection: tenant
primary_source: modules/Subscription/Models/Subscription.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Repetition/Traits/Repeatable.php
  - modules/Subscription/Providers/SubscriptionServiceProvider.php
traits:
  - Repeatable
related_models: [Repetition]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract]
---

# Subscription

## Overview

The Subscription model represents a recurring financial commitment tied to a subscribable entity (via a polymorphic morph). It records the cemetery, the associated entity, a user-facing model number, start date, status, payment amount (in cents), and running total paid (in cents).

Subscriptions implement the `Repeatable` contract from the Repetition module, meaning each subscription can have one or more `Repetition` records attached that define its recurrence schedule. The `Repeatable` trait provides the `repetitions()` relationship, a `repeat()` fluent builder, and occurrence-calculation helpers. The subscription itself is the owner of the recurrence pattern; the Repetition module drives scheduling.

The model is deliberately minimal — no explicit fillable, no casts, no observers. All business logic for scheduling is delegated to the `Repeatable` trait and the Repetition module.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| subscribable_type | varchar | No | - | Polymorphic owner type |
| subscribable_id | bigint | No | - | Polymorphic owner id |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery this subscription belongs to |
| model_no | varchar | Yes | - | User-facing subscription number (unique) |
| date | date | No | - | Subscription start date |
| status | varchar | No | - | Subscription status |
| payment_amt | int | No | - | Recurring payment amount in cents |
| total_paid | int | No | - | Running total paid in cents |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `cemetery_id` → `cemeteries.id`

**Indexes:** `cemetery_id` (FK-backing); `model_no` (unique); `status` (single-column); composite index on (`subscribable_type`, `subscribable_id`).

## Casts

_None._

## Attributes

_None declared._ No explicit `$fillable`, `$guarded`, `$hidden`, `$visible`, `$appends`, or `$attributes` on the model.

## Accessors & Mutators

_None._

## Traits

- [Repeatable](../../../system/traits/index.md#repeatable) — recurrence scheduling via polymorphic `Repetition` records; `repeat()` fluent builder, date-occurrence scopes, and base-date resolution for this subscription

## Relationships

Relationships contributed by the [Repeatable](../../../system/traits/index.md#repeatable) trait:

- `repetitions()` — morphMany [Repetition](../../repetition/models/repetition.md) (`repeatable`): the recurrence schedule records for this subscription

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

Methods contributed by the [Repeatable](../../../system/traits/index.md#repeatable) trait (documented in the trait deep doc):

- `repeat(): Repeat` — fluent builder for creating or querying recurrence patterns
- `repetitionBaseDate(?RepetitionType $type = null): Carbon` — returns the date from which occurrences are computed

## Common Usage

```php
// Create a subscription tied to a payment plan
$subscription = Subscription::create([
    'subscribable_type' => PaymentPlan::class,
    'subscribable_id'   => $plan->id,
    'cemetery_id'       => $cemetery->id,
    'date'              => today(),
    'status'            => 'active',
    'payment_amt'       => 15000, // $150.00 in cents
    'total_paid'        => 0,
]);

// Attach a monthly recurrence via the Repeatable trait
$subscription->repeat()->monthly()->startingFrom($subscription->date)->save();

// Query repetitions
$schedule = $subscription->repetitions;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
