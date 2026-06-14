---
model: VeteranTag
module: Customer
table: veteran_tags
connection: tenant
primary_source: modules/Customer/Models/VeteranTag.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Customer/Observers/VeteranTagObserver.php
  - modules/Customer/Providers/CustomerServiceProvider.php
  - modules/Customer/Models/Customer.php
  - modules/Common/Models/Country.php
  - modules/Common/Models/ListOption.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [Country, Customer, ListOption]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [customer, core]
---

# VeteranTag

## Overview

The VeteranTag model stores military service information for a customer. It is a one-to-one extension of the [Customer](./customer.md) model — each customer who served in the military can have a single `VeteranTag` record capturing branch of service, service status, rank, discharge status, service dates, military occupational specialty (MOS), unit, awards, and wars/conflicts served in.

All enumerated fields (branch, service status, rank, discharge status, awards, wars) are backed by [ListOption](../../common/models/list-option.md) lookups and each has a companion `_other` free-text column for values not in the controlled list. The model carries soft deletes and audit user stamps via traits. When a veteran tag is saved or deleted, the `VeteranTagObserver` dispatches `VeteranTagSaved` or `VeteranTagDeleted` events respectively, enabling downstream reactions (such as triggering interment badge updates).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| customer_id | bigint | No | - | FK → customers: the customer this veteran record belongs to |
| country_id | bigint | Yes | - | FK → countries: country of service |
| branch_id | bigint | Yes | - | FK → list_options: branch of military service |
| branch_other | varchar | Yes | - | Free-text branch when not in list |
| service_status_id | bigint | Yes | - | FK → list_options: service status |
| service_status_other | varchar | Yes | - | Free-text service status when not in list |
| rank_id | bigint | Yes | - | FK → list_options: rank |
| rank_other | varchar | Yes | - | Free-text rank when not in list |
| discharge_status_id | bigint | Yes | - | FK → list_options: discharge status |
| discharge_status_other | varchar | Yes | - | Free-text discharge status when not in list |
| awards_other | text | Yes | - | Free-text awards not covered by list entries |
| wars_other | text | Yes | - | Free-text wars/conflicts not covered by list entries |
| unit | text | Yes | - | Military unit |
| mos | text | Yes | - | Military occupational specialty |
| start_date | date | Yes | - | Service start date |
| end_date | date | Yes | - | Service end date |
| additional_notes | text | Yes | - | Freeform additional notes |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `customer_id` → `customers.id`; `country_id` → `countries.id`; `branch_id`, `service_status_id`, `rank_id`, `discharge_status_id` → `list_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `veteran_tags_customer_id_index` on `customer_id`; FK-backing indexes on `country_id`, `branch_id`, `service_status_id`, `rank_id`, `discharge_status_id`, `created_by`, `updated_by`, `deleted_by`.

**Note:** `start_date` and `end_date` are stored as `date` in the database but cast to `TimezonedDateTime` in the model (see Casts).

## Casts

- `start_date` → `TimezonedDateTime::class` — service start date with timezone-aware handling (see `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)
- `end_date` → `TimezonedDateTime::class` — service end date with timezone-aware handling

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getBranchAttribute(): ?string` — name of the related branch [ListOption](../../common/models/list-option.md) (`branchOption?->name`)
- `getServiceStatusAttribute(): ?string` — name of the related service status [ListOption](../../common/models/list-option.md) (`serviceStatusOption?->name`)
- `getRankAttribute(): ?string` — name of the related rank [ListOption](../../common/models/list-option.md) (`rankOption?->name`)
- `getDischargeStatusAttribute(): ?string` — name of the related discharge status [ListOption](../../common/models/list-option.md) (`dischargeStatusOption?->name`)
- `getFormattedServiceDatesAttribute(): ?string` — formatted service date range (`"MM/DD/YYYY - MM/DD/YYYY"`), returns `null` if both dates are empty; falls back to `"Unknown"` for a missing start or end
- `getFormattedBranchAttribute(): ?string` — branch name combined with `branch_other` via `stringifyWithOther()`, pipe-separated
- `getFormattedServiceStatusAttribute(): ?string` — service status combined with `service_status_other` via `stringifyWithOther()`
- `getFormattedRankAttribute(): ?string` — rank combined with `rank_other` via `stringifyWithOther()`
- `getFormattedDischargeStatusAttribute(): ?string` — discharge status combined with `discharge_status_other` via `stringifyWithOther()`

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — veteran tags are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `customer()` — belongs to [Customer](./customer.md) (`customer_id`): the customer this veteran record belongs to
- `country()` — belongs to [Country](../../common/models/country.md) (`country_id`): country of service
- `branchOption()` — belongs to [ListOption](../../common/models/list-option.md) (`branch_id`): branch of military service lookup
- `serviceStatusOption()` — belongs to [ListOption](../../common/models/list-option.md) (`service_status_id`): service status lookup
- `rankOption()` — belongs to [ListOption](../../common/models/list-option.md) (`rank_id`): rank lookup
- `dischargeStatusOption()` — belongs to [ListOption](../../common/models/list-option.md) (`discharge_status_id`): discharge status lookup
- `awards()` — belongs-to-many [ListOption](../../common/models/list-option.md) via `award_veteran_tag` (`veteran_tag_id` / `award_id`): awarded honors
- `wars()` — belongs-to-many [ListOption](../../common/models/list-option.md) via `veteran_tag_war` (`veteran_tag_id` / `war_id`): wars/conflicts served in

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle events are dispatched by `VeteranTagObserver` (see Observers).

## Observers

- `VeteranTagObserver` — registered in `CustomerServiceProvider::registerObservers()` (`VeteranTag::observe(VeteranTagObserver::class)`). Handles:
  - `saved` — dispatches `VeteranTagSaved` event
  - `deleted` — dispatches `VeteranTagDeleted` event
  - `created`, `updated`, `restored`, `forceDeleted` — no-op stubs (present but empty)

## Key Methods

- `modelReportFilters(): array` *(static)* — returns the standard model-report filter set for this model (used by the reporting module); includes the model-number filter with id `veteran-tag-1`
- `modelReportRelations(): array` *(static)* — returns the reportable relation descriptors; exposes the `customer` relation for model-report join configuration
- `getModelTitleSuffix(): ?string` — returns a display suffix combining the owning customer's full name and model identifier, used in admin/reporting UI titles
- `stringifyWithOther(string $field): ?string` *(protected)* — combines a [ListOption](../../common/models/list-option.md)-backed `$field` value and its corresponding `{$field}_other` free-text into a single pipe-separated string; returns `null` if both are empty

## Common Usage

```php
// Retrieve a customer's veteran tag (null if not a veteran)
$veteranTag = $customer->veteranTag;

// Create a veteran tag for a customer
$veteranTag = VeteranTag::create([
    'customer_id'       => $customer->id,
    'country_id'        => $usa->id,
    'branch_id'         => $armyOption->id,
    'service_status_id' => $veteranOption->id,
    'rank_id'           => $sgtOption->id,
    'start_date'        => '1970-03-01',
    'end_date'          => '1973-12-15',
    'mos'               => '11B',
    'unit'              => '1st Infantry Division',
]);

// Attach awards and wars
$veteranTag->awards()->sync([$purpleHeartOption->id, $bronzeStarOption->id]);
$veteranTag->wars()->sync([$vietnamOption->id]);

// Display helpers
echo $veteranTag->formatted_branch;           // "Army" or "Army | Other: Coast Guard Reserve"
echo $veteranTag->formatted_service_dates;    // "03/01/1970 - 12/15/1973"

// Soft-delete (observer dispatches VeteranTagDeleted)
$veteranTag->delete();

// Restore
$veteranTag->restore();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
