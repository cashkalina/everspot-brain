---
model: RecognitionArrangement
module: Recognition
table: recognition_arrangements
connection: tenant
primary_source: modules/Recognition/Models/RecognitionArrangement.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Recognition/Observers/RecognitionArrangementObserver.php
  - modules/Recognition/Providers/RecognitionServiceProvider.php
  - modules/Recognition/Models/RecognitionElement.php
  - modules/Accounting/Models/GlAccount.php
  - modules/Accounting/Models/JournalEntry.php
traits:
  - HasMoneyFields
  - SoftDeletes
related_models: [GlAccount, JournalEntry, RecognitionElement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction]
---

# RecognitionArrangement

## Overview

The `RecognitionArrangement` model is the central record for a revenue or expense recognition workflow attached to a source entity (the "recognizable"). Each arrangement captures the rule-based configuration and real-time state of a single recognition obligation: what type of recognition is required (revenue, expense, commission, or tax), which trigger conditions activate it, what the sale price and AR-paid amount are, and how far along the deferral-to-recognition lifecycle has progressed.

Arrangements are polymorphic through `recognizable` — any model using the [HasRecognition](../../../system/traits/index.md#hasrecognition) trait can own one or more arrangements. A second polymorphic pointer, `cancellable`, records the entity that triggered a cancellation when the arrangement is cancelled. Three general-ledger accounts (`deferral_account_id`, `recognition_account_id`, `offset_account_id`) and an optional `deferral_journal_entry_id` tie the arrangement to the accounting module.

As elements are posted against the arrangement, `recognized_amt` is updated via `updatedElement()`. When the recognizable entity changes its key date fields or AR-paid amount, `updatedRecognizable()` propagates those changes to the arrangement. Soft deletes ensure that historical arrangements are retained when cancelled or superseded.

**Status lifecycle:** `not-triggered` → `awaiting-element` → `in-progress` → `completed`. The default status on creation is `not-triggered`.

**Money columns** (`ar_paid_amt`, `sale_price`, `deferred_amt`, `recognized_amt`) are stored as integer cents and transparently converted by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| recognizable_type | varchar | No | - | Polymorphic type of the owning entity (morph map value) |
| recognizable_id | bigint | No | - | Polymorphic ID of the owning entity |
| type | varchar | No | - | Recognition type: `revenue`, `expense`, `commission`, or `tax` |
| status | varchar | No | - | Lifecycle status: `not-triggered`, `awaiting-element`, `in-progress`, `completed` |
| trigger | json | No | - | Trigger condition configuration (array: event that activates the arrangement) |
| sale_date | date | Yes | - | Date of the originating sale |
| constructive_date | date | Yes | - | Constructive receipt date |
| delivery_date | date | Yes | - | Delivery / performance-completion date |
| cancellation_date | date | Yes | - | Date the arrangement was cancelled |
| certificate_issuance_date | date | Yes | - | Date of certificate issuance |
| ar_paid_amt | int | No | 0 | AR-paid amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| sale_price | int | No | 0 | Original sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| rule | json | No | - | Serialized recognition rule configuration (snapshot of the rule at arrangement creation) |
| deferral_journal_entry_id | bigint | Yes | - | FK → journal_entries: the journal entry that recorded the initial deferral |
| deferral_account_id | bigint | No | - | FK → gl_accounts: the deferred-revenue/liability GL account |
| offset_account_id | bigint | No | - | FK → gl_accounts: the offset (AR or cash) GL account |
| recognition_account_id | bigint | No | - | FK → gl_accounts: the revenue/expense recognition GL account |
| deferred_amt | int | No | 0 | Remaining deferred amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| recognized_amt | int | No | 0 | Total recognized amount in cents, updated as elements are posted (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| cancellable_type | varchar | Yes | - | Polymorphic type of the entity that triggered cancellation |
| cancellable_id | bigint | Yes | - | Polymorphic ID of the cancelling entity |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `deferral_journal_entry_id` → `journal_entries.id`; `deferral_account_id`, `recognition_account_id`, `offset_account_id` → `gl_accounts.id`

**Indexes:** composite index on (`recognizable_type`, `recognizable_id`); single-column index on `status`; FK-backing indexes on `deferral_account_id`, `deferral_journal_entry_id`, `offset_account_id`, `recognition_account_id`.

## Casts

- `trigger` → `array` — JSON-encoded trigger configuration
- `rule` → `array` — JSON-encoded recognition rule snapshot
- `sale_date` → `date`
- `delivery_date` → `date`
- `cancellation_date` → `date`
- `certificate_issuance_date` → `date`

**Note:** The model class also declares `'date' => 'date'` in `$casts`, but there is no `date` column in the schema snapshot. This cast entry appears to be a leftover from a prior migration and is functionally inert.

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ (`$defaultStatus = 'not-triggered'` is a static class property used by the status system, not a column default)

**Constants / static config:**
```php
const STATUSES = [
    'not-triggered'   => ['label' => 'Not Triggered',    'badge_label' => 'Deferred',     'color' => 'warning'],
    'awaiting-element'=> ['label' => 'Awaiting Element', 'badge_label' => 'Deferred',     'color' => 'warning'],
    'in-progress'     => ['label' => 'In Progress',      'badge_label' => 'In Progress',  'color' => 'info'],
    'completed'       => ['label' => 'Completed',        'badge_label' => 'Recognized',   'color' => 'secondary'],
];
const TYPES = [
    'revenue'    => 'Revenue',
    'expense'    => 'Expense',
    'commission' => 'Commission',
    'tax'        => 'Tax',
];
public $moneyAttributes = ['ar_paid_amt', 'sale_price', 'deferred_amt', 'recognized_amt'];
```

## Accessors & Mutators

- `getFormattedTypeAttribute(): string` — human-readable type label from `TYPES` constant (e.g. `'revenue'` → `'Revenue'`)
- `getStatusBadgeAttribute(): string` — Bootstrap badge HTML using `STATUSES` color/badge_label for the current `status`
- `getDeferralStatusAttribute(): string` — `'Completed'` if `deferral_journal_entry_id` is set, otherwise `'Not Started'`
- `getRecognitionStatusAttribute(): string` — `'In Progress'` / `'Completed'` / `'Not Started'` derived from `isInProgress()` / `isCompleted()` status-checker methods (provided by `BaseModel`'s dynamic status system reading `STATUSES`)

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `ar_paid_amt`, `sale_price`, `deferred_amt`, and `recognized_amt`; provides `fromCents()` and `toCents()` helpers
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — arrangements are soft-deleted (`deleted_at`), preserving historical records

## Relationships

- `recognizable()` — morphTo: the source entity that owns this arrangement (may be any model implementing [HasRecognition](../../../system/traits/index.md#hasrecognition), e.g. an order line or contract)
- `cancellable()` — morphTo: the entity that triggered cancellation of this arrangement (e.g. a cancellation record)
- `recognitionElements()` — has many [RecognitionElement](./recognition-element.md): all individual recognition postings generated against this arrangement
- `deferralJournalEntry()` — belongs to [JournalEntry](../../accounting/models/journal-entry.md) (`deferral_journal_entry_id`): the journal entry recording the initial deferral
- `deferralAccount()` — belongs to [GlAccount](../../accounting/models/gl-account.md) (`deferral_account_id`): the deferred-revenue GL account
- `recognitionAccount()` — belongs to [GlAccount](../../accounting/models/gl-account.md) (`recognition_account_id`): the revenue/expense recognition GL account
- `offsetAccount()` — belongs to [GlAccount](../../accounting/models/gl-account.md) (`offset_account_id`): the offset (AR or cash) GL account

## Scopes

_None._

## Events

_None defined on the model._

## Observers

- `RecognitionArrangementObserver` — registered in `RecognitionServiceProvider::registerObservers()` (`RecognitionArrangement::observe(RecognitionArrangementObserver::class)`). Handles:
  - `saved` — dispatches `RecognitionArrangementSaved` event
  - `created` — dispatches `RecognitionArrangementCreated` event
  - `deleting` — dispatches `RecognitionArrangementDeleting` event
  - `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs

## Key Methods

- `updatedRecognizable($model): void` — synchronizes date fields and `ar_paid_amt` from the recognizable entity onto this arrangement; saves only if dirty. Called by the [HasRecognition](../../../system/traits/index.md#hasrecognition) trait when the parent entity changes.
- `updatedElement(): void` — recalculates `recognized_amt` by summing `amt` from all posted elements (`journal_entry_id` is not null); saves only if dirty. Called after a `RecognitionElement` is saved.

## Common Usage

```php
// Retrieve all arrangements for a recognizable entity
$arrangements = $orderLine->recognitionArrangements;

// Check the current status
if ($arrangement->isInProgress()) {
    // elements have been partially posted
}

// Display labels
echo $arrangement->formatted_type;  // "Revenue"
echo $arrangement->status_badge;    // HTML badge

// After posting a new element, update the recognized total
$arrangement->updatedElement();

// Sync dates from the parent recognizable
$arrangement->updatedRecognizable($orderLine);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
