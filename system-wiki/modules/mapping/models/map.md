---
model: Map
module: Mapping
table: maps
connection: tenant
primary_source: modules/Mapping/Models/Map.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Mapping/Observers/MapObserver.php
  - modules/Mapping/Providers/MappingServiceProvider.php
  - modules/Mapping/Models/MapLocation.php
  - modules/Common/Models/Cemetery.php
traits:
  - InteractsWithMedia
related_models: [Cemetery, MapLocation]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [location, admin, inventory]
---

# Map

## Overview

The Map model represents an interactive cemetery map within Everspot. Each map belongs to a single cemetery and serves as the top-level container for all spatial data associated with that cemetery's layout. A map defines the base layer type (e.g., satellite imagery, custom overlay), stores JSON configuration for the map viewer (center point, zoom levels, clustering parameters), and tracks the total number of non-curve locations it contains via a denormalized `total_location_count` counter.

Maps support image file attachments via Spatie MediaLibrary through the `base-layer` media collection, allowing staff to upload custom background imagery that renders beneath the interactive location overlays. Each cemetery can designate one map as its default (`is_default = true`), which is the map shown by default in the user interface.

The model exposes a `getConfigData()` helper that wraps the raw `config_data` JSON in a typed `MapConfig` value object, providing structured access to viewer settings. The `base_layer_image_url` accessor returns the public URL of the first media item in the `base-layer` collection.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| cemetery_id | bigint | No | - | FK → cemeteries: the owning cemetery |
| base_type | varchar | No | - | Base layer type enum (via `BaseType` enum cast) |
| name | varchar | No | - | Human-readable map name |
| is_default | tinyint | No | 0 | Whether this is the default map for the cemetery |
| config_data | json | No | - | Viewer configuration (center point, zoom levels, clustering) |
| total_location_count | int | No | 0 | Denormalized count of non-CURVE map locations (maintained by MapLocationObserver) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `cemetery_id` → `cemeteries.id`

**Indexes:** FK-backing index on `cemetery_id`

## Casts

- `base_type` → `BaseType::class` — casts the base layer type string to the `Modules\Mapping\Enums\BaseType` enum
- `is_default` → `boolean`
- `config_data` → `array`

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getAvailableMediaCollectionsAttribute(): array` — returns the map's defined media collection names and labels (`['base-layer' => 'Base Layer Images']`); used by the generic file UI to render collection pickers
- `getBaseLayerImageUrlAttribute(): ?string` — returns the public URL of the first media item in the `base-layer` collection, or `null` if no image is attached

## Traits

- [InteractsWithMedia](../../../system/traits/index.md#interactswithmedia) — Spatie MediaLibrary core; this model registers a `base-layer` collection stored on `public-s3` for map background imagery

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery this map belongs to
- `locations()` — has many [MapLocation](./map-location.md): all spatial locations plotted on this map

## Scopes

_None._

## Events

_None._

## Observers

- `MapObserver` — registered in `MappingServiceProvider::registerObservers()` (`Map::observe(MapObserver::class)`). Handles:
  - `creating` — sets default `config_data` when none is provided (center point, zoom levels, grouping parameters)

## Key Methods

- `getConfigData(): MapConfig` — wraps `config_data` JSON in a `Modules\Mapping\ValueObjects\MapConfig` value object for typed access to viewer configuration
- `registerMediaCollections(): void` — registers the `base-layer` media collection (stored on `public-s3`); called automatically by Spatie MediaLibrary

## Common Usage

```php
// Create a map for a cemetery
$map = Map::create([
    'cemetery_id' => $cemetery->id,
    'name'        => 'Main Cemetery Map',
    'base_type'   => BaseType::Satellite,
    'is_default'  => true,
    'config_data' => [], // observer sets defaults
]);

// Access typed config
$config = $map->getConfigData();
$centerLat = $config->centerPoint[0];

// Get base layer image URL
$imageUrl = $map->base_layer_image_url;

// All locations on the map
$locations = $map->locations()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
