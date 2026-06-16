---
model: PropertyCommitment
module: Property
table: property_commitments
connection: tenant
primary_source: modules/Property/Models/PropertyCommitment.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Property/Observers/PropertyCommitmentObserver.php
  - modules/Property/Providers/PropertyServiceProvider.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Property/Models/Property.php
  - modules/Property/Models/PropertyGroup.php
  - modules/Customer/Models/Customer.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/OwnerFile.php
  - modules/Common/Models/OwnerFileLine.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasFactory
  - SoftDeletes
related_models: [Cemetery, Customer, Note, OwnerFile, OwnerFileLine, Property, PropertyGroup]built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, contract, core]
---

# PropertyCommitment

## Overview

The `PropertyCommitment` model records a formal commitment of a cemetery property to a customer — either a **reservation** or a **sale**. A commitment is the mechanism that marks a property (or a property group slot, when `property_id` is null) as occupied for a date-bounded period. Multiple commitments can exist per property over time but only one should be active at a given moment.

Commitment activity is time-gated by `committed_at` (start) and `uncommitted_at` (end). A commitment is **active** when `committed_at` is in the past and `uncommitted_at` is either null or in the future; **pending** when `committed_at` is in the future; and **voided** when `uncommitted_at` is in the past. The model exposes `active()` and `notActive()` query scopes plus `isActive()`, `isPending()`, and `isVoided()` instance helpers.

Commitments support a polymorphic `parent` relationship (commonly a `LiabilityLine`) that can provide authoritative sale date, sale price, and deed issuance date, taking precedence over data stored on the linked `OwnerFileLine`. Customer associations are tracked on a pivot table with a `role` column (`reserved`, `assigned`). The observer dispatches domain events (`PropertyCommitmentCreated`, `PropertyCommitmentUpdated`, `PropertyCommitmentDeleting`) for downstream reactions.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| parent_type | varchar | Yes | - | Polymorphic parent type (e.g. `Modules\Liability\Models\LiabilityLine`) |
| parent_id | bigint | Yes | - | Polymorphic parent id |
| property_id | bigint | Yes | - | FK → properties: the specific property committed (null = group-level commitment) |
| property_group_id | bigint | Yes | - | FK → property_groups: the group this commitment belongs to |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery this commitment belongs to |
| type | varchar | No | - | Commitment type: `reservation` or `sale` |
| is_manual | tinyint | No | 0 | Whether this commitment was created manually (vs. system-generated) |
| batch_no | int | Yes | - | Batch number for grouped commitments |
| reason | varchar | Yes | - | Reason for the commitment (e.g. reservation reason) |
| committed_at | datetime | No | - | When the commitment becomes (or became) active |
| expires_at | date | Yes | - | Optional expiry date for reservations |
| uncommitted_at | datetime | Yes | - | When the commitment was voided/ended; null = still active |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `property_id` → `properties.id`; `property_group_id` → `property_groups.id`; `cemetery_id` → `cemeteries.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `property_commitments_cemetery_id_index` on `cemetery_id`; `property_commitments_committed_at_index` on `committed_at`; `property_commitments_parent_type_parent_id_index` on `(parent_type, parent_id)`; `property_commitments_property_id_index` on `property_id`; `property_commitments_uncommitted_at_index` on `uncommitted_at`; FK-backing indexes on `property_group_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `committed_at` → `TimezonedDateTime::class` — timezone-aware datetime handling (see `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)
- `expires_at` → `date` — expiry date as a Carbon date
- `uncommitted_at` → `TimezonedDateTime::class` — timezone-aware datetime handling

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `is_manual` defaults to `0`

**Constants / static config:**
```php
const TYPES = [
    'reservation' => 'Reservation',
    'sale'        => 'Sale',
];
```

## Accessors & Mutators

- `getStatusAttribute(): string` — computes the commitment status string (`'active'`, `'pending'`, or `'voided'`) from `committed_at` and `uncommitted_at` using Carbon comparisons
- `getFullNameAttribute(): string` — delegates to `BaseModel::getModelFullTitle()` to produce a human-readable record title
- `getFormattedTypeAttribute(): string` — human-readable type label from the `TYPES` constant (`'Reservation'` or `'Sale'`)
- `getFormattedSubjectNameAttribute(): string` — returns the property's `description` when a specific property is committed, or `"Any Property in {group full_name}"` for group-level commitments
- `getReservedTermAttribute(): string` — `'Owner'` for sales, `'Reserved For'` for reservations; used in UI labels
- `getStatusBadgeAttribute(): string` — HTML badge for the commitment status (pending/voided/active with matching colors)

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes on the commitment record
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (`PropertyCommitmentFactory`)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — commitments are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `property()` — belongs to [Property](./property.md) (`property_id`): the specific interment space committed (may be null for group-level commitments)
- `allCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) via `customer_property_commitment` with pivot `role`: all customers on this commitment regardless of role
- `reservedCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) via pivot `role = reserved`: customers in the reserved role
- `assignedCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) via pivot `role = assigned`: customers in the assigned role
- `propertyGroup()` — belongs to [PropertyGroup](./property-group.md) (`property_group_id`): the property group this commitment belongs to
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery this commitment belongs to
- `parent()` — morph to: the polymorphic parent entity (commonly a `LiabilityLine`)
- `notes()` — morph many [Note](../../common/models/note.md) (`notable`): notes attached to this commitment
- `ownerFileLine()` — morph one [OwnerFileLine](../../common/models/owner-file-line.md) (`ownable`): the owner-file line linked to this commitment

