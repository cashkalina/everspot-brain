---
model: DeliveryLine
module: Delivery
table: delivery_lines
connection: tenant
primary_source: modules/Delivery/Models/DeliveryLine.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Delivery/Observers/DeliveryLineObserver.php
  - modules/Delivery/Providers/DeliveryServiceProvider.php
  - modules/Delivery/Models/Delivery.php
  - modules/Liability/Models/LiabilityLine.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [Delivery, LiabilityLine]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, financial]
---

# DeliveryLine

## Overview

The DeliveryLine model represents a single item line within a [Delivery](./delivery.md). Each line links the delivery to a specific [LiabilityLine](../../liability/models/liability-line.md) — the actual product or service being delivered — and carries an optional memo. DeliveryLine is a child of Delivery and inherits the parent's soft-delete lifecycle through its own `deleted_at` column.

The DeliveryLineObserver propagates state changes to the parent `LiabilityLine` whenever a delivery line is saved, deleted, or restored, keeping the liability tracking system in sync with delivery status changes.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| delivery_id | bigint | No | - | FK → deliveries: the parent delivery |
| liability_line_id | bigint | No | - | FK → liability_lines: the line item being delivered |
| memo | varchar | Yes | - | Optional memo for this delivery line |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `delivery_id` → `deliveries.id`; `liability_line_id` → `liability_lines.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** single-column indexes on `delivery_id`, `liability_line_id`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`

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

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — delivery lines are soft-deleted, never hard-deleted

## Relationships

- `delivery()` — belongs to [Delivery](./delivery.md): the parent delivery this line belongs to
- `liabilityLine()` — belongs to [LiabilityLine](../../liability/models/liability-line.md): the liability line item being delivered

## Scopes

_None._

## Events

_None._

## Observers

- `DeliveryLineObserver` — registered in `DeliveryServiceProvider::registerObservers()` (`DeliveryLine::observe(DeliveryLineObserver::class)`). Handles:
  - `saved` — calls `liabilityLine->updatedDelivery()` to propagate delivery changes to the liability tracking system
  - `deleted` — calls `liabilityLine->updatedDelivery()` to update liability status on line removal
  - `restored` — calls `liabilityLine->updatedDelivery()` when a soft-deleted line is restored

## Key Methods

_None._

## Common Usage

```php
// Add a line to a delivery
$line = DeliveryLine::create([
    'delivery_id'      => $delivery->id,
    'liability_line_id'=> $liabilityLine->id,
    'memo'             => 'Special handling required',
]);

// Load all lines for a delivery with their liability lines
$lines = $delivery->deliveryLines()->with('liabilityLine')->get();

// Access parent delivery
$delivery = $line->delivery;

// Access the item being delivered
$item = $line->liabilityLine;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
