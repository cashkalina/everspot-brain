---
model: DeliveryPreference
module: Common
table: delivery_preferences
connection: tenant
primary_source: modules/Common/Models/DeliveryPreference.php
source_paths:
  - app/Models/BaseModel.php
traits: []
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin]
---

# DeliveryPreference

## Overview

The DeliveryPreference model is a simple reference-data table listing the delivery preference options available when scheduling a delivery (e.g., "As Soon As Possible", "Specific Date"). Each row has a `name` and optional `config_data` JSON for preference-specific configuration.

The model has no traits, observers, or relationships — it is a lightweight lookup table consumed by other modules when presenting delivery scheduling options to users. The `requiresDate()` method provides a business-rule check used at the UI layer.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Delivery preference label |
| config_data | json | Yes | - | Preference-specific configuration |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

_None._

## Attributes

_None declared (no `$fillable` or `$guarded` in model — inherits BaseModel defaults)._

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

- `requiresDate(): bool` — returns `true` when `name === 'Specific Date'`, indicating the UI should present a date picker for this preference
- `getModelTitle(): ?string` — returns the preference's inferred display name
- `getModelFullTitle(): ?string` — delegates to `getModelTitle()`

## Common Usage

```php
// Get all delivery preferences for a select list
$preferences = DeliveryPreference::all();

// Check if a preference requires a date
$pref = DeliveryPreference::find($id);
if ($pref->requiresDate()) {
    // show date picker
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
