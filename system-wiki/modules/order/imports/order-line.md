---
title: OrderLineImport
purpose: Spreadsheet import for OrderLine — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Order/Imports/OrderLineImport.php
source_paths:
  - modules/Order/Imports/OrderLineImport.php
  - app/Imports/BaseImport.php
primary_model: OrderLine
target_table: order_lines
registry_key: order-line
implements: OnEachRow
---

# OrderLineImport

Imports rows into **[OrderLine](../models/order-line.md)** (`order_lines`). Upserts order lines (present `id` updates, absent `id` creates) with polymorphic purchasable references and optional delivery-preference config. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `order-line` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → order_lines.id | Present = update / absent = create. |
| `order_id` | No | FK → orders.id | — |
| `assigned_customer_id` | No | FK → customers.id | — |
| `property_id` | No | FK → properties.id | — |
| `purchasable_type` | No | string (fully qualified class name) | Polymorphic type. |
| `purchasable_id` | No | integer | Polymorphic id. |
| `name` | No | string max 255 | — |
| `description` | No | string | — |
| `sku` | No | string max 255 | — |
| `unit_price` | No | numeric/decimal | — |
| `unit_tax` | No | numeric/decimal | — |
| `unit_discount` | No | numeric/decimal | — |
| `quantity` | No | integer | — |
| `notes` | No | string | — |
| `delivery_preference_id` | No | integer | Not in `rules()`; read in `onRow()`. Stored in `config_data['delivery_preference_id']`. |
| `delivery_preference_data` | No | mixed (array or string) | Not in `rules()`; read in `onRow()`. Stored in `config_data['delivery_preference_data']`. |
| `external_id` | No | string | Stored via `saveExternalId()`. |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- `delivery_preference_id` and `delivery_preference_data` are optional and stored in `config_data` only when present.

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model (the parent [Order](../models/order.md) is saved after the line via `purchasable`/`order_id`).

## Behavior Notes

- **Upsert key:** `id` — present updates the existing order line, absent creates a new one.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- Polymorphic purchasable set from `purchasable_type` + `purchasable_id`.
- `config_data` updated for delivery preferences; the parent Order is saved after the OrderLine.

## Source

Derived from `modules/Order/Imports/OrderLineImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
