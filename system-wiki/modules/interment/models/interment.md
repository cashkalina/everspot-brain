---
model: Interment
module: Interment
table: interments
connection: tenant
primary_source: modules/Interment/Models/Interment.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Interment/Observers/IntermentObserver.php
  - modules/Interment/Providers/IntermentServiceProvider.php
  - modules/Common/Casts/PartialDateCast.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/OwnerFile.php
  - modules/Customer/Models/Customer.php
  - modules/Event/Models/Event.php
  - modules/Certificate/Models/Certificate.php
  - modules/Memorial/Models/Memorial.php
  - modules/Memorial/Models/MemorialPerson.php
  - modules/Property/Models/Property.php
  - modules/WorkOrder/Models/WorkOrder.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasPartialDateScopes
  - HasSearch
  - SoftDeletes
related_models: [Cemetery, Certificate, Customer, Event, ListOption, Memorial, MemorialPerson, Note, OwnerFile, Property, WorkOrder]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, location, core]
---

# Interment

## Overview

The Interment model is the central record for a cemetery burial or placement service. It captures everything from identification of the deceased (name components, dates of birth/death/interment, veteran status) to the operational workflow (scheduling, work orders, events, certificates) and the cemetery space (property/interment space) where the burial takes place.

The model tracks four customer relationships: the deceased (linked to a Customer record), the next of kin, the funeral home, and the funeral director. Partial dates for date of birth, date of death, and date of interment are stored as year/month/day component columns to support cases where only partial date information is known — this mirrors the pattern used on the Customer model and is supported by the `HasPartialDateScopes` trait.

Interment goes through a defined status lifecycle (`awaiting-scheduling` → `awaiting-documents` → `ready` → `finalizing` → `completed`), with optional automatic stage progression managed by a `StatusConfig` strategy. Scheduling is handled by associating an `Event` as the "interment event" and syncing date/time back to the interment record. The model also participates in Spatie MediaLibrary (via `HasFiles`) for documents such as a signed authorization and obituary, and carries EAV custom attributes via `HasAttributes`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| date | date | No | - | Record/filing date |
| model_no | varchar | Yes | - | User-facing interment number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| deceased_id | bigint | No | - | FK → customers: the deceased |
| cemetery_id | bigint | No | - | FK → cemeteries |
| nok_id | bigint | Yes | - | FK → customers: next of kin |
| funeral_home_id | bigint | Yes | - | FK → customers: funeral home |
| funeral_director_id | bigint | Yes | - | FK → customers: funeral director |
| nok_relation_id | bigint | Yes | - | FK → list_options: NOK relationship type |
| status | varchar | No | - | Workflow status (`awaiting-scheduling`, `awaiting-documents`, `ready`, `finalizing`, `completed`) |
| first_name | varchar | Yes | - | Deceased's first name |
| middle_name | varchar | Yes | - | Deceased's middle name |
| last_name | varchar | Yes | - | Deceased's last name |
| suffix_id | bigint | Yes | - | FK → list_options: name suffix |
| nickname | varchar | Yes | - | Deceased's nickname |
| sex_id | bigint | Yes | - | FK → list_options: sex |
| date_of_birth | date | Yes | - | Full date of birth (legacy/computed; see DOB component columns) |
| dob_year | smallint | Yes | - | Date-of-birth year component (partial date) |
| dob_month | tinyint | Yes | - | Date-of-birth month component (partial date) |
| dob_day | tinyint | Yes | - | Date-of-birth day component (partial date) |
| dob_estimated | tinyint | No | 0 | Whether the date of birth is estimated |
| date_of_death | date | Yes | - | Full date of death (legacy/computed; see DOD component columns) |
| dod_year | smallint | Yes | - | Date-of-death year component (partial date) |
| dod_month | tinyint | Yes | - | Date-of-death month component (partial date) |
| dod_day | tinyint | Yes | - | Date-of-death day component (partial date) |
| dod_estimated | tinyint | No | 0 | Whether the date of death is estimated |
| doi_year | smallint | Yes | - | Date-of-interment year component (partial date) |
| doi_month | tinyint | Yes | - | Date-of-interment month component (partial date) |
| doi_day | tinyint | Yes | - | Date-of-interment day component (partial date) |
| doi_estimated | tinyint | No | 0 | Whether the date of interment is estimated |
| toi | time | Yes | - | Time of interment (via `TimezonedDateTime` cast) |
| interment_event_id | bigint | Yes | - | FK → events: the designated scheduling event |
| age | int | Yes | - | Age at death |
| is_veteran | tinyint | No | 0 | Whether the deceased is a veteran |
| interment_type_id | bigint | Yes | - | FK → list_options: interment type |
| service_type_id | bigint | Yes | - | FK → list_options: service type |
| interment_space | varchar | Yes | - | Human-readable interment space description |
| interment_space_id | bigint | Yes | - | FK → properties: the physical interment space |
| deed_number | varchar | Yes | - | Deed number associated with this interment |
| certificate_id | bigint | Yes | - | FK → certificates: associated burial certificate |
| property_owner | varchar | Yes | - | Denormalized property owner name |
| external_comments | text | Yes | - | External-facing comments |
| internal_comments | text | Yes | - | Internal staff comments |
| start_date | date | Yes | - | Scheduled service start date (synced from interment event) |
| start_time | time | Yes | - | Scheduled service start time (synced from interment event) |
| end_date | date | Yes | - | Scheduled service end date (synced from interment event) |
| end_time | time | Yes | - | Scheduled service end time (synced from interment event) |
| config_data | json | Yes | - | Arbitrary configuration data |
| is_manual | tinyint | No | 0 | Whether this interment was entered manually |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `certificate_id` → `certificates.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`; `deceased_id`, `funeral_director_id`, `funeral_home_id`, `nok_id` → `customers.id`; `interment_event_id` → `events.id` (ON DELETE SET NULL); `interment_space_id` → `properties.id`; `interment_type_id`, `nok_relation_id`, `service_type_id`, `sex_id`, `suffix_id` → `list_options.id`

