---
title: DeliveryImport
purpose: Spreadsheet import for Delivery — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Delivery/Imports/DeliveryImport.php
source_paths:
  - modules/Delivery/Imports/DeliveryImport.php
  - app/Imports/BaseImport.php
primary_model: Delivery
target_table: deliveries
registry_key: delivery
implements: OnEachRow
---

# DeliveryImport

Imports rows into **[Delivery](../models/delivery.md)** (`deliveries`). Upserts deliveries (present `id` updates, absent `id` creates), with `config_data` accepted as JSON. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `delivery` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → deliveries.id | Present = update / absent = create. |
| `model_no` | No | string max 255 | — |
| `cemetery_id` | No | FK → cemeteries.id | — |
| `agent_user_id` | No | FK → users.id | — |
| `date` | No | date | — |
| `status` | No | string | — |
| `memo` | No | string | — |
| `is_constructive` | No | boolean | — |
| `config_data` | No | JSON (auto-decoded if string) | Parsed from a JSON string if provided as a string; stored as JSON on the model. |
| `external_id` | No | string | Stored via `saveExternalId()`. |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- `config_data` is auto-decoded from a JSON string when `is_string`.

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model.

## Behavior Notes

- **Upsert key:** `id` — present updates the existing delivery, absent creates a new one.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- `config_data` handled as JSON with automatic string-to-array parsing.

## Source

Derived from `modules/Delivery/Imports/DeliveryImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
