---
model: Plan
module: System
table: plans
connection: central
primary_source: app/Models/Plan.php
source_paths:
  - app/Models/Feature.php
traits: []
related_models: [Feature]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Plan

## Overview

The Plan model represents a subscription tier that determines what features and capabilities are available to a tenant. Each plan has a human-readable `name`, a `description`, and a URL-safe `slug` that is unique across the central database. An `is_active` flag controls whether the plan is currently offered.

Plans are the top-level grouping for [Feature](./feature.md) records. Each tenant (via the `tenants.plan_id` foreign key) is associated with exactly one plan, and the plan's features define the tenant's functional boundaries within the Everspot platform. Adding or modifying a plan's feature set immediately affects all tenants on that plan.

The model itself is intentionally thin — no casts, no traits, no scopes — because plan management is primarily administrative. Business rules about feature access are enforced by the code that reads features, not by the Plan model.

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Human-readable plan name (e.g. `"Starter"`, `"Professional"`) |
| description | text | Yes | - | Optional longer description of the plan |
| slug | varchar | No | - | URL-safe unique identifier (e.g. `"starter"`, `"pro"`) |
| is_active | tinyint | No | 1 | Whether the plan is currently active/offered |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** _None on this table_ (Tenants reference plans via `tenants.plan_id → plans.id`)

**Indexes:** unique index on `slug`

## Casts

_None._

## Attributes

**Fillable:** `['name', 'description', 'slug']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ (`is_active` defaults to `1` at the database level)

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `features()` — has many [Feature](./feature.md) (`plan_id`): the capability flags and values belonging to this plan

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
// Find a plan by slug
$plan = Plan::where('slug', 'pro')->firstOrFail();

// Get all features for the plan
$features = $plan->features;

// Check if a plan has a specific feature key
$feature = $plan->features()->where('key', 'max_users')->first();
$maxUsers = $feature?->value; // null-safe; accessor applies type cast

// List all active plans
$activePlans = Plan::where('is_active', true)->get();

// Create a plan with features
$plan = Plan::create([
    'name'        => 'Enterprise',
    'description' => 'Full-featured plan for large cemeteries',
    'slug'        => 'enterprise',
]);
$plan->features()->createMany([
    ['key' => 'max_users',            'value' => '100', 'type' => 'integer'],
    ['key' => 'can_export_reports',   'value' => 'true', 'type' => 'boolean'],
]);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
