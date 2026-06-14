---
title: Accounting Module
module: Accounting
last_updated: 2026-06-14
---

# Accounting Module

The Accounting module provides double-entry bookkeeping infrastructure for Everspot. It maintains a chart of G/L accounts, records journal entries that capture the financial impact of events across all other modules, and integrates with external accounting systems (e.g. QuickBooks) via the syncables layer.

**Source location:** `modules/Accounting/`

**Database connection:** tenant

## Models

See [models/index.md](./models/index.md) for the full model listing.

| Model | Table | Role |
|-------|-------|------|
| [GlAccount](./models/gl-account.md) | `gl_accounts` | Chart-of-accounts entries |
| [JournalEntry](./models/journal-entry.md) | `journal_entries` | Polymorphic double-entry journal postings |
| [JournalEntryLine](./models/journal-entry-line.md) | `journal_entry_lines` | Individual debit/credit lines |

## Key Concepts

- **Double-entry accounting** — every `JournalEntry` must have balanced debit and credit `JournalEntryLine` totals.
- **Polymorphic ownership** — `JournalEntry` is owned by any module entity via `journalable_type` / `journalable_id`; `JournalEntryLine` references business entities via `entity_type` / `entity_id`.
- **Void semantics** — entries are never truly deleted; the public `delete()` path voids the entry by creating a reversing entry. `forceDelete()` is the administrative bypass.
- **External sync** — `GlAccount` and `JournalEntry` both use `HasSyncables` to link records to counterparts in the active external accounting integration.
- **Money storage** — `JournalEntryLine.amt` is stored as integer cents via `HasMoneyFields`.
