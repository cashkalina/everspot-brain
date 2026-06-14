---
model: ModelNumberConfiguration
module: Common
table: model_number_configurations
connection: tenant
primary_source: modules/Common/Models/ModelNumberConfiguration.php
source_paths:
  - app/Models/BaseModel.php
traits: []
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# ModelNumberConfiguration

## Overview

The ModelNumberConfiguration model stores the numbering template for each model type that uses [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering). Each row defines how user-facing record numbers (`model_no`) are generated for a specific model class: the prefix, suffix, minimum digit count, increment interval, and the next number to issue.

The `type` column allows for multiple configurations per model class (e.g. different number sequences for different subtypes). When `HasModelNumbering::generateModelNumber()` runs, it looks up the appropriate `ModelNumberConfiguration` row for the calling model class and increments `next_number`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_type | varchar | No | - | Fully qualified model class name this config applies to |
| type | varchar | No | default | Configuration variant (e.g. `default`, or a subtype key) |
| prefix | varchar | No | (empty) | Prefix prepended to the number |
| suffix | varchar | No | (empty) | Suffix appended to the number |
| min_digits | int | No | 0 | Minimum digit count (zero-pads the number) |
| interval | int | No | 1 | Increment step between issued numbers |
| next_number | int | No | 1 | The next number to be issued |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

_None._

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

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

- `getModelTitleSuffix(): ?string` — returns the display suffix for this configuration, derived by calling `::getModelNameTitle()` on the resolved `model_type` class

## Common Usage

```php
// Look up the numbering config for Customer
$config = ModelNumberConfiguration::where('model_type', Customer::class)
    ->where('type', 'default')
    ->first();

// Inspect the next number
echo $config->next_number;   // e.g. 1042

// Update prefix/suffix via admin UI
$config->update(['prefix' => 'CUST-', 'min_digits' => 5]);
// next generated number: "CUST-01042"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
