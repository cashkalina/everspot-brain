---
title: MediaImport
purpose: Spreadsheet import for Media — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Common/Imports/MediaImport.php
source_paths:
  - modules/Common/Imports/MediaImport.php
  - app/Imports/BaseImport.php
primary_model: Media
target_table: media
registry_key: media
implements: OnEachRow
---

# MediaImport

Imports rows into **[Media](../models/media.md)** (`media`). Updates existing media records only — `id` is required, so this import never creates new media rows. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `media` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`) |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`) |
| `id` | Yes | FK → `media.id` | Required — must reference an existing media record to update |
| `external_id` | No | string max 255 | Stored via `saveExternalId()` |
| `model_type` | No | string max 255 | — |
| `model_id` | No | integer | — |
| `uuid` | No | string max 36 | — |
| `collection_name` | No | string max 255 | — |
| `name` | No | string max 255 | — |
| `file_name` | No | string max 255 | — |
| `mime_type` | No | string max 255 | — |
| `disk` | No | string max 255 | — |
| `conversions_disk` | No | string max 255 | — |
| `size` | No | integer | — |
| `manipulations` | No | JSON | `nullable` in `rules()`; in `onRow` auto-decoded from a JSON string if provided as a string |
| `custom_properties` | No | JSON | `nullable` in `rules()`; in `onRow` auto-decoded from a JSON string if provided as a string |
| `is_public` | No | boolean | String values (`true`, `1`, `yes`, `y`) converted to boolean in `onRow` |
| `generated_conversions` | No | JSON | `nullable` in `rules()`; in `onRow` auto-decoded from a JSON string if provided as a string |
| `responsive_images` | No | JSON | `nullable` in `rules()`; in `onRow` auto-decoded from a JSON string if provided as a string |
| `order_column` | No | integer | — |
| `tags` | No | string (comma-separated or array) | `nullable` in `rules()`; in `onRow` parsed from a comma-separated string and synced via `syncTags()` |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- JSON fields (`manipulations`, `custom_properties`, `generated_conversions`, `responsive_images`) are auto-decoded from a string when `is_string`.
- `is_public` string values (`true`, `1`, `yes`, `y`, case-insensitive) are converted to boolean.
- `tags` comma-separated string is parsed to an array and synced if present.

## Related Records

Beyond the primary model, this import also touches:

- Tags — synced via `syncTags()` when the `tags` column is present.

## Behavior Notes

- **Upsert key:** `id` (required). This is an update-only import — `id` must reference an existing media record; new media cannot be created here.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports.
- JSON-typed columns accept either a raw array or a JSON string; strings are decoded in `onRow`.
- `tags` is parsed from a comma-separated string (or array) and synced rather than written as a column.

## Source

Derived from `modules/Common/Imports/MediaImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
