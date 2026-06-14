---
model: JournalEntry
module: Accounting
table: journal_entries
connection: tenant
primary_source: modules/Accounting/Models/JournalEntry.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Accounting/Observers/JournalEntryObserver.php
  - modules/Accounting/Providers/AccountingServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Accounting/Models/JournalEntryLine.php
  - modules/Customer/Models/Customer.php
traits:
  - HasSyncables
  - SoftDeletes
related_models: [Cemetery, JournalEntry, JournalEntryLine]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, accounting, transaction]
---

# JournalEntry

## Overview

The `JournalEntry` model represents a double-entry accounting journal posting in Everspot. Each entry records a balanced set of debit and credit lines against G/L accounts, capturing the financial impact of a business event — such as a payment received, a contract sale, or a refund issued.

Journal entries are polymorphic (`journalable_type` / `journalable_id`) so that any module entity (orders, payments, payment plans, etc.) can own one or more journal entries without the accounting module needing to know about every upstream type. Each entry is scoped to a `cemetery`, records a `date` and optional `memo`, and carries the individual debit/credit lines as `JournalEntryLine` children.

Journal entries are **soft-deleted** but the delete semantics are non-standard: the overridden `delete()` method **voids** the entry (creating a reversing entry via `VoidJournalEntry`) rather than marking it as soft-deleted directly. `forceDelete()` bypasses voiding for administrative correction — it dispatches the `JournalEntryDeleting` event, removes all lines, then performs a proper soft-delete via the parent implementation. The void relationship is self-referential: a voiding entry points to the original via `voided_by_id`, and the original can navigate back to all its voiding entries via `voidedEntries()`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| journalable_type | varchar | Yes | - | Polymorphic owner class (e.g. `Modules\Order\Models\Order`) |
| journalable_id | varchar | Yes | - | Polymorphic owner ID |
| cemetery_id | bigint | Yes | - | FK → cemeteries; the cemetery this entry belongs to |
| date | date | No | - | Posting date of the journal entry |
| memo | varchar | Yes | - | Optional memo / description |
| voided_by_id | bigint | Yes | - | FK → journal_entries; the entry that voided this one (null if not voided) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `voided_by_id` → `journal_entries.id`

**Indexes:** index on `date`; FK-backing indexes on `cemetery_id`, `voided_by_id`; composite index on (`journalable_type`, `journalable_id`) as `journalable_index`; primary key on `id`.

## Casts

- `date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._ (the accessor below is read on demand)
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getPostedStatusBadgeAttribute()` — returns an HTML badge: `danger`/`Voided` when the record is soft-deleted (trashed), `success`/`Posted` otherwise

## Traits

- [HasSyncables](../../../system/traits/index.md#hassyncables) — links each journal entry to its counterpart in an external accounting integration (e.g. QuickBooks)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — journal entries are soft-deleted rather than hard-deleted; note that the public `delete()` method redirects to voiding (see Key Methods)

## Relationships

- `journalable()` — morphTo: the polymorphic owner of this journal entry (may be Order, Payment, PaymentPlan, or any other module entity that posts journal entries)
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery scope for this entry
- `lines()` — has many [JournalEntryLine](./journal-entry-line.md): the individual debit/credit lines that make up this entry
- `voidedBy()` — belongs to [JournalEntry](./journal-entry.md) (`voided_by_id`): the entry that created the void/reversal for this entry
- `voidedEntries()` — has many [JournalEntry](./journal-entry.md) (`voided_by_id`): the reversing entries generated when this entry was voided

## Scopes

_None._

## Events

- `delete()` override fires the model's `'deleting'` event manually before redirecting to `void()`; if the event returns `false`, deletion is aborted.
- `forceDelete()` dispatches `JournalEntryDeleting` (from `Modules\Accounting\Events\JournalEntryDeleting`) before deleting lines and soft-deleting; guards against force-deleting already-voided entries.

## Observers

- `JournalEntryObserver` — registered in `AccountingServiceProvider::registerObservers()` (`JournalEntry::observe(JournalEntryObserver::class)`). All lifecycle hooks (`saved`, `created`, `updated`, `deleted`, `restored`, `forceDeleted`) are present but contain no logic — they are stubs for future use.

## Key Methods

- `isVoided(): bool` — returns `true` when `voided_by_id` is non-null (this entry has been reversed by another entry)
- `isVoiding(): bool` — returns `true` when at least one reversing entry exists in `voidedEntries()` (this entry is itself a void)
- `void(): self` — voids this journal entry by executing `VoidJournalEntry` action; returns the resulting reversing entry
- `delete(): bool` — **overrides Eloquent**: fires the `'deleting'` model event, then calls `void()` instead of performing a soft-delete; entries are never soft-deleted directly through the normal delete path
- `forceDelete(): bool` — **administrative hard-path**: validates the entry is not already voided, dispatches `JournalEntryDeleting`, deletes all child lines, then calls `parent::delete()` (soft-delete) to finalize
- `getCustomers(): Collection` — returns a `Collection` of [Customer](../../customer/models/customer.md) models whose IDs appear on any line of this entry with `entity_type = Customer::class`

## Common Usage

```php
// Retrieve all journal entries for an order (via polymorphic relationship)
$entries = $order->journalEntries()->with('lines.glAccount')->get();

// Check voiding status
if ($entry->isVoided()) {
    echo 'This entry was voided by entry #' . $entry->voided_by_id;
}

// Void an entry (creates a reversing entry)
$reversal = $entry->void();

// Force-delete an entry (bypasses voiding — use with care)
$entry->forceDelete();

// Find all customers referenced in an entry's lines
$customers = $entry->getCustomers();

// Display a status badge in a Blade view
{!! $entry->posted_status_badge !!}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
