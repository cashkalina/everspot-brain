---
title: IntermentImport
purpose: Spreadsheet import for Interment — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Interment/Imports/IntermentImport.php
source_paths:
  - modules/Interment/Imports/IntermentImport.php
  - app/Imports/BaseImport.php
primary_model: Interment
target_table: interments
registry_key: interment
implements: OnEachRow
---

# IntermentImport

Imports rows into **[Interment](../models/interment.md)** (`interments`). Upserts interments — a row with `id` updates an existing interment, a row without creates a new one — and may also create/update an associated Event and Note. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `interment` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`). |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`). |
| `id` | No | FK → interments.id | Present = update / absent = create. |
| `external_id` | No | string max 255 | Stored via `saveExternalId()`. |
| `date` | No | date | — |
| `model_no` | No | string max 255 | — |
| `deceased_id` | No | FK → customers.id | Empty string converted to null. |
| `cemetery_id` | No | FK → cemeteries.id | Empty string converted to null. |
| `nok_id` | No | FK → customers.id | Next of kin; empty string converted to null. |
| `funeral_home_id` | No | FK → customers.id | Empty string converted to null. |
| `funeral_director_id` | No | FK → customers.id | Empty string converted to null. |
| `nok_relation_id` | No | FK → list_options.id | Empty string converted to null. |
| `status` | No | enum-like string | Must be one of `Interment::STATUSES` keys. |
| `first_name` | No | string max 255 | — |
| `middle_name` | No | string max 255 | — |
| `last_name` | No | string max 255 | — |
| `suffix_id` | No | FK → list_options.id | Empty string converted to null. |
| `nickname` | No | string max 255 | — |
| `sex_id` | No | FK → list_options.id | Empty string converted to null. |
| `dob` | No | date | Legacy single date; parsed to `dob_year`/`dob_month`/`dob_day` (estimated=false) if provided. See partial-date note below. |
| `dob_year` | No | integer year (1–9999) | Partial-date component; preferred over single `dob`. |
| `dob_month` | No | integer month (1–12) | Partial-date component; preferred over single `dob`. |
| `dob_day` | No | integer day (1–31) | Partial-date component; adjusted for invalid dates (e.g. Feb 31 → Feb 28). |
| `dob_estimated` | No | boolean | Partial-date flag. |
| `dod` | No | date | Legacy single date; parsed to `dod_year`/`dod_month`/`dod_day` (estimated=false) if provided. See partial-date note below. |
| `dod_year` | No | integer year (1–9999) | Partial-date component; preferred over single `dod`. |
| `dod_month` | No | integer month (1–12) | Partial-date component; preferred over single `dod`. |
| `dod_day` | No | integer day (1–31) | Partial-date component; adjusted for invalid dates. |
| `dod_estimated` | No | boolean | Partial-date flag. |
| `doi` | No | date | Date of interment; legacy single date, parsed to `doi_year`/`doi_month`/`doi_day` (estimated=false) if provided. See partial-date note below. |
| `doi_year` | No | integer year (1–9999) | Partial-date component; preferred over single `doi`. |
| `doi_month` | No | integer month (1–12) | Partial-date component; preferred over single `doi`. |
| `doi_day` | No | integer day (1–31) | Partial-date component; adjusted for invalid dates. |
| `doi_estimated` | No | boolean | Partial-date flag. |
| `interment_type_id` | No | FK → list_options.id | Empty string converted to null. |
| `service_type_id` | No | FK → list_options.id | Empty string converted to null. |
| `interment_space` | No | string max 255 | — |
| `interment_space_id` | No | FK → properties.id | Empty string converted to null. |
| `deed_number` | No | string max 255 | — |
| `certificate_id` | No | FK → certificates.id | Empty string converted to null. |
| `property_owner` | No | string max 255 | — |
| `external_comments` | No | string | — |
| `internal_comments` | No | string | — |
| `start_date` | No | date | If provided, creates/updates an Event with `type='interment'`. |
| `start_time` | No | time HH:MM | Used with `start_date` for Event creation. |
| `end_date` | No | date | Used with `end_time` for Event creation. |
| `end_time` | No | time HH:MM | Used with `end_date` for Event creation. |
| `is_manual` | No | boolean | — |
| `calendar_id` | No | FK → calendars.id | Used for Event creation if `start_date` provided. |
| `notes` | No | string | Creates a Note on the Interment if provided. |
| `user_id` | No | FK → users.id | Used for note-creation `user_id` and `created_by`. |
| *(attribute keys)* | No | per attribute | Any [Interment](../models/interment.md) custom attribute may be set by adding a column named after its key. See [Attribute module](../../attribute/index.md). |

> **Partial dates (`dob_*`, `dod_*`, `doi_*`):** Each date of birth / death / interment can be supplied either as a single legacy date column (`dob`, `dod`, `doi`) or as component columns (`*_year`, `*_month`, `*_day`, `*_estimated`). The component columns take precedence; a legacy single date is parsed into year/month/day with `estimated=false`.

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- Empty strings are converted to null (via `array_map` in `onRow`).
- Partial dates accept both the legacy single-date field (`dob`, `dod`, `doi`) and the modern component fields (`*_year`/`*_month`/`*_day`/`*_estimated`); **component fields take precedence**.
- Invalid dates are adjusted via `checkdate` (e.g. Feb 31 → Feb 28/29).
- Events are created/updated only if `start_date` is provided (`updateOrCreate` keyed on type / eventable_id / eventable_type).
- Notes are created only if `notes` is provided.

## Related Records

Beyond the primary model, this import also touches:

- Event — created/updated if `start_date` provided (`type='interment'`, polymorphic eventable).
- Note — created if `notes` provided.

## Behavior Notes

- **Upsert key:** `id` — present updates the existing Interment, absent creates a new one (`updateOrCreate` keyed on `id`). On `_delete`, the `events` relationship is pre-deleted before the interment.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- Event auto-creation uses `cemetery_id` and `calendar_id` from the row.
- Custom attribute values are persisted for any extra attribute-key columns.

## Source

Derived from `modules/Interment/Imports/IntermentImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
