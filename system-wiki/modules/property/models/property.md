---
model: Property
module: Property
table: properties
connection: tenant
primary_source: modules/Property/Models/Property.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Property/Observers/PropertyObserver.php
  - modules/Property/Providers/PropertyServiceProvider.php
  - modules/Property/Models/PropertyType.php
  - modules/Property/Models/PropertyGroup.php
  - modules/Property/Models/PropertyCommitment.php
  - modules/Common/Models/Cemetery.php
  - modules/Interment/Models/Interment.php
  - modules/Certificate/Models/CertificateLine.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Order/Models/OrderLine.php
  - modules/Trust/Models/TrustingScheduleGroup.php
  - modules/Mapping/Models/MapLocation.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/OwnerFile.php
  - modules/Memorial/Models/Memorial.php
  - modules/WorkOrder/Models/WorkOrder.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasExternalApprovals
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasMoneyFields
  - HasSearch
  - SoftDeletes
related_models: [Cemetery, CertificateLine, Interment, LiabilityLine, MapLocation, Memorial, Note, OrderLine, OwnerFile, PropertyCommitment, PropertyGroup, PropertyType, TrustingScheduleGroup, WorkOrder]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, location, core]
---

# Property

## Overview

The `Property` model represents a single interment space or lot within a cemetery — the fundamental unit of cemetery inventory. Each property belongs to a [PropertyGroup](./property-group.md) (a named section or block) and is classified by a [PropertyType](./property-type.md). Properties are associated with a specific [Cemetery](../../common/models/cemetery.md) and may be linked to a mapping layer via `MapLocation` for spatial visualization.

A property's availability is determined by its active [PropertyCommitment](./property-commitment.md) records. When no active commitment exists the property is available for sale or reservation; when one or more active commitments exist it is considered occupied. The model exposes several availability-aware scopes and helper methods for this purpose.

Properties carry two money columns (`sale_price`, `cost_price`) stored as integer cents and exposed as dollars via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields). They also carry EAV custom attributes (via [HasAttributes](../../../system/traits/index.md#hasattributes)) that drive the human-readable `description` field, which is rebuilt automatically on every save by `PropertyObserver`. File attachments, search indexing, model numbering, external-approval workflows, and external-system sync are all handled through traits.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| property_type_id | bigint | No | - | FK → property_types: classification of this space |
| property_group_id | bigint | No | - | FK → property_groups: section/block this space belongs to |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery this space is in |
| model_no | varchar | Yes | - | User-facing property number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| description | text | Yes | - | Human-readable description built from EAV attribute values (rebuilt by observer on every save) |
| trusting_schedule_group_id | bigint | Yes | - | FK → trusting_schedule_groups: trust schedule group for this property |
| sale_price | int | Yes | - | Sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — exposed as dollars) |
| cost_price | int | Yes | - | Cost price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — exposed as dollars) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `property_type_id` → `property_types.id`; `property_group_id` → `property_groups.id`; `cemetery_id` → `cemeteries.id`; `trusting_schedule_group_id` → `trusting_schedule_groups.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `properties_cemetery_id_index` on `cemetery_id`; `properties_model_no_index` on `model_no`; `properties_property_group_id_index` on `property_group_id`; FK-backing indexes on `property_type_id`, `trusting_schedule_group_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

