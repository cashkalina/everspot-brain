---
model: RecognitionElement
module: Recognition
table: recognition_elements
connection: tenant
primary_source: modules/Recognition/Models/RecognitionElement.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Recognition/Observers/RecognitionElementObserver.php
  - modules/Recognition/Providers/RecognitionServiceProvider.php
  - modules/Recognition/Models/RecognitionArrangement.php
  - modules/Recognition/Models/RecognitionApproval.php
  - modules/Accounting/Models/JournalEntry.php
traits:
  - HasMoneyFields
related_models: [JournalEntry, RecognitionApproval, RecognitionArrangement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction]
---

# RecognitionElement

## Overview

The `RecognitionElement` model represents a single discrete recognition event within a `RecognitionArrangement`. Where an arrangement captures the overall obligation and lifecycle, an element captures a specific posting: the date, amount, approval status, and the resulting journal entry once posted to the general ledger.

Elements progress through three sequential states gated by business rules:

1. **Not ready** — `is_ready = false`; the element has been created but not yet marked as ready for approval (typically waiting on a scheduled job or manual trigger).
2. **Ready, awaiting approval** — `is_ready = true`, `recognition_approval_id = null`; the element is eligible for inclusion in an approval batch.
3. **Approved, awaiting posting** — `recognition_approval_id` is set; the element has been approved and can be posted.
4. **Posted** — `journal_entry_id` is set; the journal entry has been created and the amount has been recognized in the GL.

The element also carries a polymorphic `recognizable` pointer, mirroring the arrangement's pointer to the source entity. This redundancy allows elements to be queried directly by source entity without loading the parent arrangement. The `amt` column is stored as integer cents, transparently converted by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| recognition_arrangement_id | bigint | No | - | FK → recognition_arrangements: the parent arrangement |
| recognizable_type | varchar | No | - | Polymorphic type of the source entity (mirrors arrangement's recognizable) |
| recognizable_id | bigint | No | - | Polymorphic ID of the source entity |
| recognition_approval_id | bigint | Yes | - | FK → recognition_approvals: the approval batch this element belongs to (null until approved) |
| journal_entry_id | bigint | Yes | - | FK → journal_entries: the GL journal entry once posted (null until posted) |
| date | date | No | - | Recognition date for this element |
| amt | int | No | 0 | Recognition amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| is_ready | tinyint | No | 0 | Whether this element is ready for approval (`1` = ready) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `recognition_arrangement_id` → `recognition_arrangements.id`; `recognition_approval_id` → `recognition_approvals.id`; `journal_entry_id` → `journal_entries.id`

**Indexes:** single-column indexes on `is_ready`, `recognition_approval_id`, `recognition_arrangement_id`; composite index on (`recognizable_type`, `recognizable_id`); FK-backing index on `journal_entry_id`.

## Casts

- `date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:**
```php
public array $moneyAttributes = ['amt'];
```

## Accessors & Mutators

- `getReadyForApprovalStatusBadgeAttribute(): string` — Bootstrap badge HTML: green `'Ready'` when `is_ready = true`, yellow `'Not Ready'` otherwise
- `getApprovedStatusBadgeAttribute(): string` — Bootstrap badge HTML: green `'Approved'` when `isApproved()`, yellow `'Not Approved'` otherwise

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for the `amt` column; provides `fromCents()` and `toCents()` helpers

## Relationships

- `recognitionArrangement()` — belongs to [RecognitionArrangement](./recognition-arrangement.md) (`recognition_arrangement_id`): the parent recognition arrangement
- `recognizable()` — morphTo: the source entity this element applies to (mirrors the arrangement's recognizable)
- `journalEntry()` — belongs to [JournalEntry](../../accounting/models/journal-entry.md) (`journal_entry_id`): the GL journal entry generated when this element is posted
- `recognitionApproval()` — belongs to [RecognitionApproval](./recognition-approval.md) (`recognition_approval_id`): the approval batch this element belongs to

## Scopes

- `posted(Builder $query)` — filters to elements that have been posted to the GL (`journal_entry_id IS NOT NULL`)

## Events

_None defined on the model._

## Observers

- `RecognitionElementObserver` — registered in `RecognitionServiceProvider::registerObservers()` (`RecognitionElement::observe(RecognitionElementObserver::class)`). Handles:
  - `saved` — dispatches `RecognitionElementSaved` event (used to trigger downstream reactions such as updating the parent arrangement's `recognized_amt`)
  - `deleting` — dispatches `RecognitionElementDeleting` event
  - `created`, `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs

## Key Methods

- `isReady(): bool` — returns `true` when `is_ready` is set; element may be submitted for approval
- `isPosted(): bool` — returns `true` when `journal_entry_id` is set; element has been recognized in the GL
- `isApproved(): bool` — returns `true` when `recognition_approval_id` is set; element has been approved for posting
- `canBeApproved(): bool` — returns `true` when the element is ready but not yet approved (`isReady() && !isApproved()`)
- `canBePosted(): bool` — returns `true` when the element is approved but not yet posted (`isApproved() && !isPosted()`)

## Common Usage

```php
// Find all unposted elements for an arrangement
$pending = $arrangement->recognitionElements()->whereNull('journal_entry_id')->get();

// Find all posted elements (scope)
$posted = RecognitionElement::posted()->where('recognition_arrangement_id', $id)->get();

// Check state before acting
if ($element->canBeApproved()) {
    $approval->recognitionElements()->save($element);
    // or: $element->update(['recognition_approval_id' => $approval->id]);
}

if ($element->canBePosted()) {
    // generate journal entry and attach it
    $je = JournalEntry::create([...]);
    $element->update(['journal_entry_id' => $je->id]);
}

// Badge display
echo $element->ready_for_approval_status_badge;  // HTML badge
echo $element->approved_status_badge;            // HTML badge
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
