---
title: Mapping Module
module: Mapping
last_updated: 2026-06-14
---

# Mapping Module

The Mapping module provides interactive cemetery map functionality. It allows staff to create geo-referenced maps for each cemetery, plot spatial locations (groups, properties, curves) on those maps, and link locations to actual Everspot records (properties, plots, etc.) via a polymorphic relationship.

## Contents

- [Models](./models/index.md)
  - [Map](./models/map.md) — top-level map container per cemetery
  - [MapLocation](./models/map-location.md) — individual spatial element on a map

## Key Concepts

- **Maps** belong to a cemetery and hold the viewer configuration (center point, zoom levels, clustering).
- **MapLocations** are hierarchical (parent/child via `parent_id`) and typed (`LocationType` enum).
- `CURVE` type locations are excluded from the `total_location_count` counter — they are path elements, not addressable places.
- Locations carry a polymorphic `record()` relationship to whatever physical entity occupies that space.
- Observers maintain denormalized `center_lat`/`center_lng` columns and the location count counter automatically.
