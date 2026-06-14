---
model: EntityTypePivot
module: Common
table: entity_types
connection: tenant
primary_source: modules/Common/Models/EntityTypePivot.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/Entity.php
traits: []
related_models: [Entity]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin]
---

# EntityTypePivot

## Overview

The EntityTypePivot model represents a single type assignment for an [Entity](./entity.md). It uses the table `entity_types` (not `entity_type_pivots`) and carries a `type` column cast to the `EntityType` enum, which can be `MANUFACTURER`, `INSTALLER`, or `DEALER`. An entity can have multiple rows in this table, one per type.

Although this model looks like a bare pivot, it is documented because it carries a cast (`type` → `EntityType` enum), an explicit relationship back to `Entity`, and timestamps — fulfilling the documentation threshold in conventions.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| entity_id | bigint | No | - | FK → entities: the owning entity |
| type | varchar | No | - | Entity type value (cast to `EntityType` enum) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `entity_id` → `entities.id`

**Indexes:** FK-backing index on `entity_id`.

## Casts

- `type` → `EntityType::class` (enum)

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `entity()` — belongs to [Entity](./entity.md) (`entity_id`): the entity this type assignment belongs to

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._

## Common Usage

```php
// Assign a type to an entity
EntityTypePivot::create([
    'entity_id' => $entity->id,
    'type'      => EntityType::MANUFACTURER,
]);

// Check via entity relationship
$types = $entity->entityTypes->pluck('type');
// $types is a Collection of EntityType enum instances
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
