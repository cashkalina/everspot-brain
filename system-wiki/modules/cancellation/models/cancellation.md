---
model: Cancellation
module: Cancellation
table: cancellations
connection: tenant
primary_source: modules/Cancellation/Models/Cancellation.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Cancellation/Observers/CancellationObserver.php
  - modules/Cancellation/Providers/CancellationServiceProvider.php
  - modules/Cancellation/Models/CancellationLine.php
  - modules/Commission/Models/RepAssociation.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/Note.php
traits:
  - HasApprovals
  - HasByUserFields
  - HasFiles
  - HasModelNumbering
  - HasMoneyFields
  - HasSearch
related_models: [CancellationLine, Cemetery, Note, RepAssociation]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract, transaction]
---

# Cancellation

## Overview

The Cancellation model records the reversal of a prior sale — unbinding liability lines from their fulfilled state and returning them to the available or voided pool. Each Cancellation belongs to a cemetery, has a cancellation date and an optional original sale date, and progresses through `pending → posted → voided` statuses.

Financial totals (`sub_total`, `tax_total`, `total`) are stored in cents as integers and transparently converted to dollars via the `HasMoneyFields` trait, which respects the `$moneyAttributes` declaration. Posted cancellations trigger the `PostCancellation` action via `onApprovalRequestApproval()`, integrating with the approval workflow.

The model carries file attachments via `HasFiles`, search indexing via `HasSearch`, model numbering via `HasModelNumbering`, and audit user stamps via `HasByUserFields`. It links to commission representative associations via a polymorphic `repAssociations()` relationship (morph type `repable`), enabling commission credit or chargeback tracking for the cancellation.

The `CancellationObserver` dispatches a `CancellationSaved` event on every save, and `PreDeleteCancellation` runs in a transaction on delete. Unlike `Delivery`, this model does not use `SoftDeletes` — cancellations are hard-deleted (no `deleted_at` column in the schema).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_no | varchar | Yes | - | User-facing cancellation number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| cemetery_id | bigint | No | - | FK → cemeteries: the owning cemetery |
| date | date | No | - | Date of the cancellation |
| status | varchar | No | - | Lifecycle status (`pending`, `posted`, `voided`) |
| sub_total | int | No | - | Subtotal in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| tax_total | int | No | - | Tax total in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| total | int | No | - | Grand total in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| sale_date | date | Yes | - | Original sale date (optional reference to the sale being cancelled) |
| no_comm_sale | tinyint | No | 0 | Whether the original sale was a no-commission sale |
| memo | varchar | Yes | - | Optional memo or notes |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** unique index on `model_no`; single-column indexes on `cemetery_id`, `date`, `status`, `total`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`

## Casts

- `date` → `date`
- `sale_date` → `date`
- `no_comm_sale` → `boolean`

<!-- trait-contributed casts (HasMoneyFields transparent cents conversion) are documented in the trait doc, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes (via HasMoneyFields):**
```php
public $moneyAttributes = ['total', 'tax_total', 'sub_total'];
```
These columns store values in cents but are read and written in dollars through the trait's transparent conversion.

**Constants:**
```php
const STATUSES = [
    'pending' => ['label' => 'Pending', 'color' => 'warning'],
    'posted'  => ['label' => 'Posted',  'color' => 'success'],
    'voided'  => ['label' => 'Voided',  'color' => 'secondary'],
];
```

## Accessors & Mutators

_None._

## Traits

- [HasApprovals](../../../system/traits/index.md#hasapprovals) — internal approval workflow; approval triggers `onApprovalRequestApproval()` which posts the cancellation
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments (this model implements `HasMedia`)
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `total`, `tax_total`, and `sub_total`
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing via Laravel Scout

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery this cancellation belongs to
- `cancellationLines()` — has many [CancellationLine](./cancellation-line.md): the individual line items being cancelled
- `repAssociations()` — morphMany [RepAssociation](../../commission/models/rep-association.md) (`repable`): commission representative associations for this cancellation
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): notes attached to this cancellation

## Scopes

_None._

## Events

_None defined on the model._ The `CancellationObserver` dispatches `CancellationSaved` on every save (see Observers).

## Observers

- `CancellationObserver` — registered in `CancellationServiceProvider::registerObservers()` (`Cancellation::observe(CancellationObserver::class)`). Handles:
  - `saved` — dispatches `CancellationSaved` event
  - `deleting` — wraps deletion in a DB transaction and runs `PreDeleteCancellation` action

## Key Methods

- `onApprovalRequestApproval(): void` — called by the approval trait when an approval request is approved; executes `PostCancellation` action to post the cancellation
- `getQuickApproveActionName(): string` — returns `'Post Cancellation'`; the label shown on the quick-approve button in the UI

## Common Usage

```php
// Create a pending cancellation
$cancellation = Cancellation::create([
    'cemetery_id' => $cemetery->id,
    'date'        => today(),
    'status'      => 'pending',
    'sub_total'   => 150.00,  // stored as cents internally
    'tax_total'   => 12.00,
    'total'       => 162.00,
]);

// Add a line item
$cancellation->cancellationLines()->create([
    'liability_line_id' => $liabilityLine->id,
    'sale_price'        => 150.00,
    'tax'               => 12.00,
    'total'             => 162.00,
]);

// Get all notes
$notes = $cancellation->notes()->get();

// Access totals (transparent dollar conversion)
echo $cancellation->total;     // "162.00" (dollars)
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
