---
model: JournalEntryLine
module: Accounting
table: journal_entry_lines
connection: tenant
primary_source: modules/Accounting/Models/JournalEntryLine.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Accounting/Models/JournalEntry.php
  - modules/Accounting/Models/GlAccount.php
traits:
  - HasMoneyFields
related_models: [GlAccount, JournalEntry]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, accounting, transaction]
---

# JournalEntryLine

## Overview

The `JournalEntryLine` model represents a single debit or credit line within a [JournalEntry](./journal-entry.md). Each line posts an amount (`amt`) to a specific G/L account (`gl_account_id`) with a `posting_type` of either `debit` or `credit`. For a journal entry to be balanced (a fundamental double-entry accounting requirement), the sum of all debit line amounts must equal the sum of all credit line amounts.

Lines carry an optional `entity_type` / `entity_id` polymorphic reference (stored as `entity_*` columns) that identifies the business object responsible for that particular line item — for example, a `Customer` or a contract line. This allows the parent `JournalEntry::getCustomers()` method to enumerate all customers touched by an entry, and it enables reporting by entity without coupling the accounting module to upstream domain models.

The `amt` column stores amounts as **integer cents** via the `HasMoneyFields` trait. Declaring `$moneyAttributes = ['amt']` causes the trait to transparently convert between dollars (in PHP) and cents (in the database), so callers work with decimal values while the column holds integers.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| journal_entry_id | bigint | No | - | FK → journal_entries; the parent entry |
| posting_type | varchar | No | - | `debit` or `credit` |
| gl_account_id | bigint | No | - | FK → gl_accounts; the G/L account this line posts to |
| amt | int | No | - | Amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| memo | text | Yes | - | Optional per-line memo |
| entity_type | varchar | Yes | - | Polymorphic entity class (e.g. `Modules\Customer\Models\Customer`) |
| entity_id | varchar | Yes | - | Polymorphic entity ID |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `journal_entry_id` → `journal_entries.id`; `gl_account_id` → `gl_accounts.id`

**Indexes:** index on `journal_entry_id`; FK-backing index on `gl_account_id`; composite index on (`entity_type`, `entity_id`) as `entity_index`; primary key on `id`.

## Casts

_None._ (Amount conversion is handled by the `HasMoneyFields` trait — see trait doc — not via `$casts`.)

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Appends:** _None._
**Hidden:** _None._
**Visible:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['amt']` — declares `amt` to the `HasMoneyFields` trait for transparent cents-to-dollars conversion.

## Accessors & Mutators

- `getFormattedPostingTypeAttribute(): string` — returns `posting_type` with the first letter uppercased (e.g. `'debit'` → `'Debit'`)

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `amt`; also provides `formatMoney()`, `fromCents()`, and `toCents()` helpers

## Relationships

- `journalEntry()` — belongs to [JournalEntry](./journal-entry.md): the parent journal entry this line belongs to
- `glAccount()` — belongs to [GlAccount](./gl-account.md): the G/L account this line posts to
- `entity()` — morphTo: the polymorphic business entity responsible for this line (e.g. a Customer, contract, or other domain record)

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._ (The accessors and trait helpers cover all non-Eloquent behavior.)

## Common Usage

```php
// Create a debit line on a journal entry
$entry->lines()->create([
    'posting_type'   => 'debit',
    'gl_account_id'  => $revenueAccount->id,
    'amt'            => 15000,          // stored as cents; represents $150.00
    'memo'           => 'Cemetery lot sale',
    'entity_type'    => Customer::class,
    'entity_id'      => $customer->id,
]);

// Read the amount — HasMoneyFields returns dollars
$line = JournalEntryLine::find(1);
echo $line->amt;             // e.g. 150.00 (dollars; stored as 15000 cents)

// Display the posting type in a view
echo $line->formatted_posting_type;   // "Debit"

// Sum all debit lines on an entry (amounts returned in dollars by HasMoneyFields)
$totalDebits = $entry->lines()
    ->where('posting_type', 'debit')
    ->get()
    ->sum('amt');

// Find all lines for a specific entity
$customerLines = JournalEntryLine::where('entity_type', Customer::class)
    ->where('entity_id', $customer->id)
    ->with('glAccount', 'journalEntry')
    ->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
