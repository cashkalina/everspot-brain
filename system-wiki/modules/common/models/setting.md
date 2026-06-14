---
model: Setting
module: Common
table: settings
connection: tenant
primary_source: modules/Common/Models/Setting.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/SettingObserver.php
traits:
  - HasByUserFields
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Setting

## Overview

The Setting model is the polymorphic key-value store that powers the `setting()` helper throughout Everspot. Settings are scoped to any "settingable" entity (Cemetery, Tenant, User, etc.) and keyed by a string. Values can be stored in `value` (text) or `json_value` (JSON) columns depending on `type`, with casting applied dynamically at read time.

The `getValueAttribute()` accessor is the central feature: it reads the appropriate raw column based on `type`, then dispatches to `CastSettingValue` to apply the correct cast (boolean, integer, float, date, json, or string) based on a large lookup map in `getSettingDefaultCast()`. Some setting keys map to value object classes (e.g. `memorials-module-config` → `MemorialConfig`), resolved via `getSettingValueObjectClass()`.

The [HasSettings](../../../system/traits/index.md#hassettings) trait on models is the consumer of this table — it provides the `settingSvc()` method and caches setting reads. `SettingObserver` clears caches when settings are saved or deleted.

Note: This model has no `deleted_at` column — it does not use soft deletes. The `created_by`/`updated_by`/`deleted_by` columns are present (via `HasByUserFields`) but there is no `deleted_by` column in the `settings` table schema.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| settingable_type | varchar | No | - | Morph type — the class of the owning entity |
| settingable_id | varchar | No | - | Morph ID — the owning entity's primary key |
| key | varchar | No | - | Setting key |
| value | text | Yes | - | Setting value (for non-JSON types) |
| json_value | json | Yes | - | Setting value (for JSON type) |
| type | varchar | No | string | Value type hint (`string`, `boolean`, `integer`, `float`, `date`, `json`) |
| value_class | varchar | Yes | - | Optional value object class for deserialization |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** Composite index on (`settingable_type`, `settingable_id`, `key`) (unique per-entity setting).

## Casts

- `json_value` → `array`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

- `getValueAttribute($value): mixed` — reads `json_value` or `value` depending on `type`, then applies the cast from `CastSettingValue` action using the key's type and optional value class
- `getFormattedKeyAttribute(): string` — title-cases the `key` (underscores replaced with spaces)
- `getModelInferredName(): ?string` — returns `formatted_key`

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps

## Relationships

- `settingable()` — morphTo: the entity this setting belongs to (Cemetery, Tenant, User, etc.)

## Scopes

_None._

## Events

_None._

## Observers

- `SettingObserver` — registered in `CommonServiceProvider::registerObservers()` (`Setting::observe(SettingObserver::class)`). Handles:
  - `saving` — validates setting data
  - `created`, `updated`, `deleted`, `restored`, `forceDeleted` — clears the setting cache for the affected settingable

## Key Methods

- `getSettingDefaultCast(): string` — returns the cast type for this setting's key from a large lookup map; defaults to `'string'` for unrecognized keys
- `getSettingValueObjectClass(): ?string` — returns the value object class for known keys (e.g. `'memorials-module-config'` → `MemorialConfig::class`); `null` for most keys

## Common Usage

```php
// Read a setting (via the global helper — preferred)
$timezone = setting('timezone', $cemetery);

// Direct model access
$setting = Setting::where('settingable_type', Cemetery::class)
    ->where('settingable_id', $cemetery->id)
    ->where('key', 'timezone')
    ->first();

echo $setting->value;   // already cast to string

// Formatted key for display
echo $setting->formatted_key;  // "Timezone"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
