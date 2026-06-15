---
title: CertificateLineImport
purpose: Spreadsheet import for CertificateLine — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Certificate/Imports/CertificateLineImport.php
source_paths:
  - modules/Certificate/Imports/CertificateLineImport.php
  - app/Imports/BaseImport.php
primary_model: CertificateLine
target_table: certificate_lines
registry_key: certificate-line
implements: OnEachRow
---

# CertificateLineImport

Imports rows into **[CertificateLine](../models/certificate-line.md)** (`certificate_lines`). Upserts certificate lines — a row with `id` updates an existing line, a row without creates a new one. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `certificate-line` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → certificate_lines.id | Present = update / absent = create. |
| `external_id` | No | string max 255 | Stored via `saveExternalId()`. |
| `certificate_id` | No | FK → certificates.id | Empty string converted to null. |
| `liability_line_id` | No | FK → liability_lines.id | Empty string converted to null. |
| `product_id` | No | FK → products.id | Empty string converted to null. |
| `property_id` | No | FK → properties.id | Empty string converted to null. |
| `property_type_id` | No | FK → property_types.id | Empty string converted to null. |
| `property_group_id` | No | FK → property_groups.id | Empty string converted to null. |
| `property_description` | No | string | — |
| `order_reference` | No | string max 255 | — |
| `product_sku` | No | string max 255 | — |
| `product_name` | No | string max 255 | — |
| `product_description` | No | string | — |
| `sale_price` | No | numeric / decimal | — |
| `sale_date` | No | date | — |
| `internal_notes` | No | string | — |
| `external_notes` | No | string | — |
| `is_transferable` | No | boolean | — |
| `created_by` | No | FK → users.id | Column header is `created_by` but mapped to and stored as `user_id`. |
| *(attribute keys)* | No | per attribute | Any [CertificateLine](../models/certificate-line.md) custom attribute may be set by adding a column named after its key. See [Attribute module](../../attribute/index.md). |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- Empty strings are converted to null for all ID fields: `certificate_id`, `liability_line_id`, `product_id`, `property_id`, `property_type_id`, `property_group_id`.

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model (no related records explicitly created).

## Behavior Notes

- **Upsert key:** `id` — present updates the existing CertificateLine, absent creates a new one (`updateOrCreate` keyed on `id`).
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- Custom attribute values are persisted via `saveAttributeValuesForModel` for any extra attribute-key columns.

## Source

Derived from `modules/Certificate/Imports/CertificateLineImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
