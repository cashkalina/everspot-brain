---
model: Feature
module: System
table: features
connection: central
primary_source: app/Models/Feature.php
source_paths:
  - app/Models/Plan.php
traits: []
related_models: [Plan]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Feature

## Overview

The Feature model represents a single capability flag or configuration value belonging to a subscription plan. Each feature is a key-value pair scoped to a [Plan](./plan.md), where the `key` identifies the capability (e.g., `"max_users"`, `"can_export_reports"`) and the `value` stores its setting. The `type` column controls how the raw varchar `value` should be interpreted at runtime — as a boolean, integer, float, JSON object/array, or plain string.

Features are the mechanism by which Everspot differentiates what tenants on different plans can access or do. When code needs to check whether a tenant has a given capability, it queries this model via its plan. The polymorphic typing on `value` means a single storage scheme supports all scalar and structured flag types without requiring separate columns per data type.

Because Feature belongs to Plan and Plan is associated with Tenant, the feature set effectively defines the tenant's allowed functionality boundary within the Everspot central database.

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| plan_id | bigint | No | - | FK → plans.id; the plan this feature belongs to |
| key | varchar | No | - | Feature identifier string (e.g. `max_users`, `can_export`) |
| value | varchar | Yes | - | Raw stored value; cast at runtime via `getValueAttribute()` based on `type` |
| type | varchar | No | string | Value type discriminator: `boolean`, `integer`, `float`, `json`, or `string` (default) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `plan_id` → `plans.id` (no cascade)

**Indexes:** FK-backing index on `plan_id`

## Casts

- `value` → `string` — base cast declared in `$casts`; the accessor `getValueAttribute()` overrides the returned value at runtime by interpreting the raw string according to `type`

## Attributes

**Fillable:** `['plan_id', 'key', 'value', 'type']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ (the `type` column default `string` is set at the database level)

## Accessors & Mutators

- `getValueAttribute($value): mixed` — **accessor**: interprets the raw varchar `value` according to the `type` column using a `match` expression:
  - `'boolean'` → `filter_var($value, FILTER_VALIDATE_BOOLEAN)`
  - `'integer'` → `(int) $value`
  - `'float'` → `(float) $value`
  - `'json'` → `json_decode($value, true)`
  - `default` (including `'string'`) → `$value` unchanged
  - Returns `null` explicitly when the raw value is `null`

## Traits

_None._

## Relationships

- `plan()` — belongs to [Plan](./plan.md) (`plan_id`): the subscription plan this feature is part of

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
// Get all features for a plan
$features = Plan::where('slug', 'pro')->first()->features;

// Read a typed feature value
$feature = Feature::where('plan_id', $plan->id)->where('key', 'max_users')->first();
$maxUsers = $feature->value; // returns (int) 50 when type='integer'

// Check a boolean feature
$canExport = Feature::where('plan_id', $plan->id)
    ->where('key', 'can_export_reports')
    ->value('value'); // accessor applies: true or false

// Create a new feature
Feature::create([
    'plan_id' => $plan->id,
    'key'     => 'max_users',
    'value'   => '50',
    'type'    => 'integer',
]);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
