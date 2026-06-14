---
model: RecognitionApproval
module: Recognition
table: recognition_approvals
connection: tenant
primary_source: modules/Recognition/Models/RecognitionApproval.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Recognition/Observers/RecognitionApprovalObserver.php
  - modules/Recognition/Providers/RecognitionServiceProvider.php
  - modules/Recognition/Models/RecognitionElement.php
traits:
  - HasByUserFields
related_models: [RecognitionElement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, admin]
---

# RecognitionApproval

## Overview

The `RecognitionApproval` model represents a batch approval record for a set of revenue recognition elements. When recognition elements are ready for posting, they are grouped under an approval record that captures the approval date, an as-of accounting date, and an optional memo. Only elements linked to an approved batch can progress to the posted (journal-entry-generated) state.

Approvals act as the authorization gate in the recognition workflow: the finance team reviews a batch of `RecognitionElement` records, groups them under a `RecognitionApproval`, and that association signals that the elements may be posted to the general ledger. The model carries audit user stamps via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) and uses a default status of `pending` (inherited from `BaseModel::$defaultStatus`). Deletion of an approval dispatches `RecognitionApprovalDeleting` to allow dependent elements to react before the record is removed.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| date | date | No | - | Approval date |
| as_of_date | date | No | - | Accounting as-of date for the approval batch |
| memo | varchar | Yes | - | Optional descriptive memo for the batch |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Note:** This table does not have a `deleted_at` column in the schema snapshot. Despite the model using `HasByUserFields` (which includes `deleted_by`), the approval record itself is not soft-deleted — it is hard-deleted, with the `deleting` lifecycle event dispatched to dependent elements via the observer.

## Casts

- `date` → `date`
- `as_of_date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ (`$defaultStatus = 'pending'` inherited from `BaseModel` but not surfaced as a column default here)

## Accessors & Mutators

- `getTotalAmountAttribute(): float` — sums the `amt` values of all related `recognitionElements` and returns the total as a float (in cents; use `fromCents()` to convert to dollars for display)

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)

## Relationships

- `recognitionElements()` — has many [RecognitionElement](./recognition-element.md): all recognition elements grouped under this approval batch

## Scopes

_None._

## Events

_None defined on the model._

## Observers

- `RecognitionApprovalObserver` — registered in `RecognitionServiceProvider::registerObservers()` (`RecognitionApproval::observe(RecognitionApprovalObserver::class)`). Handles:
  - `deleting` — dispatches `RecognitionApprovalDeleting` event to notify dependents before the approval record is removed
  - `created`, `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs

## Key Methods

_None beyond standard Eloquent and the `total_amount` accessor._

## Common Usage

```php
// Create an approval batch
$approval = RecognitionApproval::create([
    'date'        => today(),
    'as_of_date'  => today()->startOfMonth(),
    'memo'        => 'Q2 revenue recognition batch',
]);

// Attach elements to the approval
RecognitionElement::whereIn('id', $elementIds)->update([
    'recognition_approval_id' => $approval->id,
]);

// Check total amount for the batch (in cents)
$totalCents = $approval->total_amount;

// Eager load with elements
$approval->load('recognitionElements');
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
