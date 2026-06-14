---
model: Repetition
module: Repetition
table: repetitions
connection: tenant
primary_source: modules/Repetition/Models/Repetition.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Repetition/Providers/RepetitionServiceProvider.php
traits:
  - HasFactory
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Repetition

## Overview

The Repetition model is the scheduling primitive for the Everspot recurrence system. It stores a single recurrence rule attached to any entity that implements the `Repeatable` contract via the polymorphic `repeatable` morphTo relationship. Examples include `Subscription` and any future module that adopts the pattern.

Repetitions support two scheduling strategies, controlled by the `type` column (a `RepetitionType` enum):

- **Simple** — an interval-based rule (e.g., every N seconds). Occurrences are computed by checking whether `(timestamp - start_at) % interval` falls within a day window.
- **Complex** — a calendar-pattern rule using `year`, `month`, `day`, `week`, `week_of_month`, and `weekday` columns. A wildcard value `'*'` means "any". The `tz_offset` column shifts the UTC timestamp before matching, so patterns evaluate in the entity's local timezone.

The model exposes a `toPeriod()` method that returns a lazily-evaluated `CarbonPeriod` stream of occurrence dates between `start_at` and `end_at`. Query scopes (`scopeWhereOccursOn`, `scopeWhereOccursBetween`, `scopeWhereActiveForTheDate`, etc.) let callers fetch repetitions active on a given date or range directly from the database, using driver-specific raw SQL for MySQL, SQLite, and PostgreSQL.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| repeatable_type | varchar | No | - | Polymorphic owner type |
| repeatable_id | bigint | No | - | Polymorphic owner id |
| type | enum | No | simple | Recurrence strategy: `simple` (interval) or `complex` (calendar pattern) |
| group | varchar | No | - | Grouping key to cluster related repetitions |
| start_at | timestamp | No | - | Recurrence start date |
| tz_offset | int | No | 0 | Timezone offset in seconds applied before calendar pattern evaluation |
| interval | int | Yes | - | Interval in seconds (Simple type only) |
| year | varchar | Yes | - | Year pattern (`'*'` = any, or a 4-digit year string) |
| month | varchar | Yes | - | Month pattern (`'*'` = any, or month number) |
| day | varchar | Yes | - | Day-of-month pattern (`'*'` = any, or day number) |
| week | varchar | Yes | - | ISO week-of-year pattern (`'*'` = any, or week number) |
| week_of_month | varchar | Yes | - | Week-of-month pattern (`'*'` = any, or 1–5) |
| weekday | varchar | Yes | - | Day-of-week pattern (`'*'` = any, or 0=Sunday…6=Saturday) |
| end_at | timestamp | Yes | - | Recurrence end date (null = indefinite, defaults to today + 25 years in `toPeriod()`) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** _None._

**Indexes:** `end_at`, `group`, `start_at` (single-column); composite index on (`repeatable_type`, `repeatable_id`).

## Casts

- `type` → `RepetitionType::class` — PHP-backed enum (`modules/Repetition/Enums/RepetitionType.php`); values: `simple`, `complex`
- `start_at` → `date`
- `end_at` → `date`
- `tz_offset` → `integer`

## Attributes

**Fillable:** `['type', 'start_at', 'tz_offset', 'interval', 'end_at', 'year', 'month', 'day', 'week', 'week_of_month', 'weekday', 'group']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None explicitly set._ `type` defaults to `simple` at the database level; `tz_offset` defaults to `0`.

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — wires the custom `RepetitionFactory` via `newFactory()` for model factories

## Relationships

- `repeatable()` — morphTo: the parent entity this repetition belongs to (may be Subscription, or any model implementing the `Repeatable` contract)

## Scopes

- `scopeWithGroup(Builder $query, string $group): Builder` — filters to repetitions with the given `group` value
- `scopeWhereActiveForTheDate(Builder $query, Carbon $date): Builder` — filters to records where `start_at <= $date` and (`end_at` is null or `end_at >= $date`)
- `scopeWhereOccursOn(Builder $query, Carbon $date): Builder` — filters to repetitions whose schedule produces an occurrence on `$date`; combines `whereActiveForTheDate` with driver-specific SQL for both simple-interval and complex-calendar matching
- `scopeWhereOccursBetween(Builder $query, Carbon $start, Carbon $end): Builder` — filters to repetitions that occur on any date within a date range (enumerates each date and ORs `scopeWhereOccursOn`)
- `scopeWhereHasSimpleRecurringOn(Builder $query, Carbon $date): Builder` — driver-specific SQL check for Simple-type recurrences on a given date (MySQL / SQLite / PostgreSQL)
- `scopeWhereHasComplexRecurringOn(Builder $query, Carbon $date): Builder` — driver-specific SQL check for Complex-type recurrences on a given date (MySQL / SQLite / PostgreSQL)

## Events

_None._

## Observers

_None registered._

## Key Methods

- `toPeriod($endDate = null): CarbonPeriod` — returns a lazily-evaluated `CarbonPeriod` stream of occurrence dates. For Simple type, applies a seconds-interval step; for Complex type, applies a filter function that checks all calendar components. Falls back to `today()->addYears(25)` when `end_at` is null.
- `nextOccurrence(Carbon $after): ?Carbon` — returns the next occurrence date strictly after `$after`, or `null` when the schedule has ended or no further occurrence exists.
- `calculateNumberOfOccurrences(): int` — counts total occurrences between `start_at` and `end_at`; returns `-1` when the schedule is indefinite (`end_at` is null).
- `newCollection(array $models = []): RepeatCollection` — overrides Eloquent's default collection class to return a `RepeatCollection` instance, enabling collection-level recurrence helpers.

## Common Usage

```php
// Simple repetition: every 7 days
$repetition = Repetition::create([
    'repeatable_type' => Subscription::class,
    'repeatable_id'   => $subscription->id,
    'type'            => RepetitionType::Simple,
    'group'           => 'weekly-payment',
    'start_at'        => today(),
    'interval'        => 7 * 86400, // 7 days in seconds
    'end_at'          => today()->addYear(),
]);

// Complex repetition: first Monday of every month
$repetition = Repetition::create([
    'repeatable_type' => Subscription::class,
    'repeatable_id'   => $subscription->id,
    'type'            => RepetitionType::Complex,
    'group'           => 'monthly-billing',
    'start_at'        => today(),
    'month'           => '*',
    'week_of_month'   => '1',
    'weekday'         => '1', // Monday
    'year'            => '*',
    'day'             => '*',
    'week'            => '*',
    'tz_offset'       => 0,
]);

// Get all occurrence dates as a Carbon period
$period = $repetition->toPeriod();
foreach ($period as $date) {
    echo $date->toDateString();
}

// Next occurrence after today
$next = $repetition->nextOccurrence(today());

// Query: which repetitions occur on a specific date?
$active = Repetition::whereOccursOn(today())->withGroup('weekly-payment')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
