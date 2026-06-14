---
model: Commission
module: Commission
table: commissions
connection: tenant
primary_source: modules/Commission/Models/Commission.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Commission/Observers/CommissionObserver.php
  - modules/Commission/Providers/CommissionServiceProvider.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Commission/Models/CommissionCalculation.php
  - modules/Commission/Models/CommissionApproval.php
  - modules/Recognition/Models/RecognitionArrangement.php
  - modules/Common/Models/User.php
traits:
  - SoftDeletes
  - HasMoneyFields
  - HasModelNumbering
  - HasByUserFields
related_models: [CommissionApproval, CommissionCalculation, LiabilityLine, RecognitionArrangement, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, commission]
---

# Commission

## Overview

The Commission model represents an individual commission payment disbursed to a sales representative. Each Commission record captures a specific monetary payout (`amt`) on a specific `date`, tied to a [LiabilityLine](../../liability/models/liability-line.md) (the underlying sale), a [User](../../../system/models/user.md) (the rep receiving the commission), a [CommissionCalculation](./commission-calculation.md) (the calculation that determined the commission was owed), and a [CommissionApproval](./commission-approval.md) (the approval batch under which it was released).

Commissions are the leaf-level records in the commission lifecycle: after a sale occurs a `CommissionCalculation` determines what is owed; when an approver batches and releases payouts, individual `Commission` rows are created under a `CommissionApproval`. The optional link to a `RecognitionArrangement` supports cases where the commission is tied to a recognition-module arrangement rather than a direct order line.

The model carries soft deletes, audit user stamps, a user-facing model number (`model_no`), and transparent money handling for the `amt` column (stored as integer cents, exposed as dollars via `HasMoneyFields`). The `CommissionObserver` dispatches lifecycle events on save, create, and delete.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| liability_line_id | bigint | No | - | FK → liability_lines: the sale line this commission is for |
| user_id | bigint | No | - | FK → users: the rep receiving this commission |
| commission_calculation_id | bigint | No | - | FK → commission_calculations: the calculation that produced this payout |
| commission_approval_id | bigint | No | - | FK → commission_approvals: the approval batch that released this commission |
| recognition_arrangement_id | bigint | Yes | - | FK → recognition_arrangements: optional link to a recognition arrangement |
| model_no | varchar | Yes | - | User-facing commission number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| date | date | No | - | Date of the commission payment |
| amt | int | No | - | Commission amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — exposed as dollars) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `liability_line_id` → `liability_lines.id`; `user_id` → `users.id`; `commission_calculation_id` → `commission_calculations.id`; `commission_approval_id` → `commission_approvals.id`; `recognition_arrangement_id` → `recognition_arrangements.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** unique index on `model_no`; regular indexes on `commission_approval_id`, `commission_calculation_id`, `liability_line_id`, `user_id`; FK-backing indexes on `recognition_arrangement_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['amt']` — `amt` is stored as integer cents and transparently converted to/from dollars via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — commissions are soft-deleted (`deleted_at`), never hard-deleted
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `amt`
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` record number
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps

## Relationships

- `liabilityLine()` — belongs to [LiabilityLine](../../liability/models/liability-line.md) (`liability_line_id`): the sale line this commission is for
- `user()` — belongs to [User](../../../system/models/user.md) (`user_id`): the sales rep receiving this commission
- `commissionCalculation()` — belongs to [CommissionCalculation](./commission-calculation.md) (`commission_calculation_id`): the calculation that determined this payout
- `commissionApproval()` — belongs to [CommissionApproval](./commission-approval.md) (`commission_approval_id`): the approval batch that released this commission
- `recognitionArrangement()` — belongs to [RecognitionArrangement](../../recognition/models/recognition-arrangement.md) (`recognition_arrangement_id`): optional recognition arrangement link

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle events are dispatched by `CommissionObserver` (see Observers).

## Observers

- `CommissionObserver` — registered in `CommissionServiceProvider::registerObservers()` (`Commission::observe(CommissionObserver::class)`). Handles:
  - `saved` — dispatches `CommissionSaved` event
  - `created` — dispatches `CommissionCreated` event
  - `deleting` — dispatches `CommissionDeleting` event (before deletion)
  - `deleted` — dispatches `CommissionDeleted` event
  - `forceDeleted` — dispatches `CommissionDeleted` event

## Key Methods

_None beyond trait-contributed and standard Eloquent methods._

## Common Usage

```php
// Create a commission payout
$commission = Commission::create([
    'liability_line_id'          => $liabilityLine->id,
    'user_id'                    => $rep->id,
    'commission_calculation_id'  => $calculation->id,
    'commission_approval_id'     => $approval->id,
    'date'                       => now()->toDateString(),
    'amt'                        => 250.00, // stored as 25000 cents
]);

// Retrieve commissions for a specific rep
$repCommissions = Commission::where('user_id', $rep->id)->get();

// Retrieve commissions under an approval batch
$batchCommissions = CommissionApproval::find($approvalId)->commissions;

// Soft-delete a commission
$commission->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
