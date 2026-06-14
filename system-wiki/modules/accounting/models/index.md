---
title: Accounting Module — Models Index
module: Accounting
last_updated: 2026-06-14
---

# Accounting Module — Models

All concrete Eloquent models in `modules/Accounting/Models/`. Connection: **tenant**.

| Model | Table | Description |
|-------|-------|-------------|
| [GlAccount](./gl-account.md) | `gl_accounts` | Chart-of-accounts entry; classifies every financial posting |
| [JournalEntry](./journal-entry.md) | `journal_entries` | Double-entry journal posting owned polymorphically by any module entity |
| [JournalEntryLine](./journal-entry-line.md) | `journal_entry_lines` | Individual debit or credit line within a journal entry |

## Coverage

3 of 3 models documented. Coverage: **complete**.