**Indexes:** single-column indexes on `cemetery_id`, `date_of_death`, `deceased_id`, `dob_year`, `dod_year`, `doi_year`, `first_name`, `funeral_home_id`, `is_veteran`, `last_name`, `middle_name`, `model_no`, `nickname`, `nok_id`, `start_date`, `status`; composite indexes on (`dob_year`, `dob_month`), (`dod_year`, `dod_month`), (`doi_year`, `doi_month`); FK-backing indexes on `certificate_id`, `created_by`, `deleted_by`, `funeral_director_id`, `interment_event_id`, `interment_space_id`, `interment_type_id`, `nok_relation_id`, `service_type_id`, `sex_id`, `suffix_id`, `updated_by`.

## Casts

- `is_veteran` → `boolean`
- `date` → `date`
- `dob` → `PartialDateCast::class.':dob'` — composes `dob_year` / `dob_month` / `dob_day` into a partial-date value object
- `dod` → `PartialDateCast::class.':dod'` — composes `dod_year` / `dod_month` / `dod_day` into a partial-date value object
- `doi` → `PartialDateCast::class.':doi'` — composes `doi_year` / `doi_month` / `doi_day` into a partial-date value object
- `start_date` → `date`
- `end_date` → `date`
- `start_time` → `TimezonedDateTime::class` — timezone-aware time
- `end_time` → `TimezonedDateTime::class` — timezone-aware time
- `toi` → `TimezonedDateTime::class` — time of interment, timezone-aware
- `is_manual` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `is_veteran` → `0`, `dob_estimated` → `0`, `dod_estimated` → `0`, `doi_estimated` → `0`, `is_manual` → `0` (all database-level defaults).

**Constants / static config:**
```php
const STATUSES = [
    'awaiting-scheduling' => ['label' => 'Awaiting Scheduling', 'color' => 'danger'],
    'awaiting-documents'  => ['label' => 'Awaiting Documents',  'color' => 'info'],
    'ready'               => ['label' => 'Ready',               'color' => 'success'],
    'finalizing'          => ['label' => 'Finalizing',          'color' => 'secondary'],
    'completed'           => ['label' => 'Completed',           'color' => 'dark'],
];

protected static $defaultStatus = 'awaiting-scheduling';
```