_None declared directly on the model._ Money columns (`sale_price`, `cost_price`) are handled by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc.

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._ (accessors are read on demand, not auto-appended)
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
public array $moneyAttributes = ['sale_price', 'cost_price'];
```

## Accessors & Mutators

- `getFullNameAttribute(): string` — combines `model_no` and `description` as `"{model_no} - {description}"`
- `getAvailableBadgeAttribute(): string` — HTML badge (`Available` in green / `Unavailable` in red) based on `isAvailable()`

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for location/property-specific data; drives the `description` field via `attributeValues()`
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasExternalApprovals](../../../system/traits/index.md#hasexternalapprovals) — external approval workflow (polymorphic `ExternalApprovalRequest` relationship)
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (`PropertyFactory`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments for property documents and images
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `sale_price` and `cost_price`
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; searchable payload built in `addToSearchData()`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — properties are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `propertyType()` — belongs to [PropertyType](./property-type.md) (`property_type_id`): classification of this interment space
- `propertyGroup()` — belongs to [PropertyGroup](./property-group.md) (`property_group_id`): the section or block this space belongs to
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery this space is in
- `propertyCommitments()` — has many [PropertyCommitment](./property-commitment.md): all commitments (reservations and sales) for this property
- `activeCommitment()` — has one [PropertyCommitment](./property-commitment.md) scoped to `active()`: the current active commitment, if any
- `interments()` — has many [Interment](../../interment/models/interment.md) (`interment_space_id`): interments using this property as their space
- `certificateLines()` — has many [CertificateLine](../../certificate/models/certificate-line.md): certificate lines referencing this property
- `liabilityLines()` — has many [LiabilityLine](../../liability/models/liability-line.md): liability lines linked to this property
- `orderLines()` — has many [OrderLine](../../order/models/order-line.md): order lines referencing this property
- `trustingScheduleGroup()` — belongs to [TrustingScheduleGroup](../../trust/models/trusting-schedule-group.md) (`trusting_schedule_group_id`): trust scheduling group
- `mapLocation()` — morph one [MapLocation](../../mapping/models/map-location.md) (`record`): the single primary map pin for this property
- `mapLocations()` — morph many [MapLocation](../../mapping/models/map-location.md) (`record`): all map locations associated with this property
- `notes()` — morph many [Note](../../common/models/note.md) (`notable`): notes attached to this property
- `memorials()` — belongs-to-many [Memorial](../../memorial/models/memorial.md) via `memorial_properties`: memorials placed on this property
- `workOrders()` — belongs-to-many [WorkOrder](../../work-order/models/work-order.md) via `property_work_orders`: work orders for this property

## Scopes

- `available(Builder $query)` — filters to properties with no active commitment (`whereDoesntHave('propertyCommitments', fn → active())`)
- `notAvailable(Builder $query)` — filters to properties with at least one active commitment
- `availableExceptParent(Builder $query, $parent)` — available properties excluding a given parent entity's active commitment (used during re-commitment flows)
- `availableExceptCommitmentId(Builder $query, $commitmentId)` — available properties excluding a specific commitment id (used when editing an existing commitment)

## Events

_None defined on the model._ Lifecycle behavior is handled by `PropertyObserver` (see Observers).

## Observers

- `PropertyObserver` — registered in `PropertyServiceProvider::registerObservers()` (`Property::observe(PropertyObserver::class)`). Handles:
  - `saved` — calls `generateDescription()` to rebuild the EAV-driven `description` field
  - `created` — fires `analytics()->track('Property Created')`
  - `deleting` — wraps deletion in a DB transaction and runs `PreDeleteProperty` checks

## Key Methods

- `previewDescription(array $attributeValues): ?string` *(static)* — builds a pipe-separated description string from a pre-fetched array of EAV attribute values (sorted by `sort_order`); returns `null` if no values produce content
- `generateDescription(): void` — queries EAV attribute values scoped to `'location-property'` area code, builds the pipe-separated description string, and persists it if changed
- `getModelInferredName(): ?string` — returns `$this->description`; hooks `BaseModel`'s title system
- `activePropertyCommitment(): ?PropertyCommitment` — queries for and returns the first active commitment, or `null`
- `getCertificates(): Builder` — returns a distinct `Certificate` builder scoped to certificates that have lines referencing this property (via `CertificateLine`)
- `isAvailable(): bool` — returns `true` when no active commitment exists (DB query)
- `loadedActivePropertyCommitment(): ?PropertyCommitment` — returns the active commitment from the already-loaded `propertyCommitments` collection (avoids extra queries)
- `isAvailableFromLoaded(): bool` — availability check against the loaded collection (no DB hit)
- `isAvailableExcept($parent): bool` — availability check excluding a specific parent entity's commitment
- `ownerFile(): ?OwnerFile` — resolves the `OwnerFile` through the active commitment's `ownerFileLine` (non-relationship helper)
- `ownerFiles(): Collection` — collects all unique `OwnerFile` records linked via active commitments' owner-file lines
- `addToSearchData(): array` — builds the searchable representation (description + location EAV attribute values) for [HasSearch](../../../system/traits/index.md#hassearch)
- `getMapLocation(): ?MapLocation` — returns the first map location with its map eagerly loaded

## Common Usage

```php
// Find available properties in a section
$available = Property::available()->where('property_group_id', $group->id)->get();

// Check availability
if ($property->isAvailable()) {
    // proceed with commitment
}

// Get availability badge for UI
echo $property->available_badge;  // HTML badge

// Full name for display
echo $property->full_name;  // "P001 - Section A, Row 1, Space 3"

// Active commitment
$commitment = $property->activeCommitment;

// Related interments
$interments = $property->interments;

// Get certificates linked through certificate lines
$certificates = $property->getCertificates()->get();

// Work orders for the property
$workOrders = $property->workOrders;
```

## Imports

This model can be created/updated via spreadsheet import. See **[property](../imports/property.md)** for the column reference (valid headers, required fields, types, and conditional rules).

The import mechanism (upload → queued job → Excel) is documented in the [import subsystem](../../../system/imports.md).

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
