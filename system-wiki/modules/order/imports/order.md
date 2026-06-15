---
title: OrderImport
purpose: Spreadsheet import for Order — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Order/Imports/OrderImport.php
source_paths:
  - modules/Order/Imports/OrderImport.php
  - app/Imports/BaseImport.php
primary_model: Order
target_table: orders
registry_key: order
implements: OnEachRow
---

# OrderImport

Imports rows into **[Order](../models/order.md)** (`orders`). Upserts orders (present `id` updates, absent `id` creates), syncs primary and additional customers onto the `order_customer` pivot, and auto-creates billing/shipping addresses from the primary customer's defaults. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `order` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → orders.id | Present = update / absent = create. |
| `date` | No | date | — |
| `model_no` | No | unique string (except current row's id) | Uniqueness scoped to `orders.model_no`, excluding the row's own `id`. |
| `cemetery_id` | No | FK → cemeteries.id | — |
| `order_type_id` | No | FK → list_options.id | — |
| `status` | No | string | — |
| `comments` | No | string | — |
| `sale_date` | No | date | — |
| `no_comm_sale` | No | boolean | — |
| `external_id` | No | string | Stored via `saveExternalId()`. |
| `primary_customer` | No | FK → customers.id | Synced as `primary` role to the `order_customer` pivot; also sets `primary_customer_id` on the Order. |
| `additional_customer_N` | No | FK → customers.id | Numbered columns `additional_customer_1`, `additional_customer_2`, `additional_customer_3`, … (N = 1, 2, 3, …). A single wildcard rule covers all numbered columns; each is synced as an `additional` role to the `order_customer` pivot. |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- `primary_customer` sets the order's `primary_customer_id` and is synced to `customers()` with `role = primary`.
- `additional_customer_1`, `additional_customer_2`, … are synced to `customers()` with `role = additional`.
- Billing/shipping addresses are auto-created from the primary customer's default addresses if available.

## Related Records

Beyond the primary model, this import also touches:

- OrderCustomer (pivot; synced with `primary`/`additional` roles).
- Address (auto-created for billing/shipping when the primary customer has defaults).

## Behavior Notes

- **Upsert key:** `id` — present updates the existing order, absent creates a new one.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- Many-to-many customer sync writes role pivot data (`primary`, `additional`) on `order_customer`.
- Billing/shipping addresses are derived from the primary customer's default addresses on import.

## Source

Derived from `modules/Order/Imports/OrderImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
