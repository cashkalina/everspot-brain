---
trait: HasIcon
owning_module: Common
source_paths:
  - modules/Common/Traits/HasIcon.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasIcon

**Source:** `modules/Common/Traits/HasIcon.php`
**Registry entry:** [system/traits/index.md#hasicon](../../../system/traits/index.md#hasicon)

## Purpose

Maps Everspot model classes to Bootstrap Icons class strings, providing a uniform way to retrieve a model's UI icon. The mapping is maintained as a static array inside the trait. Any class not listed falls back to `bi-file-earmark-text`.

Applied on `BaseModel`, so all concrete Everspot models that extend `BaseModel` inherit it.

## Contributed Columns

None.

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getBootstrapIconClass()` | `static (string $modelClass): string` | Looks up `$modelClass` in the icon map and returns the Bootstrap icon class string (e.g. `'bi-person'`). Returns `'bi-file-earmark-text'` for unknown classes. |
| `getIcon()` | `static (): string` | Calls `getBootstrapIconClass(static::class)` — convenience method that returns the icon for the calling model. |

## Icon Map (as of built_at)

Key model mappings (representative, not exhaustive):

| Model | Icon |
|-------|------|
| User | `bi-people` |
| Customer | `bi-person` |
| Order | `bi-basket` |
| Interment | `bi-file-earmark-medical` |
| WorkOrder | `bi-tools` |
| TrustAccount | `bi-bank` |
| Property | `bi-pin-map-fill` |
| Event | `bi-calendar-event` |
| Task | `bi-list-check` |
| Report | `bi-book` |

## Configuration / Contract

No interface required. No properties to define. `BaseModel` uses this trait; all models that extend it inherit `getIcon()` automatically.

## Used By

Applied on `BaseModel` (inherited by all concrete models). Discoverable by `use HasIcon` in Everspot source.
