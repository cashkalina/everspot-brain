---
title: BulkFileUploadFileImport
purpose: Spreadsheet import for bulk file handling — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Common/Imports/BulkFileUploadFileImport.php
source_paths:
  - modules/Common/Imports/BulkFileUploadFileImport.php
  - app/Imports/BaseImport.php
primary_model: (none — pass-through array)
target_table: (none)
registry_key: (unregistered)
implements: ToArray
---

# BulkFileUploadFileImport

Returns a raw array for bulk file handling rather than creating or updating any model. This `ToArray` implementation is a pass-through: it validates the rows and hands the resulting array back to the caller (the zip/bulk-upload flow) for file processing. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Unregistered:** not selectable from the standard import dropdown; driven by the zip/bulk-upload flow, which invokes it directly to parse a manifest of files to attach.

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`) |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`) |
| `id` | No | integer | — |
| `model_type` | Yes | string | Polymorphic owner type for the media attachment |
| `model_id` | Yes | integer | Polymorphic owner id |
| `collection_name` | Yes | string | Media library collection to attach into |
| `name` | No | string | — |
| `dir_file_path` | Yes | string | Path within the uploaded bulk directory to the file |
| `tags` | No | string | — |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- None beyond the standard column validation.

## Related Records

Beyond the primary model, this import also touches:

- None — this import creates no records; it returns the validated rows as an array for the bulk-upload flow to process.

## Behavior Notes

- **Upsert key:** N/A — no model is created or updated. `ToArray` returns the parsed rows verbatim.
- **External ID:** Not supported.
- Acts as a manifest parser for the zip/bulk-upload flow: each row points at a file (`dir_file_path`) and the model (`model_type` + `model_id`) and collection (`collection_name`) it should be attached to.

## Source

Derived from `modules/Common/Imports/BulkFileUploadFileImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