## Accessors & Mutators

- `getSuffixAttribute(): ?string` — name of the related suffix [ListOption](../../common/models/list-option.md)
- `getSexAttribute(): ?string` — name of the related sex [ListOption](../../common/models/list-option.md)
- `getNokRelationAttribute(): ?string` — name of the NOK relation [ListOption](../../common/models/list-option.md)
- `getIntermentTypeAttribute(): ?string` — name of the interment type [ListOption](../../common/models/list-option.md)
- `getServiceTypeAttribute(): ?string` — name of the service type [ListOption](../../common/models/list-option.md)
- `getDeceasedFullNameAttribute(): ?string` — joins `first_name`, `middle_name`, `last_name`, and `suffix` (non-null parts, space-separated, trimmed)
- `getDeceasedInitialsAttribute(): ?string` — up to 3 uppercase initials from first/middle/last name
- `getLifeDatesAttribute(): ?string` — formatted string `"DOB - DOD"` using `dob->toString()` and `dod->toString()`; returns `null` when neither is set

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for storing dynamic per-interment fields
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `IntermentFactory`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary attachments (signed authorization, obituary, and dynamic collections)
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) — query scopes over `dob_year`/`dob_month`/`dob_day`, `dod_year`/`dod_month`/`dod_day`, and `doi_year`/`doi_month`/`doi_day` partial-date columns
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; searchable payload built in `addToSearchData()`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — interments are soft-deleted, never hard-deleted

## Relationships

**People:**
- `deceased()` — belongs to [Customer](../../customer/models/customer.md) (`deceased_id`): the deceased person
- `nextOfKin()` — belongs to [Customer](../../customer/models/customer.md) (`nok_id`): next of kin
- `funeralHome()` — belongs to [Customer](../../customer/models/customer.md) (`funeral_home_id`): the funeral home
- `funeralDirector()` — belongs to [Customer](../../customer/models/customer.md) (`funeral_director_id`): the funeral director

**Reference data:**
- `nokRelationOption()` — belongs to [ListOption](../../common/models/list-option.md) (`nok_relation_id`): NOK relationship type
- `suffixOption()` — belongs to [ListOption](../../common/models/list-option.md) (`suffix_id`): name suffix
- `sexOption()` — belongs to [ListOption](../../common/models/list-option.md) (`sex_id`): sex
- `intermentTypeOption()` — belongs to [ListOption](../../common/models/list-option.md) (`interment_type_id`): interment type
- `serviceTypeOption()` — belongs to [ListOption](../../common/models/list-option.md) (`service_type_id`): service type

**Cemetery & property:**
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery
- `intermentSpaceObject()` — belongs to [Property](../../property/models/property.md) (`interment_space_id`): the physical property/space

**Events & scheduling:**
- `events()` — morphMany [Event](../../event/models/event.md) (`eventable`): all calendar events for this interment
- `intermentEvent()` — belongs to [Event](../../event/models/event.md) (`interment_event_id`): the designated scheduling event whose dates sync back to the interment

**Work & documents:**
- `workOrders()` — has many [WorkOrder](../../work-order/models/work-order.md): work orders for this interment
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): notes
- `certificate()` — belongs to [Certificate](../../certificate/models/certificate.md): associated burial certificate
- `signedAuthorization()` — morphOne media model (`collection_name = signed_authorization`): the signed authorization document
- `obituary()` — morphOne media model (`collection_name = obituary`): the obituary document

**Memorial:**
- `memorialPerson()` — has one [MemorialPerson](../../memorial/models/memorial-person.md): the memorial person record linked to this interment
- `memorial()` — has one through [Memorial](../../memorial/models/memorial.md) (through MemorialPerson): the primary memorial
- `memorials()` — has many through [Memorial](../../memorial/models/memorial.md) (through MemorialPerson): all memorials

## Scopes

