---
title: Property Module — Models
module: Property
last_updated: 2026-06-14
---

# Property Module — Models

This directory contains documentation for all Eloquent models in the `modules/Property` module.

| Model | Table | Description |
|-------|-------|-------------|
| [Property](./property.md) | `properties` | A single interment space or lot within a cemetery |
| [PropertyCommitment](./property-commitment.md) | `property_commitments` | A reservation or sale commitment linking customers to a property |
| [PropertyGroup](./property-group.md) | `property_groups` | A named section or block containing properties (supports nesting) |
| [PropertyType](./property-type.md) | `property_types` | Classification/type of an interment space |

## Module Overview

The Property module manages cemetery inventory — the physical interment spaces (lots, niches, crypts, etc.) available for sale or reservation. The four models form a clear ownership hierarchy:

- **PropertyType** — lookup/reference; classifies what kind of space a property is
- **PropertyGroup** — container; organizes properties into named sections, which can nest
- **Property** — the individual interment space; belongs to a group and type
- **PropertyCommitment** — the transactional record; marks a property as reserved or sold, with time-bounded activity

All models use the tenant database connection.
