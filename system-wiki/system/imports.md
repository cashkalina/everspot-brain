---
title: Import Subsystem
purpose: Spreadsheet (Excel/CSV) data import — base contract, processing flow, and registry of all concrete imports
type: subsystem
doc_kind: subsystem-concept
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: app/Imports/BaseImport.php
source_paths:
  - app/Imports/BaseImport.php
  - modules/Common/Support/Imports/Import.php
  - modules/Common/Jobs/ImportJob.php
  - modules/Common/Livewire/Import.php
related_traits:
  - has-external-ids
related_modules:
  - Attribute
status: pilot
---

# Import Subsystem

> **Reference example for the subsystem-doc pattern.** This was the wiki's first non-model subsystem document; the pattern it piloted is now codified in `foundation.md` §5.6 and `meta/subsystem-template.md`. It documents the spreadsheet-import surface that the per-module inventory (`meta/non-model-surface.md`) bucketed as 17 `Imports` files across 10 modules.

Everspot imports tabular data (Excel/CSV) into domain models through a single, consistent subsystem built on [Maatwebsite Laravel Excel](https://docs.laravel-excel.com/). A user picks an import type and uploads a file; the file is processed asynchronously inside a database transaction; the uploader is emailed the outcome. Nearly every concrete import is a thin subclass of one abstract base.

---

## Architecture at a Glance

```
Modules\Common\Livewire\Import         (UI: pick type + upload file)
        │  runImport()  →  stores file, dispatches job
        ▼
Modules\Common\Jobs\ImportJob          (queued; wraps Excel::import in DB::transaction)
        │  Excel::import(new $importClass, $file)
        ▼
App\Imports\BaseImport  (abstract)     ← every concrete XImport extends this
        │  per-row: shouldDelete? → getUpdateArray → updateOrCreate
        │           → saveAttributeValuesForModel → saveExternalId
        ▼
   Target model(s)  (Property, Customer, Order, …)

Registry: Modules\Common\Support\Imports\Import::getImports()
          maps  type-key → { label, class }   (drives the UI dropdown)
```

Three moving parts plus the base:

| Part | Class | Role |
|---|---|---|
| Entry point | `Modules\Common\Livewire\Import` | Livewire component. `mount()` loads the type dropdown from the registry; `runImport()` validates the selection + file, stores the upload to `imports/{type}`, and dispatches `ImportJob`. (Also hosts an unrelated `runZipUpload()` for bulk-file/zip uploads.) |
| Async processor | `Modules\Common\Jobs\ImportJob` | `ShouldQueue` job. Pauses analytics, runs `Excel::import(new $importClass, $file)` inside `DB::transaction`, then emails the creator success (`common::email.imports.success`) or failure (`common::email.imports.failure`). Catches Maatwebsite `ValidationException` and any `\Throwable` separately. **The whole import is one transaction — a failure on any row rolls back the entire file.** |
| Registry | `Modules\Common\Support\Imports\Import` | Static `getImports()` returns the canonical `type-key → {label, class, sample-file}` map; `getImportOptions()` reduces it to `key → label` for the dropdown. **To add an importable type, register it here** — an import class that isn't in this map is unreachable from the standard UI. |

---

## The Base Contract — `App\Imports\BaseImport`

`abstract class BaseImport implements WithHeadingRow, WithValidation`

- `WithHeadingRow` — the first spreadsheet row is treated as column headers; each data row arrives as an associative array keyed by header.
- `WithValidation` — Maatwebsite runs each subclass's `rules()` against every row before processing; a violation aborts the import with a `ValidationException`.

It supplies six shared `protected` helpers that concrete imports compose. **This is the reuse surface — document changes here ripple to every import.**

| Helper | Purpose |
|---|---|
| `shouldDelete(array $row): bool` | True when the row sets `_delete` or `delete` truthy. The convention for soft-driving deletions from a spreadsheet. |
| `deleteModel(string $modelClass, array $row, array $relationshipsToDelete = []): bool` | Finds `$row['id']`, optionally deletes named relationships first, then deletes the model. No-op (returns false) if `id` is missing or not found. |
| `getUpdateArray(array $mapping, array $data): array` | Projects a row into a model attribute array using a `field => dataKey` map — only keys present in the row are included. The workhorse for column→field mapping. |
| `saveExternalId(Model $model, ?string $externalId, ?string $system = 'default'): void` | Calls `$model->addOrDeleteExternalId(...)` — ties imports to the [HasExternalIds](./traits/index.md#hasexternalids) trait, so imported rows carry their source-system identity. |
| `saveAttributeValuesForModel(Model $model, array $row): void` | Reads the model's dynamic attributes via `GetAttributesValuesForModel` (Attribute module) and, for any row column matching an attribute key (case-/dash-normalized), persists it via `SaveAttributeValueForModel`. **This is why imports can populate EAV attributes by simply adding a column named after the attribute key.** |

---

## The Standard Pattern — `OnEachRow`

17 of the concrete imports follow one shape:

```php
class XImport extends BaseImport implements OnEachRow
{
    public function onRow(Row $row): void
    {
        $rowArray = $row->toArray();
        if ($this->shouldDelete($rowArray)) { $this->deleteModel(X::class, $rowArray); return; }

        $mapping = [ /* field => column */ ];
        $model = X::updateOrCreate(['id' => $rowArray['id'] ?? null],
                                   $this->getUpdateArray($mapping, $rowArray));

        $this->saveAttributeValuesForModel($model, $rowArray);
        $this->saveExternalId($model, $rowArray['external_id'] ?? null);
        // … optionally create related records (addresses, notes, map locations, …)
    }

    public function rules(): array { return [ /* per-column validation */ ]; }
}
```

Conventions that hold across the standard imports:
- **Upsert by `id`** — rows with an `id` update; rows without create. `id` is validated `nullable|exists:<table>,id`.
- **`external_id`** — most imports map an `external_id` column to the [HasExternalIds](./traits/index.md#hasexternalids) trait for idempotent re-imports from a source system.
- **Empty-string → null** — ID/foreign-key columns left blank are coerced to `null` before `updateOrCreate` (see `CustomerImport`).
- **Related-record creation** — an import may reach beyond its primary model: `CustomerImport` also upserts an address + notes + veteran tag; `PropertyImport` optionally creates a `MapLocation`.

The per-import column→field mapping and validation rules are the genuinely import-specific detail. **Each concrete import has its own doc** — co-located in its module at `modules/<module>/imports/<name>.md` — that lists every valid spreadsheet column, whether it's required, its type/constraint, and the conditional rules `rules()` can't express. The registry table below links to each. (Those per-import docs are derived from `rules()` and `onRow()`; the source remains authoritative — re-derive on update.)

---

## Registry of Concrete Imports

All entries reachable from the standard UI come from `Import::getImports()`. Target model is the primary entity each import upserts (related models it also touches are noted).

| Type key | Doc (columns + rules) | Primary model | Module | Also touches |
|---|---|---|---|---|
| `property` | [property](../modules/property/imports/property.md) | [Property](../modules/property/models/property.md) | Property | MapLocation (optional) |
| `property-commitment` | [property-commitment](../modules/property/imports/property-commitment.md) | [PropertyCommitment](../modules/property/models/property-commitment.md) | Property | Property |
| `property-group` | [property-group](../modules/property/imports/property-group.md) | [PropertyGroup](../modules/property/models/property-group.md) | Property | — |
| `customer` | [customer](../modules/customer/imports/customer.md) | [Customer](../modules/customer/models/customer.md) | Customer | Address, Note, VeteranTag |
| `merge-customers` | [merge-customers](../modules/customer/imports/merge-customers.md) | [Customer](../modules/customer/models/customer.md) | Customer | *(merge, not upsert — see Variants)* |
| `interment` | [interment](../modules/interment/imports/interment.md) | [Interment](../modules/interment/models/interment.md) | Interment | Event, Note |
| `owner-file-line` | [owner-file-line](../modules/common/imports/owner-file-line.md) | [OwnerFileLine](../modules/common/models/owner-file-line.md) | Common | OwnerFile, Property |
| `map-location` | [map-location](../modules/mapping/imports/map-location.md) | [MapLocation](../modules/mapping/models/map-location.md) | Mapping | Property |
| `order` | [order](../modules/order/imports/order.md) | [Order](../modules/order/models/order.md) | Order | OrderCustomer, Address |
| `order-line` | [order-line](../modules/order/imports/order-line.md) | [OrderLine](../modules/order/models/order-line.md) | Order | — |
| `payment-plan` | [payment-plan](../modules/payment-plan/imports/payment-plan.md) | [PaymentPlan](../modules/payment-plan/models/payment-plan.md) | PaymentPlan | — |
| `payment` | [payment](../modules/transaction/imports/payment.md) | [Payment](../modules/transaction/models/payment.md) | Transaction | *(create-only; polymorphic parent)* |
| `delivery` | [delivery](../modules/delivery/imports/delivery.md) | [Delivery](../modules/delivery/models/delivery.md) | Delivery | — |
| `delivery-line` | [delivery-line](../modules/delivery/imports/delivery-line.md) | [DeliveryLine](../modules/delivery/models/delivery-line.md) | Delivery | OrderLine, LiabilityLine |
| `certificate-line` | [certificate-line](../modules/certificate/imports/certificate-line.md) | [CertificateLine](../modules/certificate/models/certificate-line.md) | Certificate | — |
| `media` | [media](../modules/common/imports/media.md) | [Media](../modules/common/models/media.md) | Common | Tags |

> Re-derive this table from `Import::getImports()` on every update — the registry is the source of truth, and an import added to source but not yet to the registry will not appear in the UI. Each per-import doc is co-located in its module's `imports/` folder.

---

## Variants & Exceptions (not the standard pattern)

These exist in the codebase and are intentionally called out so the "everything extends BaseImport with OnEachRow" mental model isn't over-applied:

| Class / Doc | How it differs |
|---|---|
| [bulk-file-upload-file](../modules/common/imports/bulk-file-upload-file.md) (`BulkFileUploadFileImport`) | Extends `BaseImport` but implements `ToArray` (whole-sheet array), not `OnEachRow`. Drives the zip/bulk-file upload path (`runZipUpload`), not the standard registry flow. **Unregistered.** |
| [merge-customers](../modules/customer/imports/merge-customers.md) (`MergeCustomersImport`) | Extends `BaseImport` + `OnEachRow`, but performs customer **merge** logic rather than upsert. Registered as `merge-customers` (so it's in the table above too). |
| [location-mapper](../modules/mapping/imports/location-mapper.md) (`Mapping\Livewire\Imports\*`) | A **separate, parallel** system — `LocationMapperImport implements WithMultipleSheets` with `MarkerSheet` / `PropertySheet` (`WithHeadingRow`, currently stub placeholders). Does **not** extend `BaseImport`, **not** in the registry; driven by the Mapping module's own Livewire flow. |

---

## How to Find / Verify (for maintainers)

- **All import classes:** `git show origin/main` over files matching `modules/*/Imports/*.php` and `app/Imports/*.php`.
- **What's actually importable:** `Modules\Common\Support\Imports\Import::getImports()` — the registry, not the file listing (some import files are unregistered variants).
- **Source set for freshness:** this doc's `source_paths` (base + job + livewire + registry) plus each registered import class. A change to `BaseImport` or `ImportJob` affects all imports; a change to one import class affects only its row.

<!-- human:begin -->
## Business Logic Notes
_(Human insight goes here — e.g. operational gotchas, which imports are customer-facing vs. migration-only, sample-file locations, known data-quality caveats. Never regenerated.)_
<!-- human:end -->

## Future Work

- **Per-import column docs** — ✅ Done. Every concrete import has a per-file doc under `modules/<module>/imports/` with its full column reference; linked from the registry table above.
- **Cross-link from model docs** — add an "Imported via" pointer in each target model doc (e.g. [Property](../modules/property/models/property.md), [Customer](../modules/customer/models/customer.md)) back to its import doc. *(Pending — the model docs don't yet reference their imports.)*
- **Codify the pattern** — ✅ Done. The subsystem-doc pattern is now `foundation.md` §5.6 + `meta/subsystem-template.md`; this doc is its reference example.
