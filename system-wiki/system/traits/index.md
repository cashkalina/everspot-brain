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
| <a id="hasapprovals"></a>**HasApprovals** | Internal approval workflow: polymorphic `ApprovalRequest` relationship, lock-checking, quick-approve path. | Approval | `modules/Approval/Traits/HasApprovals.php` | [has-approvals.md](../../modules/approval/traits/has-approvals.md) |
| <a id="hasattributes"></a>**HasAttributes** | EAV-style custom attributes: morphs to attribute values, helpers like `getAV()`/`getAVValue()` for reading dynamic per-entity attributes. | Attribute | `modules/Attribute/Traits/HasAttributes.php` | [has-attributes.md](../../modules/attribute/traits/has-attributes.md) |
| <a id="hasbyuserfields"></a>**HasByUserFields** | Audit user stamps: `createdBy()` / `updatedBy()` / `deletedBy()` relationships backed by `created_by` / `updated_by` / `deleted_by` columns. | Common | `modules/Common/Traits/HasByUserFields.php` | [has-by-user-fields.md](../../modules/common/traits/has-by-user-fields.md) |
| <a id="hascolor"></a>**HasColor** | Hex color storage and UI helpers: `getColor()`, `getTextColor()` (contrast), `getColorWithOpacity()`. | Event | `modules/Event/Traits/HasColor.php` | [has-color.md](../../modules/event/traits/has-color.md) |
| <a id="hasdatabase"></a>**HasDatabase** | Stancl Tenancy — per-tenant database provisioning and migration. Framework trait — no owning module. | _(framework)_ | `Stancl\Tenancy\Database\Concerns\HasDatabase` | [has-database.md](./has-database.md) |
| <a id="hasdatestatusfields"></a>**HasDateStatusFields** | Date-driven fulfillment status from delivery/constructive/cancellation/deed date columns; scopes `open()` and `notCanceled()`. | Common | `modules/Common/Traits/HasDateStatusFields.php` | [has-date-status-fields.md](../../modules/common/traits/has-date-status-fields.md) |
| <a id="hasdomains"></a>**HasDomains** | Stancl Tenancy — domain-to-tenant routing via the `domains` table. Framework trait — no owning module. | _(framework)_ | `Stancl\Tenancy\Database\Concerns\HasDomains` | [has-domains.md](./has-domains.md) |
| <a id="hasexternalapprovals"></a>**HasExternalApprovals** | External approval workflow: polymorphic `ExternalApprovalRequest` relationship, available type lookup, config resolution. | Approval | `modules/Approval/Traits/HasExternalApprovals.php` | [has-external-approvals.md](../../modules/approval/traits/has-external-approvals.md) |
| <a id="hasexternalids"></a>**HasExternalIds** | Polymorphic multi-system external identifier storage: `addExternalId()`, `getExternalId()`, `hasExternalId()` keyed by system name. | Common | `modules/Common/Traits/HasExternalIds.php` | [has-external-ids.md](../../modules/common/traits/has-external-ids.md) |
| <a id="hasfactory"></a>**HasFactory** | Laravel's model-factory hook (`factory()`). Framework trait — no owning module. | _(framework)_ | `Illuminate\Database\Eloquent\Factories\HasFactory` | [has-factory.md](./has-factory.md) |
| <a id="hasfiles"></a>**HasFiles** | Spatie MediaLibrary file attachments: registers dynamic media collections driven by `ListOption` rows and exposes attached files/images. | Common | `modules/Common/Traits/HasFiles.php` | [has-files.md](../../modules/common/traits/has-files.md) |
| <a id="hasicon"></a>**HasIcon** | Static Bootstrap Icon class mapping for model classes: `getIcon()` / `getBootstrapIconClass()`. | Common | `modules/Common/Traits/HasIcon.php` | [has-icon.md](../../modules/common/traits/has-icon.md) |
| <a id="hasmodeldefinition"></a>**HasModelDefinition** | Resolves and returns a `ModelDefinition` instance for the model via convention or explicit `$definitionClass`. | Definition | `modules/Definition/Traits/HasModelDefinition.php` | [has-model-definition.md](../../modules/definition/traits/has-model-definition.md) |
| <a id="hasmodelnumbering"></a>**HasModelNumbering** | User-facing record numbers: generates `model_no` via `generateModelNumber()` from a per-model `ModelNumberConfiguration` row. | Common | `modules/Common/Traits/HasModelNumbering.php` | [has-model-numbering.md](../../modules/common/traits/has-model-numbering.md) |
| <a id="hasmodificationrules"></a>**HasModificationRules** | Lifecycle gate via strategy pattern: `canBeEdited()`, `canBeDeleted()`, `canBeVoided()`, `canBeSubmittedForApproval()`, `isLocked()`. | Common | `modules/Common/Traits/HasModificationRules.php` | [has-modification-rules.md](../../modules/common/traits/has-modification-rules.md) |
| <a id="hasmoneyfields"></a>**HasMoneyFields** | Transparent cents-to-dollars conversion for money columns declared in `$moneyAttributes`; `formatMoney()`, `fromCents()`, `toCents()`. | Common | `modules/Common/Traits/HasMoneyFields.php` | [has-money-fields.md](../../modules/common/traits/has-money-fields.md) |
| <a id="haspartialdatescopes"></a>**HasPartialDateScopes** | Query scopes for partial date fields stored as year/month/day component columns (e.g. `dob_year`/`dob_month`/`dob_day`). | Common | `modules/Common/Traits/HasPartialDateScopes.php` | [has-partial-date-scopes.md](../../modules/common/traits/has-partial-date-scopes.md) |
| <a id="hasrecognition"></a>**HasRecognition** | Recognition module integration: polymorphic `RecognitionArrangement`/`RecognitionElement` relationships; cascades updates to arrangements. | Recognition | `modules/Recognition/Traits/HasRecognition.php` | [has-recognition.md](../../modules/recognition/traits/has-recognition.md) |
| <a id="hasschemalessattributes"></a>**HasSchemalessAttributes** | Spatie SchemalessAttributes: `config_data` JSON column with dot-notation access for arbitrary key-value pairs; `scopeWithExtraAttributes()`. | Common | `modules/Common/Traits/HasSchemalessAttributes.php` | [has-schemaless-attributes.md](../../modules/common/traits/has-schemaless-attributes.md) |
| <a id="hassearch"></a>**HasSearch** | Laravel Scout search indexing: `toSearchableArray()` with standard columns, global special cases, and per-model `addToSearchData()`/`removeFromSearchData()` hooks. | Common | `modules/Common/Traits/HasSearch.php` | [has-search.md](../../modules/common/traits/has-search.md) |
| <a id="hassettings"></a>**HasSettings** | Key-value settings store via polymorphic `Setting` model; all ops routed through `settingSvc()` for caching. | Common | `modules/Common/Traits/HasSettings.php` | [has-settings.md](../../modules/common/traits/has-settings.md) |
| <a id="hassharing"></a>**HasSharing** | Fine-grained sharing with users, roles, cemeteries, departments, or public; permission-level hierarchy via `SharePermissionRegistry`. | Common | `modules/Common/Support/Sharing/Traits/HasSharing.php` | [has-sharing.md](../../modules/common/traits/has-sharing.md) |
| <a id="hassyncables"></a>**HasSyncables** | External-integration sync linkage: `syncable()`/`syncables()` and per-integration lookups for mapping records to integrations (e.g. QuickBooks). | Common | `modules/Common/Traits/HasSyncables.php` | [has-syncables.md](../../modules/common/traits/has-syncables.md) |
| <a id="hastags"></a>**HasTags** | Spatie Tags: polymorphic tagging via `tags()` relationship and sync/attach/detach helpers. Framework trait — no owning module. | _(framework)_ | `Spatie\Tags\HasTags` | [has-tags.md](./has-tags.md) |
| <a id="hastimeentries"></a>**HasTimeEntries** | Time-tracking via polymorphic `TimeEntry` model; `calculateTotalTime()` updates `time_spent` column. | WorkOrder | `modules/WorkOrder/Traits/HasTimeEntries.php` | [has-time-entries.md](../../modules/work-order/traits/has-time-entries.md) |
| <a id="hastrusting"></a>**HasTrusting** | Trust module integration: polymorphic `TrustArrangement`/`TrustElement` relationships; cascades updates to trust arrangements. | Trust | `modules/Trust/Traits/HasTrusting.php` | [has-trusting.md](../../modules/trust/traits/has-trusting.md) |
| <a id="interactswithmedia"></a>**InteractsWithMedia** | Spatie MediaLibrary core: media attachment, collections, conversions, and `media()` relationship. Framework trait — no owning module. Used via `HasFiles` in most models. | _(framework)_ | `Spatie\MediaLibrary\InteractsWithMedia` | [interacts-with-media.md](./interacts-with-media.md) |
| <a id="logsactivity"></a>**LogsActivity** | Spatie Activitylog: auto-logs create/update/delete events to `activity_log`. Framework trait — no owning module. Applied on `BaseModel`. | _(framework)_ | `Spatie\Activitylog\Traits\LogsActivity` | [logs-activity.md](./logs-activity.md) |
| <a id="repeatable"></a>**Repeatable** | Recurrence scheduling via polymorphic `Repetition` model; `repeat()` fluent builder, date-occurrence scopes. | Repetition | `modules/Repetition/Traits/Repeatable.php` | [repeatable.md](../../modules/repetition/traits/repeatable.md) |
| <a id="softdeletes"></a>**SoftDeletes** | Laravel soft deletes: adds `deleted_at`, scopes out trashed rows, enables restore. Framework trait — no owning module. | _(framework)_ | `Illuminate\Database\Eloquent\SoftDeletes` | [soft-deletes.md](./soft-deletes.md) |
