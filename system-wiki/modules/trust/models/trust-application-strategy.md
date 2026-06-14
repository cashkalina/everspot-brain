---
model: TrustApplicationStrategy
module: Trust
table: trust_application_strategies
connection: tenant
primary_source: modules/Trust/Models/TrustApplicationStrategy.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Trust/Casts/SpreadConfigCast.php
  - modules/Trust/Casts/WeightingConfigCast.php
traits: []
related_models: [TrustTransactionType]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, admin]
---

# TrustApplicationStrategy

## Overview

`TrustApplicationStrategy` defines a named strategy for how trust funds are applied (spread and weighted) when processing deposits or withdrawals across multiple trust elements. Each strategy encodes two configuration objects: a `spread_config` (how the total amount is distributed across elements, e.g., proportionally, equally, by element order) and a `weighting_config` (weighting factors or rules applied during the spread calculation).

These strategies are referenced by `TrustTransactionType` records — one strategy for principal application and one for income application — making the application behavior configurable per transaction type without code changes. The custom cast classes `SpreadConfigCast` and `WeightingConfigCast` deserialize the JSON columns into typed configuration objects that expose validation rules and calculation inputs.

`TrustApplicationStrategy` has no relationships back to the models it affects; it is purely a configuration record that is looked up at processing time through `TrustTransactionType`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Strategy name (e.g., "Pro-Rata", "Equal Split") |
| description | text | Yes | - | Human-readable description of the strategy |
| spread_config | json | No | - | Spread configuration object (deserialized via SpreadConfigCast) |
| weighting_config | json | No | - | Weighting configuration object (deserialized via WeightingConfigCast) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** _None._

**Indexes:** primary key only.

## Casts

- `spread_config` → `SpreadConfigCast::class` — deserializes the JSON spread configuration into a typed object (see `modules/Trust/Casts/SpreadConfigCast.php`)
- `weighting_config` → `WeightingConfigCast::class` — deserializes the JSON weighting configuration into a typed object (see `modules/Trust/Casts/WeightingConfigCast.php`)

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

_None._ (Referenced by [TrustTransactionType](./trust-transaction-type.md) via `principal_application_strategy_id` and `income_application_strategy_id`.)

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None beyond standard Eloquent._

## Common Usage

```php
// Look up a strategy by name
$strategy = TrustApplicationStrategy::where('name', 'Pro-Rata')->first();

// Access the spread configuration
$spreadConfig = $strategy->spread_config; // returns a SpreadConfigCast object

// Retrieve strategies linked to a transaction type
$type = TrustTransactionType::with(['principalApplicationStrategy', 'incomeApplicationStrategy'])->find($id);
$principalStrategy = $type->principalApplicationStrategy;
$incomeStrategy    = $type->incomeApplicationStrategy;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
