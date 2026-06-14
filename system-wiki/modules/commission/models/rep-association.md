---
model: RepAssociation
module: Commission
table: rep_associations
connection: tenant
primary_source: modules/Commission/Models/RepAssociation.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Commission/Observers/RepAssociationObserver.php
  - modules/Commission/Providers/CommissionServiceProvider.php
  - modules/Common/Models/User.php
  - modules/Commission/Models/CommissionCalculation.php
traits:
  - HasByUserFields
related_models: [CommissionCalculation, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, commission]
---

# RepAssociation

## Overview

The RepAssociation model links a sales representative ([User](../../../system/models/user.md)) to a saleable entity (via a polymorphic `repable` relationship — e.g. an order or liability line). It captures how the rep is involved in a sale: whether they are the primary rep (`is_primary`), an additional rep (`is_additional`), their contribution percentage share (`contribution_pct`), and whether commissions are enabled for this association (`enable_commissions`).

RepAssociation is the bridge between "who sold what" and the commission calculation engine. When a `RepAssociation` exists on a saleable record, the commission module uses it (along with the applicable [CommissionPlan](./commission-plan.md) and [CommissionRate](./commission-rate.md)) to create [CommissionCalculation](./commission-calculation.md) records that track what is owed. Multiple reps can be associated to a single sale (primary + additional).

The `RepAssociationObserver` enforces a business rule on `saving`: if the `repable` entity has `no_comm_sale = true`, commissions are automatically disabled for this association (`enable_commissions = false`), preventing commission generation on sales that are marked non-commissionable.

Note: `RepAssociation` does NOT use `SoftDeletes` — rows are hard-deleted. It also has no `deleted_at` column in the schema.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| repable_type | varchar | No | - | Polymorphic type of the associated saleable entity |
| repable_id | bigint | No | - | Polymorphic ID of the associated saleable entity |
| user_id | bigint | No | - | FK → users: the sales rep |
| contribution_pct | decimal | No | - | Rep's contribution percentage share of the sale |
| is_primary | tinyint | No | 0 | Whether this rep is the primary rep on the sale |
| enable_commissions | tinyint | No | 1 | Whether commissions are enabled for this rep association |
| is_additional | tinyint | No | 0 | Whether this rep is an additional (non-primary) rep |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `user_id` → `users.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** composite index on `(repable_type, repable_id)`; index on `user_id`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Note:** No `deleted_at` column — this model does NOT use soft deletes.

## Casts

- `is_primary` → `boolean`
- `enable_commissions` → `boolean`
- `is_additional` → `boolean`

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

## Relationships

- `repable()` — morphTo: the parent saleable entity (concrete type varies — e.g. an order or liability line)
- `user()` — belongs to [User](../../../system/models/user.md) (`user_id`): the sales representative
- `commissionCalculations()` — has many [CommissionCalculation](./commission-calculation.md) (`rep_association_id`): all commission calculations generated from this rep association

## Scopes

_None._

## Events

_None._

## Observers

- `RepAssociationObserver` — registered in `CommissionServiceProvider::registerObservers()` (`RepAssociation::observe(RepAssociationObserver::class)`). Handles:
  - `saving` — if `repable->no_comm_sale` is `true`, sets `enable_commissions = false` on the association before save, preventing commission generation on non-commissionable sales

## Key Methods

_None beyond standard Eloquent methods._

## Common Usage

```php
// Associate a rep with a sale
$repAssoc = RepAssociation::create([
    'repable_type'    => Order::class,
    'repable_id'      => $order->id,
    'user_id'         => $rep->id,
    'contribution_pct'=> 100.00,
    'is_primary'      => true,
    'enable_commissions' => true,
    'is_additional'   => false,
]);

// Retrieve all commission calculations for this rep-sale link
$calculations = $repAssoc->commissionCalculations;

// Check if commissions are enabled
if ($repAssoc->enable_commissions) {
    // proceed with commission calculation
}

// Access the parent saleable entity polymorphically
$sale = $repAssoc->repable; // Order, LiabilityLine, etc.
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
