---
model: Country
module: Common
table: countries
connection: tenant
primary_source: modules/Common/Models/Country.php
source_paths:
  - app/Models/BaseModel.php
traits: []
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# Country

## Overview

The Country model is a reference-data table containing countries and their international codes. It is used system-wide wherever a country selection is required — most notably by [Address](./address.md) and [VeteranTag](../../customer/models/veteran-tag.md). The table is typically pre-seeded with standard ISO country data and is rarely modified at runtime.

Each row holds the country's display name, ISO 3-letter code (`iso3`), ISO 2-letter code (`iso2`), international phone dial code (`phonecode`), capital city, currency code, native name, and Unicode emoji representations. The model has no traits, observers, or custom scopes — it is a simple read-heavy reference table.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Country display name |
| iso3 | varchar | No | - | ISO 3-letter country code |
| iso2 | varchar | Yes | - | ISO 2-letter country code |
| phonecode | varchar | No | - | International dial code (e.g. `1`, `44`) |
| capital | varchar | Yes | - | Capital city name |
| currency | varchar | No | - | Currency code (e.g. `USD`) |
| native | varchar | Yes | - | Country name in its native language |
| emoji | varchar | No | - | Flag emoji character |
| emoji_u | varchar | No | - | Unicode code points for the flag emoji |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

_None._

## Attributes

**Fillable:** `['name', 'iso3', 'iso2', 'phonecode', 'capital', 'currency', 'native', 'emoji', 'emoji_u']`

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

_None._

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getModelTitle(): ?string` — returns the country's inferred display name
- `getModelFullTitle(): ?string` — returns the full display name (delegates to `getModelTitle()`)

## Common Usage

```php
// Find a country by ISO2
$usa = Country::where('iso2', 'US')->first();

// Use in address creation
$address->update(['country_id' => $usa->id]);

// Display the flag emoji
echo $usa->emoji;   // 🇺🇸
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
