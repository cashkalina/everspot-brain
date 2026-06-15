---
title: PaymentPlanImport
purpose: Spreadsheet import for PaymentPlan — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/PaymentPlan/Imports/PaymentPlanImport.php
source_paths:
  - modules/PaymentPlan/Imports/PaymentPlanImport.php
  - app/Imports/BaseImport.php
primary_model: PaymentPlan
target_table: payment_plans
registry_key: payment-plan
implements: OnEachRow
---

# PaymentPlanImport

Imports rows into **[PaymentPlan](../models/payment-plan.md)** (`payment_plans`). Upserts payment plans (present `id` updates, absent `id` creates), with numeric financing fields range-validated and a unique `model_no` per plan. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `payment-plan` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → payment_plans.id | Present = update / absent = create. |
| `order_id` | No | FK → orders.id | — |
| `cemetery_id` | No | FK → cemeteries.id | — |
| `model_no` | No | unique string (except current row's id) | Uniqueness scoped to `payment_plans.model_no`, excluding the row's own `id`. |
| `date` | No | date | — |
| `enable_late_fee` | No | boolean | — |
| `late_fee_amt` | No | numeric ≥ 0 | — |
| `grace_period` | No | integer ≥ 0 | Number of days. |
| `down_payment` | No | numeric/decimal | — |
| `frequency` | No | string | e.g. `monthly`, `quarterly`, etc. |
| `term` | No | integer ≥ 1 | Number of payment periods. |
| `first_due_date` | No | date | — |
| `interest_rate` | No | numeric 0–1 (0.0–1.0 format) | — |
| `amount_financed` | No | numeric/decimal | — |
| `payment_amt` | No | numeric/decimal | — |
| `external_id` | No | string | Not in `rules()`; read in `saveExternalId()`. |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- None beyond the standard column validation.

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model.

## Behavior Notes

- **Upsert key:** `id` — present updates the existing payment plan, absent creates a new one.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports (called in `onRow()` though it has no explicit `rules()` entry).
- All numeric fields validated for their min/max constraints; `model_no` must be unique per payment plan (excluding the current row).

## Source

Derived from `modules/PaymentPlan/Imports/PaymentPlanImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