- `next7Days(Builder $query)` — returns incomplete interments whose `start_date` falls within the next 7 days (or have no start date), ordered by `start_date` and `start_time`
- `last7Days(Builder $query)` — returns interments whose `start_date` falls in the past 7 days, ordered by `start_date` desc

Partial-date scopes over the DOB/DOD/DOI component columns are contributed by [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) (see trait doc).

## Events

_None defined on the model._ Lifecycle behavior is handled by `IntermentObserver` (see Observers).

## Observers

- `IntermentObserver` — registered in `IntermentServiceProvider::registerObservers()` (`Interment::observe(IntermentObserver::class)`). Handles:
  - `saving` — dispatches `IntermentSaving` event
  - `saved` — dispatches `IntermentSaved` event (with previous `deceased_id` if it changed)
  - `created` — dispatches `IntermentCreated` event; fires `analytics()->track('Interment Created')`
  - `deleting` — wraps deletion in a DB transaction running `PreDeleteInterment` checks
  - `deleted` — dispatches `IntermentDeleted` event

## Key Methods

- `event(): ?Event` — returns the first event by `start_date` / `start_time` from the `events()` collection (earliest upcoming)
- `ownerFile(): ?OwnerFile` — delegates to `$this->intermentSpaceObject?->ownerFile()` to get the owner file for the interment space
- `ownerFiles(): Collection` — returns all unique owner files linked via the interment space property's commitments
- `canBeScheduled(): bool` — returns `true` when no events are associated with this interment
- `updateDateTimes(): void` — syncs `start_date`, `start_time`, `end_date`, `end_time`, `doi`, and `toi` from the designated `intermentEvent`; saves quietly to avoid re-triggering the event sync
- `getStatusConfig(): StatusConfig` — returns the type-specific status configuration object via `StatusConfigFactory`
- `manageStagesAutomatically(): void` — delegates to `getStatusConfig()->manageAutoProgression()` to auto-advance workflow status
- `hasIntermentEventMismatch(): bool` — returns `true` when the stored DOI/TOI does not match the interment event's start date/time, or when DOI is incomplete or estimated
- `getIntermentEventMismatchMessage(): ?string` — returns a human-readable mismatch message, or `null` if there is no mismatch
- `getPdfEmailContacts(): array` — returns an array of contact definitions (customer + label) for PDF email recipients: next of kin, funeral home, funeral director
- `addToSearchData(): array` — provides `deceased_full_name`, `nok_full_name`, `nok_contact_email`, `nok_contact_phone`, `deed_number` to the search index
- `getModelInferredName(): ?string` — returns `deceased_full_name`; used by `HasModelNumbering` for display

## Factory & Seeders

Uses `IntermentFactory` via `newFactory()` override. Factory path: `modules/Interment/Database/Factories/IntermentFactory.php`.

## Common Usage

```php
// Create an interment
$interment = Interment::create([
    'date'         => today(),
    'deceased_id'  => $deceased->id,
    'cemetery_id'  => $cemetery->id,
    'first_name'   => 'Jane',
    'last_name'    => 'Smith',
    'status'       => 'awaiting-scheduling',
    'is_veteran'   => false,
]);

// Display names and life dates
echo $interment->deceased_full_name;  // "Jane Smith"
echo $interment->life_dates;          // "1935 - 2024" (from partial dates)

// Scheduling check
if ($interment->canBeScheduled()) {
    // Attach an event and sync dates
    $interment->intermentEvent()->associate($event);
    $interment->save();
    $interment->updateDateTimes();
}

// Upcoming and past interments
$upcoming = Interment::next7Days()->get();
$recent   = Interment::last7Days()->get();

// Auto-advance workflow
$interment->manageStagesAutomatically();

// PDF email contacts
$contacts = $interment->getPdfEmailContacts();
// [['customer' => $nok, 'label' => 'Next of Kin'], ...]
```

## Imports

This model can be created/updated via spreadsheet import. See **[interment](../imports/interment.md)** for the column reference (valid headers, required fields, types, and conditional rules).

The import mechanism (upload → queued job → Excel) is documented in the [import subsystem](../../../system/imports.md).

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
