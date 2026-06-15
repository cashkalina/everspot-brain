---
title: MapLocationImport
purpose: Spreadsheet import for MapLocation — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Mapping/Imports/MapLocationImport.php
source_paths:
  - modules/Mapping/Imports/MapLocationImport.php
  - app/Imports/BaseImport.php
primary_model: MapLocation
target_table: map_locations
registry_key: map-location
implements: OnEachRow
---

# MapLocationImport

Imports rows into **[MapLocation](../models/map-location.md)** (`map_locations`). Creates or updates MapLocation records via `updateOrCreate` keyed on the composite `record_type` + `record_id` (not `id`), always for the polymorphic Property record type. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `map-location` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK -> map_locations.id | Unused — `updateOrCreate` uses the `record_type` + `record_id` composite key instead. |
| `external_id` | No | string max 255 | Stored via `saveExternalId()`. |
| `property_id` | No | FK -> properties.id | Mapped to `record_id` in the import mapping. |
| `map_id` | No | FK -> maps.id | |
| `center_point_lat` | No | float | Combined with `center_point_lng` into the `center_point` array in `onRow`. |
| `center_point_lng` | No | float | Combined with `center_point_lat` into the `center_point` array in `onRow`. |
| `bounds` | No | JSON (auto-decoded) | Parsed from a JSON string if provided. |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- `center_point_lat` and `center_point_lng` are combined into a `[lat, lng]` array if both are present.
- `type` is always set to `'property'`; `record_type` is always set to `Property::class` (polymorphic).

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model.

## Behavior Notes

- **Upsert key:** `updateOrCreate` uses the composite key (`record_type=Property::class`, `record_id=property_id`) rather than `id` — re-imports for the same property update the existing location.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- `center_point_lat`/`center_point_lng` are converted to a `[lat, lng]` array; `bounds` is auto-decoded from a JSON string.

## Source

Derived from `modules/Mapping/Imports/MapLocationImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
