---
title: Model Document Template
purpose: Standard template for all model documentation
version: 1
last_updated: 2026-06-12
---

# Model Document Template

This is the standard template for all model documentation in the Everspot System Wiki. Copy this structure for every new model document.

---

```markdown
---
model: Payment
module: Transaction
table: payments
connection: tenant            # central | tenant (derived from which snapshot holds the table)
source_paths:                 # computed; recomputed on every regeneration
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Models/Concerns/HasRefunds.php
  - app/Providers/EventServiceProvider.php
related: [Transaction, Refund, Customer]   # derived; powers reverse-relationship lookups
built_at: <main commit this document was generated against>
last_updated: 2026-06-12       # informational only; currency is built_at + sources + snapshot
completeness: complete         # complete | partial | stub (rule-based; see conventions)
deprecated: false              # if true, requires `successor:`
tags: [financial, payment, core]   # controlled vocabulary
---

# Payment

**Primary source:** `modules/Transaction/Models/Payment.php`

## Overview
What this model represents and why it exists. AI-owned.

## Connection & Table
Tenant · `payments`

## Schema
| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| ...    | ...  | ...      | ...     | ...         |
<!-- rendered from schema/tenant.json; validated against it before commit -->

## Properties / Casts
...

## Relationships
- `transaction()` — belongs to [Transaction](./transaction.md): the parent financial record.

## Key Methods
- `process()` — ...

## Scopes / Events / Observers
...

## Common Usage
```php
// representative examples
```

<!-- human:begin -->
## Business Logic Notes
Human-authored insight. Never overwritten by the agent. See §6.3.
<!-- human:end -->
```

---

## Template Notes

### Frontmatter Fields

- **model:** The PHP class name (e.g., `Payment`, `TransactionItem`)
- **module:** The module name if in `modules/`, or `Core` if in `app/Models/`
- **table:** The database table name
- **connection:** `central` or `tenant` — derived from which schema snapshot contains the table
- **source_paths:** List of all files this document derives from (model, traits, observers, relationship inverses). **Recomputed on every regeneration.**
- **related:** List of model names this model has relationships to. Powers reverse-relationship lookups.
- **built_at:** The `main` commit hash this document was generated against
- **last_updated:** Human-readable date (YYYY-MM-DD). Informational only; actual currency is `built_at` + `source_paths` + snapshot
- **completeness:** `complete`, `partial`, or `stub` (see `meta/conventions.md`)
- **deprecated:** `true` if model has been removed from Everspot. If true, must include `successor:` field
- **tags:** 2-4 tags from controlled vocabulary (see `meta/conventions.md`)

### Section Guidelines

**Overview:** AI-generated prose explaining the business purpose and role of this model. Should be 2-4 paragraphs.

**Connection & Table:** Format as `Connection · table_name` (e.g., `Tenant · payments` or `Central · users`)

**Schema:** Rendered deterministically from the connection snapshot (`schema/central.json` or `schema/tenant.json`). Include markdown comment noting the source snapshot. Validated against snapshot before commit.

**Properties / Casts:** Document `$fillable`, `$guarded`, `$casts`, `$dates`, `$appends`, accessors (`get*Attribute`), and mutators (`set*Attribute`).

**Relationships:** One bullet per relationship. Format:
- `relationshipName()` — relationship type [LinkedModel](./path/to/model.md): description of what it represents

**Key Methods:** Public methods beyond standard Eloquent. Show signature and purpose, not full body.

**Scopes / Events / Observers:** Document query scopes, model events, and observer registrations.

**Common Usage:** Code examples showing typical usage patterns. Use PHP code blocks.

**Business Logic Notes:** Human-authored section. Content between `<!-- human:begin -->` and `<!-- human:end -->` is never overwritten by AI. This is where humans add insights not derivable from code.

### AI Maintenance Rules

1. **Never modify content between `<!-- human:begin -->` and `<!-- human:end -->`**
2. All other sections are AI-owned and regenerated freely
3. Re-derive `source_paths` on every update by analyzing model dependencies
4. Re-derive `related` by extracting all relationship target models
5. Derive `connection` by checking which snapshot (`central.json` or `tenant.json`) contains the table
6. Validate Schema table against snapshot before committing
7. Stamp `built_at` with the current `main` commit hash
8. Update `last_updated` to current date
