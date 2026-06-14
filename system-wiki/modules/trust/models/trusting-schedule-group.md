---
model: TrustingScheduleGroup
module: Trust
table: trusting_schedule_groups
connection: tenant
primary_source: modules/Trust/Models/TrustingScheduleGroup.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Trust/Models/TrustingSchedule.php
traits: []
related_models: [TrustingSchedule]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, admin]
---

# TrustingScheduleGroup

## Overview

`TrustingScheduleGroup` is a simple organizational container for `TrustingSchedule` records. It groups related schedules under a shared name, enabling the UI and configuration screens to present trust schedules in logical sets (e.g., by product category or jurisdiction).

The model has minimal logic — it holds only a name and exposes the `trustingSchedules()` has-many relationship back to its member schedules. All behavioral complexity lives in `TrustingSchedule` and its child `TrustArrangement` records.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Group display name |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** _None._

**Indexes:** primary key only.

## Casts

_None._

## Attributes

**Fillable:** `['name']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `trustingSchedules()` — has many [TrustingSchedule](./trusting-schedule.md): the schedules organized under this group

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
// List all schedule groups with their schedules
$groups = TrustingScheduleGroup::with('trustingSchedules')->get();

foreach ($groups as $group) {
    echo $group->name;
    foreach ($group->trustingSchedules as $schedule) {
        echo "  - " . $schedule->name;
    }
}

// Create a new group
$group = TrustingScheduleGroup::create(['name' => 'Burial Services']);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
