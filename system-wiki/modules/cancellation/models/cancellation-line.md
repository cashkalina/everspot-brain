---
model: CancellationLine
module: Cancellation
table: cancellation_lines
connection: tenant
primary_source: modules/Cancellation/Models/CancellationLine.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Cancellation/Observers/CancellationLineObserver.php
  - modules/Cancellation/Providers/CancellationServiceProvider.php
  - modules/Cancellation/Models/Cancellation.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Recognition/Models/RecognitionArrangement.php
traits:
  - HasByUserFields
  - HasMoneyFields
  - SoftDeletes
related_models: [Cancellation, LiabilityLine, RecognitionArrangement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract]
---

# CancellationLine

## Overview

The CancellationLine model represents a single item line within a [Cancellation](./cancellation.md). Each line links the cancellation to a specific [LiabilityLine](../../liability/models/liability-line.md) — the product or service being cancelled — and records the financial amounts that were reversed: sale price, tax, and total (all stored in cents via `HasMoneyFields`).

An `is_property` flag marks lines that represent property (plots, crypts, etc.) as opposed to merchandise or services, enabling different business logic paths during the posting process. A polymorphic `recognitionArrangements()` relationship links cancelled lines to any [RecognitionArrangement](../../recognition/models/recognition-arrangement.md)s that were tied to the original sale, allowing recognition credits to be reversed alongside the cancellation.

The `CancellationLineObserver` propagates events up: on `saved`, it dispatches both `CancellationSaved` (to notify the parent cancellation) and `CancellationLineSaved`; on `deleted`, it dispatches `CancellationLineDeleted`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| cancellation_id | bigint | No | - | FK → cancellations: the parent cancellation |
| liability_line_id | bigint | No | - | FK → liability_lines: the line item being cancelled |
| is_property | tinyint | No | 0 | Whether this line represents property (vs. merchandise/service) |
| sale_price | int | No | - | Original sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| tax | int | No | - | Tax amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| total | int | No | - | Line total in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| memo | varchar | Yes | - | Optional memo for this line |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `cancellation_id` → `cancellations.id`; `liability_line_id` → `liability_lines.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** single-column indexes on `cancellation_id`, `liability_line_id`, `total`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`

## Casts

_None._

<!-- trait-contributed casts (HasMoneyFields transparent cents conversion) are documented in the trait doc, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes (via HasMoneyFields):**
```php
public $moneyAttributes = ['sale_price', 'tax', 'total'];
```
These columns store values in cents but are read and written in dollars through the trait's transparent conversion.

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `sale_price`, `tax`, and `total`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — cancellation lines are soft-deleted, never hard-deleted

## Relationships

- `cancellation()` — belongs to [Cancellation](./cancellation.md): the parent cancellation this line belongs to
- `liabilityLine()` — belongs to [LiabilityLine](../../liability/models/liability-line.md): the liability line item being cancelled
- `recognitionArrangements()` — morphMany [RecognitionArrangement](../../recognition/models/recognition-arrangement.md) (`cancellable`): recognition arrangements linked to this cancellation line for reversal

## Scopes

_None._

## Events

_None defined on the model._ The `CancellationLineObserver` dispatches events on save and delete (see Observers).

## Observers

- `CancellationLineObserver` — registered in `CancellationServiceProvider::registerObservers()` (`CancellationLine::observe(CancellationLineObserver::class)`). Handles:
  - `saved` — dispatches `CancellationSaved` (passing the parent cancellation) and `CancellationLineSaved`
  - `deleted` — dispatches `CancellationLineDeleted`

## Key Methods

_None._

## Common Usage

```php
// Add a line to a cancellation
$line = CancellationLine::create([
    'cancellation_id'  => $cancellation->id,
    'liability_line_id'=> $liabilityLine->id,
    'is_property'      => false,
    'sale_price'       => 150.00,   // stored as cents internally
    'tax'              => 12.00,
    'total'            => 162.00,
]);

// Load lines for a cancellation with liability lines
$lines = $cancellation->cancellationLines()->with('liabilityLine')->get();

// Check if line is a property line
if ($line->is_property) {
    // handle property reversal
}

// Access totals (transparent dollar conversion)
echo $line->total;       // "162.00" (dollars)
echo $line->sale_price;  // "150.00" (dollars)
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
