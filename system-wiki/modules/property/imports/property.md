---
title: PropertyImport
purpose: Spreadsheet import for Property — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Property/Imports/PropertyImport.php
source_paths:
  - modules/Property/Imports/PropertyImport.php
  - app/Imports/BaseImport.php
primary_model: Property
target_table: properties
registry_key: property
implements: OnEachRow
---

# PropertyImport

Imports rows into **[Property](../models/property.md)** (`properties`). Creates or updates Property records via `updateOrCreate` keyed on `id`, and can conditionally create/update an associated MapLocation. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `property` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK -> properties.id | Present=update / absent=create. |
| `external_id` | No | string max 255 | Stored via `saveExternalId()`. |
| `property_type_id` | No | FK -> property_types.id | |
| `property_group_id` | No | FK -> property_groups.id | |
| `cemetery_id` | No | FK -> cemeteries.id | |
| `model_no` | No | string max 255 | |
| `description` | No | string max 255 | |
| `trusting_schedule_group_id` | No | FK -> trusting_schedule_groups.id | |
| `sale_price` | No | numeric/decimal | |
| `cost_price` | No | numeric/decimal | |
| `add_to_map` | No | boolean | If `1`, creates/updates a MapLocation. |
| `map_location_id` | No | FK -> map_locations.id | Used for MapLocation `updateOrCreate` key if `add_to_map=1`. |
| `map_id` | No | FK -> maps.id | Used for MapLocation creation if `add_to_map=1`. |
| `center_point_lat` | No | float | Used for `MapLocation.center_point[0]` if `add_to_map=1`. |
| `center_point_lng` | No | float | Used for `MapLocation.center_point[1]` if `add_to_map=1`. |
| `bounds` | No | JSON (auto-decoded) | Used for `MapLocation.bounds` if `add_to_map=1`. |
| *(attribute keys)* | No | per attribute | Any [Property](../models/property.md) custom attribute may be set by adding a column named after its key. See [Attribute module](../../attribute/index.md). |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- MapLocation created/updated only if `add_to_map=1`; `MapLocation.type` is always `'property'` and `record_type` is always `Property::class`.

## Related Records

Beyond the primary model, this import also touches:

- [MapLocation](../../mapping/models/map-location.md) — created/updated when `add_to_map=1`.

## Behavior Notes

- **Upsert key:** `updateOrCreate` keyed on `id` — present=update, absent=create.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- `center_point_lat`/`center_point_lng` are combined into a `[lat, lng]` array; `bounds` is auto-decoded from a JSON string.
- Custom attributes are persisted via `saveAttributeValuesForModel`.

## Source

Derived from `modules/Property/Imports/PropertyImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
