---
title: Trait Registry
purpose: Global lookup for every trait used across Everspot models
last_updated: 2026-06-14
---

# Trait Registry

This is the **single global lookup table** for traits used by Everspot models. Trait behavior is documented once and linked everywhere, per the DRY rule (foundation §5.1, conventions "Traits Documentation").

## How to use this registry

1. A model doc's `## Traits` section links each trait here (by anchor, e.g. `index.md#hasfiles`).
2. Each row below gives a one-line description and the **owning module**.
3. The **Deep doc** column links to the full trait documentation, which lives **in the owning module** (e.g. `modules/common/traits/has-files.md`). The deep doc owns the trait's contributed columns, casts, scopes, relationships, and configuration.

When a model uses a trait, follow: model doc → this registry → deep doc. The same trait is referenced from the same place across every model that uses it.

## Conventions

- **Anchor:** the trait's short name lowercased (e.g. `HasFiles` → `#hasfiles`). Model docs link to these anchors.
- **Owning module:** the module whose `Traits/` directory contains the trait source. Laravel/framework traits (e.g. `SoftDeletes`, `HasFactory`) have no owning module — their deep doc is a short note here in `system/traits/` since no Everspot module owns them.
- **Source path:** the trait file relative to the Everspot repo root; this is what freshness checks resolve a model's `traits:` entries to.
- Add a row whenever a model's generation surfaces a trait not yet listed (Generate §2.5b). Keep alphabetical.

## Registry

| Trait | Description | Owning module | Source path | Deep doc |
|-------|-------------|---------------|-------------|----------|
| <a id="hasattributes"></a>**HasAttributes** | EAV-style custom attributes: morphs to attribute values, helpers like `getAV()`/`getAVValue()` for reading dynamic per-entity attributes. | Attribute | `modules/Attribute/Traits/HasAttributes.php` | _pending_ |
| <a id="hasbyuserfields"></a>**HasByUserFields** | Audit user stamps: `createdBy()` / `updatedBy()` / `deletedBy()` relationships backed by `created_by` / `updated_by` / `deleted_by` columns. | Common | `modules/Common/Traits/HasByUserFields.php` | _pending_ |
| <a id="hasfactory"></a>**HasFactory** | Laravel's model-factory hook (`factory()`). Framework trait — no owning module. | _(framework)_ | `Illuminate\Database\Eloquent\Factories\HasFactory` | _pending_ |
| <a id="hasfiles"></a>**HasFiles** | Spatie MediaLibrary file attachments: registers media collections and exposes attached files/images on the model. | Common | `modules/Common/Traits/HasFiles.php` | _pending_ |
| <a id="hasmodelnumbering"></a>**HasModelNumbering** | User-facing record numbers: generates `model_no` via `generateModelNumber()` from a per-model numbering configuration. | Common | `modules/Common/Traits/HasModelNumbering.php` | _pending_ |
| <a id="haspartialdatescopes"></a>**HasPartialDateScopes** | Query scopes for partial date fields stored as year/month/day component columns (e.g. `dob_year`/`dob_month`/`dob_day`). | Common | `modules/Common/Traits/HasPartialDateScopes.php` | _pending_ |
| <a id="hassearch"></a>**HasSearch** | Search indexing: defines `toSearchableArray()` for the model's searchable representation. | Common | `modules/Common/Traits/HasSearch.php` | _pending_ |
| <a id="hassyncables"></a>**HasSyncables** | External-integration sync linkage: `syncable()`/`syncables()` and per-integration lookups for mapping records to integrations (e.g. QuickBooks). | Common | `modules/Common/Traits/HasSyncables.php` | _pending_ |
| <a id="softdeletes"></a>**SoftDeletes** | Laravel soft deletes: adds `deleted_at`, scopes out trashed rows, enables restore. Framework trait — no owning module. | _(framework)_ | `Illuminate\Database\Eloquent\SoftDeletes` | _pending_ |

_Deep docs are stubbed as `_pending_` until written. They will live at `modules/<module>/traits/<trait-kebab>.md` for module-owned traits, and `system/traits/<trait-kebab>.md` for framework traits._
