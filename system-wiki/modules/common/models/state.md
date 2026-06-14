---
model: State
module: Common
table: states
connection: tenant
primary_source: modules/Common/Models/State.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/Country.php
traits: []
related_models: [Country]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# State

## Overview

The State model is a reference-data table listing states, provinces, and territories, each associated with a [Country](./country.md). It is used by [Address](./address.md) and [Cemetery](./cemetery.md) for state/province selection. The table is typically pre-seeded and rarely modified at runtime.

Each row has a display `name` and a short `code` (e.g. `'CA'`, `'ON'`). The `scopeForCountry()` scope provides a convenient filter for populating state dropdowns scoped to a specific country, defaulting to country ID 1 (typically the United States) when the country ID is empty.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| country_id | bigint | Yes | - | FK → countries: the country this state belongs to |
| name | varchar | No | - | State/province display name |
| code | varchar | No | - | State/province abbreviation (e.g. `CA`, `NY`) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `country_id` → `countries.id`

**Indexes:** FK-backing index on `country_id`.

## Casts

_None._

## Attributes

**Fillable:** `['country_id', 'name', 'code']`

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `country()` — belongs to [Country](./country.md) (`country_id`): the country this state belongs to

## Scopes

- `forCountry($query, $countryId): Builder` — filters to states for the given country (defaults to country ID 1 when `$countryId` is empty)

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getModelTitle(): ?string` — returns the state's inferred display name
- `getModelFullTitle(): ?string` — delegates to `getModelTitle()`

## Common Usage

```php
// Get states for the United States
$states = State::forCountry(1)->get();

// Get states for a specific country
$canadianProvinces = State::forCountry($canada->id)->get();

// Use in address creation
$address->update(['state_id' => $california->id]);
echo $address->state->code;   // "CA"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
