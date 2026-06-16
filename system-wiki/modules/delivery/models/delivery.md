---
model: Delivery
module: Delivery
table: deliveries
connection: tenant
primary_source: modules/Delivery/Models/Delivery.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Delivery/Observers/DeliveryObserver.php
  - modules/Delivery/Providers/DeliveryServiceProvider.php
  - modules/Delivery/Models/DeliveryLine.php
  - modules/Common/Models/Address.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/User.php
traits:
  - HasApprovals
  - HasByUserFields
  - HasExternalApprovals
  - HasFiles
  - HasModelNumbering
  - HasSchemalessAttributes
  - HasSearch
  - SoftDeletes
related_models: [Address, Cemetery, DeliveryLine, Note, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, financial, contract]
---

# Delivery

## Overview

The Delivery model records the transfer of goods from Everspot's inventory to their destination — either directly to a customer (`is_constructive = false`) or into storage/constructive receipt (`is_constructive = true`). Deliveries are associated with a cemetery, have a delivery date, and progress through a lifecycle of `pending → posted → voided` statuses.

Each Delivery aggregates one or more [DeliveryLine](./delivery-line.md) records, each of which links to a specific [LiabilityLine](../../liability/models/liability-line.md) — the item being delivered. A single delivery address (morphOne [Address](../../common/models/address.md)) may be attached for direct-to-customer deliveries.

The model participates in the approval workflow (via `HasApprovals` and `HasExternalApprovals`): when an approval request is approved, `onApprovalRequestApproval()` is called, which posts the delivery. `getQuickApproveActionName()` returns the label `'Post Delivery'` used in the UI quick-approve button. The model also carries file attachments (Spatie MediaLibrary via `HasFiles`), schemaless config (`HasSchemalessAttributes`), search indexing (`HasSearch`), model numbering (`HasModelNumbering`), audit user stamps (`HasByUserFields`), and soft deletes.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_no | varchar | Yes | - | User-facing delivery number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| cemetery_id | bigint | No | - | FK → cemeteries: the owning cemetery |
| agent_user_id | bigint | Yes | - | FK → users: the agent responsible for the delivery |
| date | date | No | - | Delivery date |
| status | varchar | No | - | Lifecycle status (`pending`, `posted`, `voided`) |
| memo | varchar | Yes | - | Optional memo or notes |
| is_constructive | tinyint | No | 0 | Whether this is a constructive receipt (to storage) rather than direct delivery to customer |
| config_data | json | Yes | - | Schemaless config data (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `agent_user_id` → `users.id`; `cemetery_id` → `cemeteries.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** unique index on `model_no`; single-column indexes on `cemetery_id`, `agent_user_id`, `date`, `memo`, `status`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`

## Casts

- `date` → `date`
- `is_constructive` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants:**
```php
const STATUSES = [
    'pending' => ['label' => 'Pending', 'color' => 'warning'],
    'posted'  => ['label' => 'Posted',  'color' => 'success'],
    'voided'  => ['label' => 'Voided',  'color' => 'secondary'],
];
```

## Accessors & Mutators

- `getDeliveryTypeAttribute(): string` — returns `'To Storage'` when `is_constructive` is true, otherwise `'To Customer'`

## Traits

- [HasApprovals](../../../system/traits/index.md#hasapprovals) — internal approval workflow; approval triggers `onApprovalRequestApproval()` which posts the delivery
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasExternalApprovals](../../../system/traits/index.md#hasexternalapprovals) — external approval workflow for deliveries requiring out-of-system sign-off
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments (this model implements `HasMedia`)
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` JSON column with dot-notation access for arbitrary key-value config
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing via Laravel Scout
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — deliveries are soft-deleted, never hard-deleted

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery this delivery belongs to
- `agentUser()` — belongs to [User](../../common/models/user.md) (`agent_user_id`): the agent user responsible for the delivery
- `deliveryLines()` — has many [DeliveryLine](./delivery-line.md): the individual line items being delivered
- `deliveryAddress()` — morphOne [Address](../../common/models/address.md) (`addressable`): the delivery destination address
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): notes attached to this delivery

## Scopes

_None._

## Events

_None._

## Observers

- `DeliveryObserver` — registered in `DeliveryServiceProvider::registerObservers()` (`Delivery::observe(DeliveryObserver::class)`). Handles:
  - `created` — fires `analytics()->track('Delivery Created')`
  - `updated` — iterates `deliveryLines` and calls `liabilityLine->updatedDelivery()` on each to propagate delivery-status changes to liability tracking
  - `deleting` — wraps deletion in a DB transaction and runs `PreDeleteDelivery` action

## Key Methods

- `onApprovalRequestApproval(): void` — called by the approval trait when an approval request is approved; transitions the delivery to `posted` status via `$this->toPosted()`
- `getQuickApproveActionName(): string` — returns `'Post Delivery'`; the label shown on the quick-approve button in the UI

## Common Usage

```php
// Create a pending delivery
$delivery = Delivery::create([
    'cemetery_id'    => $cemetery->id,
    'agent_user_id'  => auth()->id(),
    'date'           => today(),
    'status'         => 'pending',
    'is_constructive'=> false,
]);

// Add a line item
$delivery->deliveryLines()->create([
    'liability_line_id' => $liabilityLine->id,
]);

// Check delivery type
echo $delivery->delivery_type; // "To Customer" or "To Storage"

// Get all notes
$notes = $delivery->notes()->get();
```

## Imports

This model can be created/updated via spreadsheet import. See **[delivery](../imports/delivery.md)** for the column reference (valid headers, required fields, types, and conditional rules).

The import mechanism (upload → queued job → Excel) is documented in the [import subsystem](../../../system/imports.md).

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
