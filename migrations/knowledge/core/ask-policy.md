# core/ask-policy.md — the §9 ask-policy as operational rules

**Always loaded. Keep tight.** One batched question round only (between dry-discovery
and reference-reconcile). Ask once, record to the ledger, run to completion unattended.

## The test (§9.1) — ask ONLY what is BOTH:

- **(a)** undecidable from `data + codebase + the library/pattern KB`, **AND**
- **(b)** materially affects correctness **or** is irreversible.

Fail either condition → it is **not** a question. It gets a **confident default,
recorded** (auditable, never silent). A default is always logged as `auto-resolved`
with its proposed value.

## MUST become a question (§9.2 — never auto-resolved)

- a table has **no stable `source_key`** → `kind: source_key`. (If truly keyless, fall back to a deterministic hash of the identifying columns and **flag the fragility** — but still ask which columns identify a record.)
- an **ambiguous value-set** whose codes' meaning isn't clear from profile + naming → `kind: value_set` (low confidence).
- an **unmapped column feeding a required target field**, OR a **required target field with no source column** → `kind: unmapped` / `missing_required`.
- a value-set value that **does not resolve to a real tenant `list_option` id** (the `missing` set) → `kind: value_set`.
- a **borderline entity-merge** pair → `kind: entity_merge`.
- a **blocking** validation failure that data cannot fill → `kind: validation`.

## Gets a confident default (§9.3 — recorded; may surface as low-friction "accept-all")

- a column with an **obvious 1:1 target + high-confidence transform**.
- a value-set value that **resolves cleanly and unambiguously** to exactly one tenant `list_option`.
- an **obviously-ignorable column** (export artifact, all-blank) → `unmapped` with a note.
- a **warning-level** validation finding (acceptable confidence, cosmetic difference).

## Question record shape (§9.4 — JSON-first, rendered to Markdown)

Required fields: `id`, `gate`, `kind` (`value_set | unmapped | missing_required |
source_key | entity_merge | validation`), `question`, **`proposed_answer` (mandatory —
enables "accept all")**, `options`, `allow_custom`, `handoff` (`internal | client |
either`), `status` (`open | answered | auto-resolved | skipped`).

## Persistence & idempotency (§9.5)

- Every resolved question (answered / auto-resolved / skipped-with-rationale) → `ledger/questions/<id>.json`.
- A question whose **subject already has a ledger record is never re-asked** — re-apply the answer. (This is what makes v2 cheap.)
- **Hard rule:** never proceed past the question round while any question is `open`.

## Graduation (§11.3)

A question asked the same way across many clients → promote its answer into a
**default here**, and it stops being asked. Record the move in `CHANGELOG.md`.
