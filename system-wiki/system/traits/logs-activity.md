---
trait: LogsActivity
owning_module: framework
framework: Spatie\Activitylog\Traits\LogsActivity
source_paths:
  - vendor/spatie/laravel-activitylog/src/Traits/LogsActivity.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# LogsActivity

**Namespace:** `Spatie\Activitylog\Traits\LogsActivity`
**Package:** `spatie/laravel-activitylog`
**Registry entry:** [index.md#logsactivity](./index.md#logsactivity)

## Purpose

Automatically logs Eloquent model events (created, updated, deleted, and optionally restored) to an `activity_log` table via the Spatie Activity Log package. Each log entry records the event type, the changed attributes (configurable), the causer (typically the authenticated user), and the subject model.

In Everspot, `LogsActivity` is applied on `BaseModel`, so all concrete models that extend it inherit automatic activity logging.

## Contributed Columns

No columns are added to the using model's table. Activity log entries are stored in the shared `activity_log` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Description |
|--------|------|-------------|
| `activities()` | `MorphMany` | All activity log entries for this model instance (via the `subject` polymorphic relationship on `ActivityLog`). Provided by the package. |

## Contributed Scopes

None on the model itself (filtering helpers are on `ActivityLog`).

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getActivitylogOptions()` | `(): LogOptions` | Must be defined on the using model (or its base class) to configure what gets logged. Returns a `LogOptions` instance. Applied on `BaseModel` in Everspot. |
| `tapActivity()` | `(Activity $activity, string $eventName): void` | Optional override: called just before saving each activity log entry, allowing custom fields to be set on the `Activity` model. |

## Configuration (Everspot-specific)

`BaseModel` implements `getActivitylogOptions()`. The configuration used across Everspot models (unless overridden) is defined there. Models may override `getActivitylogOptions()` to change which attributes are logged, the log name, etc.

Typical configuration pattern:

```php
public function getActivitylogOptions(): LogOptions
{
    return LogOptions::defaults()
        ->logFillable()
        ->logOnlyDirty();
}
```

## Used By

Applied on `BaseModel` (all concrete models inherit it). Discoverable by `use LogsActivity` / `use Spatie\Activitylog\Traits\LogsActivity` in Everspot source.
