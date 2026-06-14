---
model: CommissionApproval
module: Commission
table: commission_approvals
connection: tenant
primary_source: modules/Commission/Models/CommissionApproval.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Commission/Models/Commission.php
traits:
  - SoftDeletes
  - HasMoneyFields
  - HasByUserFields
  - HasSearch
related_models: [Commission]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, commission]
---

# CommissionApproval

## Overview

The CommissionApproval model represents a batched approval event that releases a group of commission payouts to sales representatives. When a manager reviews and approves a set of commissions, a single `CommissionApproval` record is created capturing the approval `date`, an `as_of_date` (the cutoff date for commissions included in the batch), and an optional `memo`. The individual [Commission](./commission.md) records issued under the batch each carry a `commission_approval_id` foreign key back to this record.

The model provides a `total` accessor that dynamically sums the `amt` values of all related `Commission` records, giving a quick aggregate view of the approval batch's total payout value. CommissionApproval carries soft deletes, audit user stamps, money-field handling (via `HasMoneyFields`, though `amt` is not a stored column — it applies to aggregate views), and Scout search indexing via `HasSearch`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| date | date | No | - | Date this approval was issued |
| as_of_date | date | No | - | Cutoff date — commissions earned up to this date are included |
| memo | varchar | Yes | - | Optional approval memo or notes |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** regular indexes on `date`, `as_of_date`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `date`
- `as_of_date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getTotalAttribute(): float` — dynamically sums the `amt` values of all related `commissions`; represents the total payout value of this approval batch

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — approval records are soft-deleted, never hard-deleted
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — money-field conversion helpers (no stored money column on this model; applied for consistency with the commission module)
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasSearch](../../../system/traits/index.md#hassearch) — Scout search indexing for approval records

## Relationships

- `commissions()` — has many [Commission](./commission.md) (`commission_approval_id`): all commission payouts released under this approval batch

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None beyond standard Eloquent methods._

## Common Usage

```php
// Create an approval batch
$approval = CommissionApproval::create([
    'date'        => now()->toDateString(),
    'as_of_date'  => now()->startOfMonth()->toDateString(),
    'memo'        => 'Q2 commission batch',
]);

// Retrieve the total payout value for the batch
echo $approval->total; // float — sum of all commission amts in dollars

// List all commissions in this batch
$commissions = $approval->commissions;

// Soft-delete an approval
$approval->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
