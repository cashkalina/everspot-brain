---
title: OwnerFileLineImport
purpose: Spreadsheet import for PropertyCommitment — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Common/Imports/OwnerFileLineImport.php
source_paths:
  - modules/Common/Imports/OwnerFileLineImport.php
  - app/Imports/BaseImport.php
primary_model: PropertyCommitment
target_table: property_commitments
registry_key: owner-file-line
implements: OnEachRow
---

# OwnerFileLineImport

Imports rows into **[PropertyCommitment](../../property/models/property-commitment.md)** (`property_commitments`). Creates or updates a PropertyCommitment, then cascades into an OwnerFileLine, OwnerFile attributes/notes, and reserved/assigned customer syncs. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `owner-file-line` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`) |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`) |
| `id` | No | FK → `property_commitments.id` | Present = update existing commitment / absent = create new (with active commitment check) |
| `external_id` | No | string max 255 | Stored on PropertyCommitment via `saveExternalId()` |
| `property_id` | No | FK → `properties.id` | Required for commitment creation (see Conditional Rules) |
| `type` | No | enum-like string | One of `PropertyCommitment::TYPES` keys |
| `is_manual` | No | boolean | — |
| `reason` | No | string max 255 | — |
| `committed_at` | No | datetime (`Y-m-d H:i:s`) | — |
| `uncommitted_at` | No | datetime (`Y-m-d H:i:s`) | — |
| `expires_at` | No | datetime (`Y-m-d H:i:s`) | — |
| `created_by` | No | FK → `users.id` | — |
| `owner_file_id` | No | FK → `owner_files.id` | If present, uses the owner file's primary customers instead of `customer_N` |
| `customer_N` | No | FK → `customers.id` | Numbered `customer_1`..`customer_5`; reserved customers (alternative to `owner_file_id`). Synced only if non-empty |
| `assigned_N` | No | FK → `customers.id` | Numbered `assigned_1`..`assigned_5`; assigned customers. Synced only if non-empty |
| `sale_date` | No | date | Stored in `OwnerFileLine.config_data`; only if value present |
| `sale_price` | No | numeric ≥ 0 | Stored in `OwnerFileLine.config_data`; only if value present |
| `deed_date` | No | date | Stored in `OwnerFileLine.config_data`; only if value present |
| `deed_number` | No | string max 255 | Stored in `OwnerFileLine.config_data` as string; only if value present |
| `notes` | No | string | Creates a Note on the OwnerFile if provided (only if not a duplicate) |
| `user_id` | No | FK → `users.id` | `required_with:notes` — required if `notes` provided; used for note `user_id` and `created_by` |
| *(attribute keys)* | No | per attribute | Any [PropertyCommitment](../../property/models/property-commitment.md) custom attribute may be set by adding a column named after its key. See [Attribute module](../../attribute/index.md). |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- Empty strings are converted to null (via `array_map` in `onRow`).
- Throws `RuntimeException` if `property_id` already has an active commitment on create — the existing commitment must be voided first.
- If `owner_file_id` is provided, its `primaryCustomers` are used instead of `customer_1`..`customer_5`.
- `customer_1`..`customer_5` and `assigned_1`..`assigned_5` are synced only when non-empty; otherwise empties are synced.
- `sale_date` / `sale_price` / `deed_date` / `deed_number` are stored in `OwnerFileLine.config_data` with `_enabled` flags only if at least one is present.
- Notes are created only if the content is not a duplicate on the OwnerFile.
- `user_id` is required when `notes` is supplied.

## Related Records

Beyond the primary model, this import also touches:

- [PropertyCommitment](../../property/models/property-commitment.md) — primary upsert.
- [OwnerFileLine](../models/owner-file-line.md) — created automatically by event; its `config_data` is populated with sale/deed info.
- [OwnerFile](../models/owner-file.md) — attributes synced.
- Note — created on the OwnerFile if the `notes` column is present (and not a duplicate).

## Behavior Notes

- **Upsert key:** `id` present = update / absent = create (with an active-commitment guard per property).
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports (on PropertyCommitment).
- Multi-step per row: (1) upsert PropertyCommitment, (2) sync reserved/assigned customers, (3) auto-create OwnerFileLine via event, (4) populate `OwnerFileLine.config_data` with sale/deed info, (5) sync OwnerFile attributes, (6) create a note if provided.
- The active-commitment check prevents more than one active commitment per property.

## Source

Derived from `modules/Common/Imports/OwnerFileLineImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
