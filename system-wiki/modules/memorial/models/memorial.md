---
model: Memorial
module: Memorial
table: memorials
connection: tenant
primary_source: modules/Memorial/Models/Memorial.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Memorial/Observers/MemorialObserver.php
  - modules/Memorial/Providers/MemorialServiceProvider.php
  - modules/Common/Casts/PartialDateCast.php
  - modules/Common/Models/Entity.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Customer/Models/Customer.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Memorial/Models/MemorialPerson.php
  - modules/Property/Models/Property.php
  - modules/WorkOrder/Models/WorkOrder.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasExternalApprovals
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasPartialDateScopes
  - HasSearch
  - SoftDeletes
related_models: [Customer, Entity, LiabilityLine, ListOption, MemorialPerson, Note, Property, WorkOrder]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, service]
---

# Memorial

## Overview

The Memorial model represents a physical memorial marker — a headstone, plaque, monument, or similar object — associated with one or more cemetery plots and people. It tracks the full lifecycle of a memorial from ordering through installation, capturing manufacturer, dealer, installer, physical dimensions, material specifications, and partial dates for when it was ordered, shipped, and installed.

Each memorial has one or more [MemorialPerson](./memorial-person.md) records that link the memorial to the deceased individuals it commemorates and optionally to [Customer](../../customer/models/customer.md) records and interment records. The `display_name` is automatically derived from person names (via `generateDisplayName()`) unless `manual_name` is set to override it.