## Scopes

- `active(Builder $query)` — commitments where `committed_at <= now` AND (`uncommitted_at > now` OR `uncommitted_at IS NULL`)
- `notActive(Builder $query)` — commitments where `committed_at > now` OR `uncommitted_at <= now`
- `exceptParent(Builder $query, $parent)` — excludes commitments tied to a specific polymorphic parent (used to allow re-selling under a new parent while excluding the current one)

## Events

_None defined on the model._ Lifecycle events are dispatched by `PropertyCommitmentObserver` (see Observers).

## Observers

- `PropertyCommitmentObserver` — registered in `PropertyServiceProvider::registerObservers()` (`PropertyCommitment::observe(PropertyCommitmentObserver::class)`). Handles:
  - `created` — dispatches `PropertyCommitmentCreated` event
  - `updated` — dispatches `PropertyCommitmentUpdated` event
  - `deleting` — dispatches `PropertyCommitmentDeleting` event

## Key Methods

- `isActive(): bool` — returns `true` when `status === 'active'`
- `isPending(): bool` — returns `true` when `status === 'pending'`
- `isVoided(): bool` — returns `true` when `status === 'voided'`
- `isTransferrable(): bool` — returns `true` when `type === 'sale'` and the commitment is active (sales can be transferred)
- `syncCustomers(array $customerIds, string $role): void` — delegates to `SyncPropertyCommitmentCustomers` action to sync a role's customer list on the pivot
- `hasParentLiabilityLine(): bool` — returns `true` when `parent_type` is `LiabilityLine` and the parent exists
- `getSaleDate(): ?\Carbon\Carbon` — sale date with priority: parent `LiabilityLine.sale_date` → `ownerFileLine.config_data.sale_date`
- `getSalePrice(): ?float` — sale price with priority: parent `LiabilityLine.sale_price` → `ownerFileLine.config_data.sale_price`
- `getDeedDate(): ?\Carbon\Carbon` — deed date with priority: parent `LiabilityLine.certificate_issuance_date` → `ownerFileLine.config_data.deed_date`
- `getDeedNumber(): ?string` — deed number from `ownerFileLine.config_data.deed_number` (no LiabilityLine source)
- `isFieldFromLiabilityLine(string $fieldName): bool` — checks whether a specific sale/deed field is sourced from the parent `LiabilityLine` (and therefore read-only in the UI)
- `hasSaleDeedData(): bool` — returns `true` if any sale or deed data exists (sale date, price, deed date, or deed number)
- `addToSearchData(): array` — returns the searchable payload (`['property_description' => ...]`) used when a calling context indexes this model; the method exists without `HasSearch` applied to this model directly
- `ownerFile(): ?OwnerFile` — helper (not a relationship method) resolving the `OwnerFile` through the linked `ownerFileLine`

## Common Usage

```php
// Active commitments for a property
$active = $property->propertyCommitments()->active()->get();

// Check commitment status
if ($commitment->isActive()) {
    echo $commitment->status_badge;
}

// Commitment type label
echo $commitment->formatted_type;  // "Sale" or "Reservation"

// Subject name for UI display
echo $commitment->formatted_subject_name;  // "Section A, Row 1, Space 3" or "Any Property in Section A"

// Customers on a commitment
$owners = $commitment->assignedCustomers;
$reserved = $commitment->reservedCustomers;

// Sync customers
$commitment->syncCustomers([$customer->id], 'assigned');

// Transferability check
if ($commitment->isTransferrable()) {
    // allow transfer flow
}

// Sale/deed data (respects LiabilityLine priority)
$saleDate  = $commitment->getSaleDate();
$salePrice = $commitment->getSalePrice();
$deedDate  = $commitment->getDeedDate();
$deedNo    = $commitment->getDeedNumber();

// Is this field locked because it comes from a LiabilityLine?
if ($commitment->isFieldFromLiabilityLine('sale_price')) {
    // render as read-only
}
```

## Imports

This model can be created/updated via spreadsheet import. See **[property-commitment](../imports/property-commitment.md)** for the column reference (valid headers, required fields, types, and conditional rules).

The import mechanism (upload → queued job → Excel) is documented in the [import subsystem](../../../system/imports.md).

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
