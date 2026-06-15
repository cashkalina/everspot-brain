---
title: PropertyCommitmentImport
purpose: Spreadsheet import for PropertyCommitment — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Property/Imports/PropertyCommitmentImport.php
source_paths:
  - modules/Property/Imports/PropertyCommitmentImport.php
  - app/Imports/BaseImport.php
primary_model: PropertyCommitment
target_table: property_commitments
registry_key: property-commitment
implements: OnEachRow
---

# PropertyCommitmentImport

Imports rows into **[PropertyCommitment](../models/property-commitment.md)** (`property_commitments`). Creates or updates PropertyCommitment records (create blocked when the property already has an active commitment) and syncs reserved/assigned customers. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `property-commitment` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK -> property_commitments.id | Present=update existing / absent=create (with active commitment check). |
| `external_id` | No | string max 255 | Stored via `saveExternalId()`. |
| `property_id` | No | FK -> properties.id | Required for commitment creation. |
| `type` | No | enum-like string | One of `PropertyCommitment::TYPES` keys. |
| `is_manual` | No | boolean | |
| `reason` | No | string max 255 | |
| `committed_at` | No | datetime (Y-m-d H:i:s) | |
| `uncommitted_at` | No | datetime (Y-m-d H:i:s) | |
| `expires_at` | No | datetime (Y-m-d H:i:s) | |
| `created_by` | No | FK -> users.id | |
| `customer_N` | No | FK -> customers.id | Numbered `customer_1`..`customer_5`; reserved customers, synced (per index) if present. |
| `assigned_N` | No | FK -> customers.id | Numbered `assigned_1`..`assigned_5`; assigned customers, synced (per index) if present. |
| *(attribute keys)* | No | per attribute | Any [PropertyCommitment](../models/property-commitment.md) custom attribute may be set by adding a column named after its key. See [Attribute module](../../attribute/index.md). |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- On create (`id` absent): throws `RuntimeException` if `property_id` already has an active commitment; the existing one must be voided first.
- On create: `property_group_id` and `cemetery_id` are auto-set from the property.
- `customer_1`..`customer_5` synced with the `reserved` role if any are non-empty.
- `assigned_1`..`assigned_5` synced with the `assigned` role if any are non-empty.

## Related Records

Beyond the primary model, this import also touches:

- [Customer](../../customer/models/customer.md) — existing customers synced into the reserved/assigned pivot (no customers are created).

## Behavior Notes

- **Upsert key:** `updateOrCreate` keyed on `id` — present=update, absent=create with the active-commitment guard above.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- Many-to-many customer sync carries role pivot data (`reserved`, `assigned`).

## Source

Derived from `modules/Property/Imports/PropertyCommitmentImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
