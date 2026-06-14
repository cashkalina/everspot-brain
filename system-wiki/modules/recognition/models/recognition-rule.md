---
model: RecognitionRule
module: Recognition
table: recognition_rules
connection: tenant
primary_source: modules/Recognition/Models/RecognitionRule.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Product/Models/Product.php
traits:
  - SoftDeletes
related_models: [Product]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, admin]
---

# RecognitionRule

## Overview

The `RecognitionRule` model defines a reusable recognition schedule template. A rule specifies the trigger conditions that activate recognition, the period over which the obligation is spread (`period_type`, `period_count`, `period_interval`), and any supplemental key-value configuration (`config_data`). Rules are templates — they are not tied to a single transaction, but are attached to one or more products (and potentially other entities) that should apply the same recognition schedule.

The rule `type` maps to the TYPES constant across the Recognition module (`rev_rec_rule` → `revenue`, `exp_rec_rule` → `expense`, `comm_rec_rule` → `commission`, `tax_rec_rule` → `tax`). When a recognizable event occurs on an entity associated with a rule, the system uses the rule's trigger and period configuration to generate a `RecognitionArrangement` (with its rule snapshot) and subsequent `RecognitionElement` postings.

Rules support soft deletes so that historical arrangements retain a reference to the rule configuration even after the rule is retired from active use.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Human-readable name for the rule |
| trigger | json | No | - | Trigger condition configuration (array: event that activates arrangements using this rule) |
| period_type | varchar | No | - | Unit of the recognition period (e.g. `month`, `year`, `day`) |
| period_count | int | Yes | - | Number of periods over which recognition is spread |
| period_interval | int | Yes | - | Interval between recognition postings within the period |
| is_custom | tinyint | No | 0 | Whether this is a custom (user-defined) rule vs. a system rule |
| config_data | json | Yes | - | Arbitrary additional configuration as key-value pairs |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Indexes:** Primary key only.

**Note:** The `recognition_rulables` pivot table (`id`, `recognition_rulable_type`, `recognition_rulable_id`, `recognition_rule_id`, `type`, `created_at`, `updated_at`) stores the polymorphic many-to-many associations between rules and their attached entities (e.g. products). It carries a `type` column that records the recognition type for that specific rule-entity pairing. This pivot is not separately documented as its own model because it carries no business logic beyond relationship bookkeeping.

## Casts

- `trigger` → `array` — JSON-encoded trigger configuration

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
const TYPES = [
    'rev_rec_rule'  => 'revenue',
    'exp_rec_rule'  => 'expense',
    'comm_rec_rule' => 'commission',
    'tax_rec_rule'  => 'tax',
];
```

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — rules are soft-deleted (`deleted_at`), preserving references from historical arrangements

## Relationships

- `products()` — morphedByMany [Product](../../product/models/product.md) via `recognition_rulable` (`recognition_rulable_id` / `recognition_rule_id`), with pivot `type`: products that use this recognition rule

## Scopes

_None._

## Events

_None defined on the model._

## Observers

_None registered._

## Key Methods

_None beyond standard Eloquent._

## Common Usage

```php
// Create a revenue recognition rule
$rule = RecognitionRule::create([
    'name'            => '12-Month Straight-Line Revenue',
    'trigger'         => ['event' => 'sale'],
    'period_type'     => 'month',
    'period_count'    => 12,
    'period_interval' => 1,
    'is_custom'       => false,
]);

// Attach a product to the rule with a type
$rule->products()->attach($product->id, ['type' => 'rev_rec_rule']);

// Retrieve all products using this rule
$products = $rule->products()->withPivot('type')->get();

// Look up the recognition type from the rule type key
$recognitionType = RecognitionRule::TYPES['rev_rec_rule']; // 'revenue'

// Soft-delete a retired rule (historical arrangements retain the rule snapshot)
$rule->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
