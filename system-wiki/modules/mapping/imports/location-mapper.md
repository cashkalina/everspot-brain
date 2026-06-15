---
title: MappingLocationMapper
purpose: Multi-sheet location mapper — parallel WithMultipleSheets system, currently stubbed
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Mapping/Livewire/Imports/LocationMapperImport.php
source_paths:
  - modules/Mapping/Livewire/Imports/LocationMapperImport.php
  - modules/Mapping/Livewire/Imports/Sheets/PropertySheet.php
  - modules/Mapping/Livewire/Imports/Sheets/MarkerSheet.php
primary_model: (none — sheets unimplemented)
target_table: (none — sheets unimplemented)
registry_key: (unregistered)
implements: WithMultipleSheets
---

# MappingLocationMapper

A **distinct, parallel import system** — not a standard `BaseImport`. `LocationMapperImport` is a multi-sheet coordinator that implements `WithMultipleSheets` (Laravel Excel) and dispatches to two child sheets, `PropertySheet` ("Property") and `MarkerSheet` ("Markers"). It is driven by the Mapping module's own Livewire flow, not the central import subsystem. Both child sheets are currently **stub placeholders** — they declare `WithHeadingRow` only, with no `rules()` or `onRow()` implemented — so the importer parses headers but persists nothing. See the [import subsystem](../../../system/imports.md) for the standard `BaseImport` contract this system deliberately does **not** follow.

> **Unregistered:** not selectable from the standard import dropdown (absent from `Import::getImports`). It is invoked through the Mapping module's Livewire location-mapping flow, where the coordinator hands each sheet to its handler.

## How it differs from the standard pattern

- **No `BaseImport` inheritance.** Neither `LocationMapperImport` nor its sheets extend `app/Imports/BaseImport.php`; none of the BaseImport machinery (upsert, `saveExternalId`, attribute saving, `_delete`/`delete` handling) applies.
- **`WithMultipleSheets`, not `OnEachRow`.** The coordinator's `sheets()` returns the two named sheets; the standard imports each process a single flat sheet via `OnEachRow`.
- **Sheets are stubs.** `PropertySheet` and `MarkerSheet` implement only `WithHeadingRow`. They must be wired up (add `rules()`/`onRow()`, choose a target model and key) before the system does anything.

## Columns

Both sheets are unimplemented stubs, so there is no validated column set to document:

- **`Property` sheet** — registered as `"Property"` in `LocationMapperImport::sheets()`. `WithHeadingRow` only; no `rules()` or `onRow()`. Placeholder.
- **`Markers` sheet** — registered as `"Markers"` in `LocationMapperImport::sheets()`. `WithHeadingRow` only; no `rules()` or `onRow()`. Placeholder.

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- None beyond the standard column validation.

## Related Records

Beyond the primary model, this import also touches:

- None — upserts only the primary model.

## Behavior Notes

- **Upsert key:** none — the sheets perform no persistence in their current stub state.
- **External ID:** Not supported.
- Intended for the Mapping Livewire location-mapping flow; the two sheets must be implemented and wired into `LocationMapperImport` before the coordinator does any work.

## Source

Derived from `modules/Mapping/Livewire/Imports/LocationMapperImport.php`, `modules/Mapping/Livewire/Imports/Sheets/PropertySheet.php`, and `modules/Mapping/Livewire/Imports/Sheets/MarkerSheet.php` @ `origin/main` 86b4328. Re-derive `sheets()` and each sheet's `rules()`/`onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
