---
title: PropertyGroupImport
purpose: Spreadsheet import for PropertyGroup — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Property/Imports/PropertyGroupImport.php
source_paths:
  - modules/Property/Imports/PropertyGroupImport.php
  - app/Imports/BaseImport.php
primary_model: PropertyGroup
target_table: property_groups
registry_key: property-group
implements: OnEachRow
---

# PropertyGroupImport

Imports rows into **[PropertyGroup](../models/property-group.md)** (`property_groups`). Creates or updates PropertyGroup records via `updateOrCreate` keyed on `id`, supporting self-referential hierarchies. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `property-group` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK -> property_groups.id | Present=update / absent=create. |
| `external_id` | No | string max 255 | Stored via `saveExternalId()`. |
| `property_group_id` | No | FK -> property_groups.id | Self-referential parent group. |
| `cemetery_id` | No | FK -> cemeteries.id | |
| `product_id` | No | FK -> products.id | |
| `name` | No | string max 255 | |
| `trusting_schedule_group_id` | No | FK -> trusting_schedule_groups.id | |
| `sale_price` | No | numeric/decimal | |
| `cost_price` | No | numeric/decimal | |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- None beyond the standard column validation.

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model.

## Behavior Notes

- **Upsert key:** `updateOrCreate` keyed on `id` — present=update, absent=create.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- `property_group_id` is self-referential, allowing hierarchical groups.

## Source

Derived from `modules/Property/Imports/PropertyGroupImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
