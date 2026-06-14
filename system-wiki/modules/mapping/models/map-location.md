---
model: MapLocation
module: Mapping
table: map_locations
connection: tenant
primary_source: modules/Mapping/Models/MapLocation.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Mapping/Observers/MapLocationObserver.php
  - modules/Mapping/Providers/MappingServiceProvider.php
  - modules/Mapping/Models/Map.php
traits: []
related_models: [Map, MapLocation]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [location, inventory]
---

# MapLocation

## Overview

The MapLocation model represents a single spatial element plotted on a cemetery map. Locations are hierarchical — any location may have a parent location (`parent_id` self-reference), enabling multi-level groupings such as sections containing rows containing individual plots. Every location belongs to exactly one [Map](./map.md).

Each location has a `type` (the `LocationType` enum, e.g., group, property, curve) that governs how it is rendered and counted. Critically, `CURVE` type locations are excluded from the `maps.total_location_count` counter — they are path-drawing elements rather than addressable places. The observer maintains this counter automatically on create, update (when type changes), and delete.

A location carries spatial data in `center_point` (a JSON `[lat, lng]` array) and `bounds` (a JSON polygon). The observer denormalizes `center_point` into the indexed `center_lat` / `center_lng` decimal columns on save to enable efficient proximity queries without JSON parsing. The `config_data` JSON column holds renderer-specific options wrapped by the `LocationConfig` value object.

A polymorphic `record()` relationship links the location to whatever Everspot entity physically occupies that space (e.g., a cemetery property or interment plot), identified by `record_type` and `record_id`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| map_id | bigint | No | - | FK → maps: the owning map |
| parent_id | bigint | Yes | - | FK → map_locations: parent location (for hierarchical groupings) |
| type | varchar | No | - | Location type enum (via `LocationType` cast — group, property, curve, etc.) |
| record_type | varchar | Yes | - | Polymorphic morph type for the linked record |
| record_id | bigint | Yes | - | Polymorphic morph id for the linked record |
| center_point | json | Yes | - | `[lat, lng]` array; source of truth for the center coordinates |
| center_lat | decimal | Yes | - | Denormalized latitude from `center_point` (maintained by observer) |
| center_lng | decimal | Yes | - | Denormalized longitude from `center_point` (maintained by observer) |
| bounds | json | Yes | - | Polygon boundary coordinates |
| config_data | json | Yes | - | Renderer configuration options |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `map_id` → `maps.id`; `parent_id` → `map_locations.id`

**Indexes:** composite index on (`center_lat`, `center_lng`) for proximity queries; single-column indexes on `map_id`, `parent_id`, `record_id`, `record_type`, `type`

## Casts

- `type` → `LocationType::class` — casts the type string to the `Modules\Mapping\Enums\LocationType` enum
- `config_data` → `array`
- `center_point` → `array`
- `bounds` → `array`

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getCenterPointLatAttribute(): ?float` — convenience accessor returning the latitude component (index 0) of `center_point` as a float, or `null` if not set
- `getCenterPointLngAttribute(): ?float` — convenience accessor returning the longitude component (index 1) of `center_point` as a float, or `null` if not set

## Traits

_None._

## Relationships

- `map()` — belongs to [Map](./map.md): the map this location belongs to
- `parent()` — belongs to [MapLocation](./map-location.md) (`parent_id`): the parent location in the hierarchy
- `children()` — has many [MapLocation](./map-location.md) (`parent_id`): child locations nested under this one
- `record()` — morphTo: the physical record occupying this location (may be a Property, Plot, or other entity referenced by `record_type`/`record_id`)

## Scopes

_None._

## Events

_None._

## Observers

- `MapLocationObserver` — registered in `MappingServiceProvider::registerObservers()` (`MapLocation::observe(MapLocationObserver::class)`). Handles:
  - `creating` — populates `center_lat` / `center_lng` from `center_point` if available
  - `created` — increments `maps.total_location_count` for non-CURVE locations
  - `updating` — re-derives `center_lat` / `center_lng` when `center_point` is dirty
  - `updated` — adjusts `maps.total_location_count` when `type` changes between CURVE and non-CURVE
  - `deleted` — decrements `maps.total_location_count` for non-CURVE locations

## Key Methods

- `getMeta(bool $fullDetails = true, bool $withOwnerData = true): array` — delegates to `GenerateLocationMeta` action to build the full metadata array for this location (used by the map API to populate tooltip/info panels)
- `getConfigData(): LocationConfig` — wraps `config_data` JSON in a `Modules\Mapping\ValueObjects\LocationConfig` value object for typed renderer configuration access

## Common Usage

```php
// Create a group location
$group = MapLocation::create([
    'map_id'       => $map->id,
    'type'         => LocationType::Group,
    'center_point' => [40.4407, -80.0025],
    'config_data'  => [],
]);

// Add a child property location linked to a record
$property = MapLocation::create([
    'map_id'      => $map->id,
    'parent_id'   => $group->id,
    'type'        => LocationType::Property,
    'center_point'=> [40.4408, -80.0026],
    'record_type' => 'Modules\\Property\\Models\\Property',
    'record_id'   => $property->id,
]);

// Hierarchy traversal
$children = $group->children()->get();
$parent   = $property->parent;

// Get the physical record
$record = $property->record;

// Location metadata for map rendering
$meta = $mapLocation->getMeta(fullDetails: true);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
