---
title: DeliveryLineImport
purpose: Spreadsheet import for DeliveryLine — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Delivery/Imports/DeliveryLineImport.php
source_paths:
  - modules/Delivery/Imports/DeliveryLineImport.php
  - app/Imports/BaseImport.php
primary_model: DeliveryLine
target_table: delivery_lines
registry_key: delivery-line
implements: OnEachRow
---

# DeliveryLineImport

Imports rows into **[DeliveryLine](../models/delivery-line.md)** (`delivery_lines`). Upserts delivery lines (present `id` updates, absent `id` creates), resolving the target liability line either directly or from an order line. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `delivery-line` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → delivery_lines.id | Present = update / absent = create. |
| `delivery_id` | No | FK → deliveries.id | — |
| `liability_line_id` | No | FK → liability_lines.id | Must be provided directly OR resolved from `order_line_id` — not both, not neither (see Conditional Rules). |
| `order_line_id` | No | FK → order_lines.id | If provided, resolved to the first available LiabilityLine (no `delivery_date`, no `cancellation_date`). |
| `memo` | No | string | — |
| `external_id` | No | string | Stored via `saveExternalId()`. |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- **Exactly one** of `liability_line_id` OR `order_line_id` must be provided (enforced by `customValidation`) — supplying both or neither fails the row.
- Throws an Exception if `liability_line_id` cannot be resolved.
- Throws an Exception if the resolved LiabilityLine is **not available** (already delivered — has a `delivery_date` — or cancelled — has a `cancellation_date`).

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model (reads LiabilityLine / OrderLine to resolve the target).

## Behavior Notes

- **Upsert key:** `id` — present updates the existing delivery line, absent creates a new one.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- Hybrid ID resolution: `liability_line_id` taken directly if provided, otherwise resolved from `order_line_id`'s first `availableLiabilityLines()`.
- Availability is validated (no `delivery_date`, no `cancellation_date`) before the line is attached.

## Source

Derived from `modules/Delivery/Imports/DeliveryLineImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
