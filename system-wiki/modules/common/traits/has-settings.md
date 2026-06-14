---
trait: HasSettings
owning_module: Common
source_paths:
  - modules/Common/Traits/HasSettings.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasSettings

**Source:** `modules/Common/Traits/HasSettings.php`
**Registry entry:** [system/traits/index.md#hassettings](../../../system/traits/index.md#hassettings)

## Purpose

Attaches a key-value settings store to any model via the `Setting` model (`settingable` polymorphic relationship). All read and write operations are routed through `settingSvc()` (a Laravel service singleton that handles caching and value casting), ensuring consistent behavior and cache invalidation across the codebase.

The Tenant model is a special case: because it operates on the central database, settings for Tenant are queried without the standard polymorphic morph through `Setting::where(...)` directly rather than via `morphMany`.

## Contributed Columns

No columns are added to the using model's table. Settings live in the `settings` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type / Return | Description |
|--------|--------------|-------------|
| `settings()` | `MorphMany` (or query builder for Tenant) | All `Setting` rows for this model. |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getSetting()` | `(string $key, mixed $default = null): mixed` | Reads a setting value via `settingSvc()->getDirectSetting($this, $key)`. Returns `$default` if not set. |
| `setSetting()` | `(string $key, mixed $value): mixed` | Writes a setting value via `settingSvc()->setSetting($this, $key, $value)`. |
| `hasSetting()` | `(string $key): bool` | Returns `true` if `getSetting($key)` is non-null. |
| `forgetSetting()` | `(string $key): int` | Deletes a single setting via `settingSvc()->deleteSetting()`; returns 1 for backward compat. |
| `forgetAllSettings()` | `(): int` | Deletes all settings for the model; returns the count of deleted rows. |
| `settings()` | `(void): MorphMany\|Builder` | Returns the relationship/query for all settings rows. |

## Configuration / Contract

No interface required. The `Setting` model and its `settings` table must exist (part of the Common module's schema). The `settingSvc()` global helper must be bound in the service container.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasSettings` across model docs, or `use HasSettings` in Everspot source.
