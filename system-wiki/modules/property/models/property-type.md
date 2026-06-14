---
model: PropertyType
module: Property
table: property_types
connection: tenant
primary_source: modules/Property/Models/PropertyType.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Property/Observers/PropertyTypeObserver.php
  - modules/Property/Providers/PropertyServiceProvider.php
  - modules/Property/Models/Property.php
  - modules/Certificate/Models/CertificateLine.php
traits:
  - HasAttributes
  - HasFactory
  - SoftDeletes
related_models: [CertificateLine, Property]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, admin]
---

# PropertyType

## Overview

`PropertyType` is a reference/lookup model that classifies interment spaces by their physical or legal type — for example, "Full Burial", "Cremation", "Niche", "Mausoleum Crypt", etc. Every [Property](./property.md) record must belong to exactly one `PropertyType`. Certificate lines may also be linked to a property type to describe what kind of interment space a certificate covers.

The model is intentionally minimal: it holds only a `name` and the standard timestamp columns. Because it uses [HasAttributes](../../../system/traits/index.md#hasattributes), operators can attach EAV custom attributes to property types for any additional metadata the cemetery requires without schema changes. Soft deletes allow deactivating a type without losing historical references.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Display name for this property type |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Indexes:** `property_types_name_index` on `name`.

**Note:** No foreign key constraints; `property_types` is referenced by `properties.property_type_id` and `certificate_lines.property_type_id` but owns no FKs itself.

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for additional property-type metadata
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (`PropertyTypeFactory`)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — property types are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `properties()` — has many [Property](./property.md) (`property_type_id`): all interment spaces of this type
- `certificateLines()` — has many [CertificateLine](../../certificate/models/certificate-line.md) (`property_type_id`): certificate lines for this type

## Scopes

_None._

## Events

_None defined on the model._

## Observers

- `PropertyTypeObserver` — registered in `PropertyServiceProvider::registerObservers()` (`PropertyType::observe(PropertyTypeObserver::class)`). Handles:
  - `created` — fires `analytics()->track('Property Type Created')`
  - `deleting` — wraps deletion in a DB transaction and runs `PreDeletePropertyType` checks

## Key Methods

_None beyond standard Eloquent._

## Common Usage

```php
// All available property types
$types = PropertyType::all();

// Properties of a given type
$cremationProperties = PropertyType::where('name', 'Cremation')->first()
    ->properties()
    ->available()
    ->get();

// Certificate lines for a type
$lines = $propertyType->certificateLines;

// With EAV attributes
$attributeValues = $propertyType->attributeValues()->forAreaCode('property-type')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
