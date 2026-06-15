---
title: PaymentImport
purpose: Spreadsheet import for Payment — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Transaction/Imports/PaymentImport.php
source_paths:
  - modules/Transaction/Imports/PaymentImport.php
  - app/Imports/BaseImport.php
primary_model: Payment
target_table: payments
registry_key: payment
implements: OnEachRow
---

# PaymentImport

Imports rows into **[Payment](../models/payment.md)** (`payments`). **Create-only** — this import never updates existing payments; each row creates a new Payment via the parent model's `createPayment()`, where the parent is resolved from the `transactionable_type` + `transactionable_id` polymorphic columns. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `payment` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → payments.id | Read but not used — create-only import does not update. |
| `amount` | Yes | numeric / decimal | — |
| `customer_id` | Yes | FK → customers.id | — |
| `method` | Yes | string | Payment method name. |
| `payment_method_id` | No | FK → payment_methods.id | — |
| `date` | Yes | date (Y-m-d) | Parsed via `Carbon::createFromFormat('Y-m-d', ...)`. |
| `check_no` | No | string | E.g. check number when `method='check'`. |
| `memo` | No | string | Stored in `Payment.memo` after creation. |
| `external_id` | No | string | Stored via `saveExternalId()` — not in `rules()`, read in `onRow`. |
| `transactionable_type` | No | fully qualified model class name | Polymorphic type (e.g. `App\Models\Order`); required in code to resolve the parent model. Not in `rules()`, read in `onRow`. |
| `transactionable_id` | No | integer | Polymorphic id; required in code to resolve the parent model. Not in `rules()`, read in `onRow`. |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- Although `transactionable_type` and `transactionable_id` are not in `rules()`, both are read in `onRow` and an Exception is thrown if either is missing or the referenced model is not found.
- The Payment is created via `model->createPayment(...)` on the resolved parent model — the parent (transactionable) morphs the payment. This is a create-only operation; no existing payment is updated.
- `date` is parsed as `Y-m-d` format (`Carbon::createFromFormat`).
- `memo` is optional and is set on the Payment after creation if provided.

## Related Records

Beyond the primary model, this import also touches:

- Polymorphic transactionable — the parent model (Order, PaymentPlan, etc.) inferred from `transactionable_type`/`transactionable_id`, whose `createPayment()` produces the Payment.

## Behavior Notes

- **Upsert key:** None — **create-only**. Every valid row creates a new Payment; `id` is read but ignored, and existing payments are never updated.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports (read in `onRow`, not declared in `rules()`).
- The import raises the memory limit to 2GB.
- Payment creation is delegated to the resolved parent model's `createPayment()`; the parent is required and is found via the `transactionable_type` + `transactionable_id` polymorphic columns.

## Source

Derived from `modules/Transaction/Imports/PaymentImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