Memorials can be flagged as templates (`is_template = true`) for re-use as starting configurations. Status transitions are configured via `memorials-module-config` settings rather than hard-coded, making the status vocabulary flexible per-tenant. The model also supports EAV custom attributes, file attachments, model numbering, search indexing, soft deletes, external approval workflows, and partial date scopes — all via traits (see [Traits](#traits)).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_no | varchar | Yes | - | User-facing memorial number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| display_name | varchar | Yes | - | Display name; auto-derived from person names unless `manual_name = true` |
| manual_name | tinyint | No | 0 | When true, `display_name` is user-controlled and not auto-updated |
| manufacturer_id | bigint | Yes | - | FK → entities: the manufacturer |
| installer_id | bigint | Yes | - | FK → entities: the installer |
| dealer_id | bigint | Yes | - | FK → entities: the dealer |
| type_id | bigint | Yes | - | FK → list_options: memorial type (e.g. flat marker, upright) |
| material_id | bigint | Yes | - | FK → list_options: material (e.g. granite, bronze) |
| color_id | bigint | Yes | - | FK → list_options: color |
| width_location_id | bigint | Yes | - | FK → list_options: width measurement location |
| length_location_id | bigint | Yes | - | FK → list_options: length measurement location |
| width | decimal | Yes | - | Width dimension |
| height | decimal | Yes | - | Height dimension |
| depth | decimal | Yes | - | Depth dimension |
| size_uom | varchar | Yes | - | Unit of measure for dimensions (cast to `SizeUom` enum) |
| manufacturer_sku | varchar | Yes | - | Manufacturer's SKU (trimmed on save by observer) |
| dealer_sku | varchar | Yes | - | Dealer's SKU (trimmed on save by observer) |
| status | varchar | Yes | - | Memorial status (tenant-configured; default set by observer) |
| ordered_date_year | smallint | Yes | - | Ordered date year component (partial date via [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes)) |
| ordered_date_month | tinyint | Yes | - | Ordered date month component (partial date) |
| ordered_date_day | tinyint | Yes | - | Ordered date day component (partial date) |
| ordered_date_estimated | tinyint | No | 0 | Whether the ordered date is estimated |
| shipped_date_year | smallint | Yes | - | Shipped date year component (partial date) |
| shipped_date_month | tinyint | Yes | - | Shipped date month component (partial date) |
| shipped_date_day | tinyint | Yes | - | Shipped date day component (partial date) |
| shipped_date_estimated | tinyint | No | 0 | Whether the shipped date is estimated |
| installed_date_year | smallint | Yes | - | Installed date year component (partial date) |
| installed_date_month | tinyint | Yes | - | Installed date month component (partial date) |
| installed_date_day | tinyint | Yes | - | Installed date day component (partial date) |
| installed_date_estimated | tinyint | No | 0 | Whether the installed date is estimated |
| comments | text | Yes | - | Free-text comments |
| is_template | tinyint | No | 0 | Whether this memorial is a reusable template |
| template_name | varchar | Yes | - | Display name for the template (when `is_template = true`) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `manufacturer_id`, `installer_id`, `dealer_id` → `entities.id`; `type_id`, `material_id`, `color_id`, `width_location_id`, `length_location_id` → `list_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `model_no`, `status`, `is_template`, `manufacturer_id`, `installer_id`, `dealer_id`; single-column and composite year/month indexes on `ordered_date_year`, `shipped_date_year`, `installed_date_year`; FK-backing indexes on `color_id`, `material_id`, `type_id`, `width_location_id`, `length_location_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `is_template` → `boolean`
- `manual_name` → `boolean`
- `width` → `decimal:2`
- `height` → `decimal:2`
- `depth` → `decimal:2`
- `size_uom` → `SizeUom::class` (enum cast)
- `ordered_date` → `PartialDateCast::class.':ordered_date'` — composes `ordered_date_year` / `ordered_date_month` / `ordered_date_day` into a partial-date value (see `modules/Common/Casts/PartialDateCast.php`)
- `shipped_date` → `PartialDateCast::class.':shipped_date'` — composes `shipped_date_year` / `shipped_date_month` / `shipped_date_day`
- `installed_date` → `PartialDateCast::class.':installed_date'` — composes `installed_date_year` / `installed_date_month` / `installed_date_day`

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ — `status` is defaulted by the observer from `memorials-module-config` settings.

**Searchable columns:**
```php
protected $searchableColumns = ['model_no', 'display_name'];
```

## Accessors & Mutators

- `getStatusLabelAttribute(): ?string` — human-readable label for the current status from `memorials-module-config`; falls back to the raw status value if config is unavailable
- `getStatusColorAttribute(): ?string` — UI color for the current status from `memorials-module-config`; defaults to `'secondary'`

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for storing dynamic per-memorial fields
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasExternalApprovals](../../../system/traits/index.md#hasexternalapprovals) — external approval workflow for memorial-related approvals
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `MemorialFactory`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments for memorial photos and documents
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` for the memorial
- [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) — query scopes over the partial date component columns (`ordered_date_*`, `shipped_date_*`, `installed_date_*`)
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; searchable columns are `model_no` and `display_name`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — memorials are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

**People:**
- `people()` — has many [MemorialPerson](./memorial-person.md): the people commemorated on this memorial
- `customers()` — has-many-through [Customer](../../customer/models/customer.md) (through MemorialPerson via `customer_id`): customers linked to this memorial via their memorial-person records

**Vendors:**
- `manufacturer()` — belongs to [Entity](../../common/models/entity.md) (`manufacturer_id`): the manufacturing company
- `installer()` — belongs to [Entity](../../common/models/entity.md) (`installer_id`): the installing company
- `dealer()` — belongs to [Entity](../../common/models/entity.md) (`dealer_id`): the dealer/vendor

**Reference data:**
- `type()` — belongs to [ListOption](../../common/models/list-option.md) (`type_id`): memorial type
- `material()` — belongs to [ListOption](../../common/models/list-option.md) (`material_id`): material
- `color()` — belongs to [ListOption](../../common/models/list-option.md) (`color_id`): color
- `widthLocation()` — belongs to [ListOption](../../common/models/list-option.md) (`width_location_id`): width measurement location
- `lengthLocation()` — belongs to [ListOption](../../common/models/list-option.md) (`length_location_id`): length measurement location

**Cemetery operations:**
- `properties()` — belongs-to-many [Property](../../property/models/property.md) via `memorial_properties`: cemetery properties where this memorial is installed
- `liabilityLines()` — belongs-to-many [LiabilityLine](../../liability/models/liability-line.md) via `memorial_liability_lines`: fulfillment liability lines associated with this memorial
- `workOrders()` — belongs-to-many [WorkOrder](../../work-order/models/work-order.md) via `memorial_work_orders`: work orders for this memorial (installation, cleaning, etc.)

**Administrative:**
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): notes attached to this memorial

## Scopes

- `templates($query): Builder` — filters to records where `is_template = true`
- `notTemplates($query): Builder` — filters to records where `is_template = false`
- `byStatus($query, string $status)` — filters to records with the specified status value

Partial-date query scopes over the ordered/shipped/installed date component columns are contributed by [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) (see trait doc).

## Events

_None defined on the model._ Lifecycle behavior is handled by `MemorialObserver` (see Observers).

## Observers

- `MemorialObserver` — registered in `MemorialServiceProvider::registerObservers()` (`Memorial::observe(MemorialObserver::class)`). Handles:
  - `saving` — trims whitespace on `manufacturer_sku`, `dealer_sku`, `size_uom`; sets default status from `memorials-module-config` when `status` is empty
  - `created` — fires `analytics()->track('Memorial Created')`
  - `deleting` — wraps deletion in a DB transaction; runs `PreDeleteMemorial` checks

## Key Methods

- `getModelStatuses(): array` *(static)* — returns the configured status list from `memorials-module-config` settings (array of status configs with labels and colors)
- `generateDisplayName($people): string` *(static)* — accepts a Collection of `MemorialPerson` objects and returns a formatted display name joining their full names with ` & `; returns `'**Add Person to Update**'` if the collection is empty
- `getModelInferredName(): ?string` — returns `$this->display_name` (used by model numbering display)

## Common Usage

```php
// Create a memorial
$memorial = Memorial::create([
    'type_id'          => $typeOption->id,
    'material_id'      => $materialOption->id,
    'manufacturer_id'  => $entity->id,
    'width'            => 24.00,
    'height'           => 12.00,
    'depth'            => 4.00,
    'size_uom'         => 'in',
]);

// Add people to the memorial
$person = $memorial->people()->create([
    'first_name' => 'John',
    'last_name'  => 'Doe',
    'customer_id' => $customer->id,
]);

// Auto-update display name from people
if (! $memorial->manual_name) {
    $memorial->display_name = Memorial::generateDisplayName($memorial->people);
    $memorial->save();
}

// Template operations
$templates = Memorial::templates()->get();
$active    = Memorial::notTemplates()->byStatus('active')->get();

// Partial date example
$memorial->update([
    'ordered_date_year'  => 2024,
    'ordered_date_month' => 3,
    'ordered_date_day'   => 15,
]);

// Status display
echo $memorial->status_label;  // "Ordered" (from memorials-module-config)
echo $memorial->status_color;  // "warning"

// Soft delete (runs PreDeleteMemorial via observer)
$memorial->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
