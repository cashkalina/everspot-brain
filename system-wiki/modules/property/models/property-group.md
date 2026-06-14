---
model: PropertyGroup
module: Property
table: property_groups
connection: tenant
primary_source: modules/Property/Models/PropertyGroup.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Property/Observers/PropertyGroupObserver.php
  - modules/Property/Providers/PropertyServiceProvider.php
  - modules/Property/Models/Property.php
  - modules/Property/Models/PropertyCommitment.php
  - modules/Common/Models/Cemetery.php
  - modules/Certificate/Models/CertificateLine.php
  - modules/Common/Models/Note.php
  - modules/Product/Models/Product.php
  - modules/Trust/Models/TrustingScheduleGroup.php
traits:
  - HasFactory
  - HasMoneyFields
  - SoftDeletes
related_models: [Cemetery, CertificateLine, Note, Product, Property, PropertyCommitment, PropertyGroup, TrustingScheduleGroup]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, location]
---

# PropertyGroup

## Overview

`PropertyGroup` represents a named section, block, or organizational subdivision of a cemetery — the container that holds individual [Property](./property.md) records (interment spaces). Groups can be nested: a group may have a `property_group_id` pointing to a parent group, enabling hierarchical section structures (e.g. Section → Block → Row).

Each group belongs to a [Cemetery](../../common/models/cemetery.md) and optionally to a [Product](../../product/models/product.md) (used for linking a section to a product catalog entry) and a [TrustingScheduleGroup](../../trust/models/trusting-schedule-group.md) (for trust accounting). Groups carry two money columns (`sale_price`, `cost_price`) stored as integer cents and exposed as dollars via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

The model exposes inventory-counting helpers — total spaces, assigned spaces, sold-but-unassigned group commitments, and net available spaces — that aggregate across its properties and commitments, supporting cemetery inventory dashboards.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| property_group_id | bigint | Yes | - | FK → property_groups: parent group (for nested sections) |
| product_id | bigint | Yes | - | FK → products: linked product catalog entry |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery this group belongs to |
| name | varchar | No | - | Display name for this group/section |
| trusting_schedule_group_id | bigint | Yes | - | FK → trusting_schedule_groups: trust schedule group |
| sale_price | int | Yes | - | Default sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — exposed as dollars) |
| cost_price | int | Yes | - | Default cost price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — exposed as dollars) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `property_group_id` → `property_groups.id`; `product_id` → `products.id`; `cemetery_id` → `cemeteries.id`; `trusting_schedule_group_id` → `trusting_schedule_groups.id`

**Indexes:** `property_groups_cemetery_id_index` on `cemetery_id`; `property_groups_name_index` on `name`; `property_groups_product_id_index` on `product_id`; FK-backing indexes on `property_group_id`, `trusting_schedule_group_id`.

## Casts

_None declared directly on the model._ Money columns (`sale_price`, `cost_price`) are handled by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc.

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
public array $moneyAttributes = ['sale_price', 'cost_price'];
```

## Accessors & Mutators

- `getFullNameAttribute(): string` — if this group has a parent, returns `"{parent->full_name} - {name}"`; otherwise just `name`. Resolves hierarchically to produce fully-qualified section paths.

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (`PropertyGroupFactory`)
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `sale_price` and `cost_price`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — property groups are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery this group belongs to
- `product()` — belongs to [Product](../../product/models/product.md) (`product_id`): the associated product catalog entry
- `trustingScheduleGroup()` — belongs to [TrustingScheduleGroup](../../trust/models/trusting-schedule-group.md) (`trusting_schedule_group_id`): trust schedule group
- `parentGroup()` — belongs to [PropertyGroup](./property-group.md) (`property_group_id`): the parent group (for nested structures)
- `childGroups()` — has many [PropertyGroup](./property-group.md) (`property_group_id`): direct child groups
- `properties()` — has many [Property](./property.md): interment spaces in this group
- `propertyCommitments()` — has many [PropertyCommitment](./property-commitment.md): all commitments under this group (including group-level and property-level)
- `certificateLines()` — has many [CertificateLine](../../certificate/models/certificate-line.md): certificate lines referencing this group
- `notes()` — morph many [Note](../../common/models/note.md) (`notable`): notes attached to this group

## Scopes

- `forCemetery(Builder $query, $cemeteryId)` — filters to groups belonging to a specific cemetery

## Events

_None defined on the model._ Lifecycle behavior is handled by `PropertyGroupObserver` (see Observers).

## Observers

- `PropertyGroupObserver` — registered in `PropertyServiceProvider::registerObservers()` (`PropertyGroup::observe(PropertyGroupObserver::class)`). Handles:
  - `created` — fires `analytics()->track('Property Group Created')`
  - `deleting` — wraps deletion in a DB transaction and runs `PreDeletePropertyGroup` checks

## Key Methods

- `getAllChildGroups(): Collection` — recursively collects all descendant groups (children, grandchildren, etc.) into a flat collection
- `getTotalSpacesCount(): int` — total number of properties (spaces) in this group
- `getAssignedSpacesCount(): int` — number of properties in this group that currently have at least one active commitment
- `getSoldUnassignedCount(): int` — number of active commitments in this group where `property_id` is null (sold to the group but not yet assigned to a specific space)
- `getNetAvailableSpacesCount(): int` — `max(0, total - assigned - sold_unassigned)`; the net available inventory count
- `getInventoryMetrics(): array` — returns all four inventory counts as an associative array (`total_spaces`, `assigned_spaces`, `sold_unassigned`, `net_available`)

## Common Usage

```php
// All top-level groups for a cemetery
$topLevelGroups = PropertyGroup::forCemetery($cemetery->id)
    ->whereNull('property_group_id')
    ->get();

// Nested group full name (e.g. "Section A - Block 1 - Row 3")
echo $group->full_name;

// All descendant groups (recursive)
$allDescendants = $group->getAllChildGroups();

// Inventory overview
$metrics = $group->getInventoryMetrics();
// ['total_spaces' => 50, 'assigned_spaces' => 35, 'sold_unassigned' => 5, 'net_available' => 10]

// Available properties in this group
$available = $group->properties()->available()->get();

// Properties and their active commitments
$properties = $group->properties()->with('activeCommitment')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
