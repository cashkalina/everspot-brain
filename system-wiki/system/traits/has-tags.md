---
trait: HasTags
owning_module: framework
framework: Spatie\Tags\HasTags
source_paths:
  - vendor/spatie/laravel-tags/src/HasTags.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasTags

**Namespace:** `Spatie\Tags\HasTags`
**Package:** `spatie/laravel-tags`
**Registry entry:** [index.md#hastags](./index.md#hastags)

## Purpose

The Spatie Tags trait for attaching tags to Eloquent models. Tags are stored in a separate `tags` table and linked to models via a polymorphic `taggables` pivot table. Tags support localization and optional type grouping.

In Everspot, `HasTags` is used on the `Media` model (from `modules/Common/Models/Media.php`, which extends Spatie's base `Media` class) to allow categorizing media files with tags.

## Contributed Columns

No columns are added to the using model's table. Tags and their model associations live in the `tags` and `taggables` tables.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Description |
|--------|------|-------------|
| `tags()` | `MorphToMany` | All tags attached to this model (via `taggables` pivot). |

## Contributed Scopes

| Scope | Description |
|-------|-------------|
| `withAnyTags()` | Filters models that have at least one of the given tags. |
| `withAllTags()` | Filters models that have all of the given tags. |
| `withAnyTagsOfAnyType()` | Filters models with any tag of any type matching the given names. |

## Contributed Methods (key subset)

| Method | Description |
|--------|-------------|
| `attachTag($tag, $type)` | Attaches a tag; creates the tag if it does not exist. |
| `attachTags($tags, $type)` | Attaches multiple tags. |
| `detachTag($tag, $type)` | Removes a tag. |
| `detachTags($tags, $type)` | Removes multiple tags. |
| `syncTags($tags)` | Sets the model's tags to exactly the given set (detaches others). |
| `syncTagsWithType($tags, $type)` | Syncs tags of a specific type. |
| `tagsWithType($type)` | Returns tags of a given type. |

## Configuration / Contract

Using models must use `HasTags`. The `tags` and `taggables` tables must exist (migrated from the `spatie/laravel-tags` package). Tags can be optionally typed (string type discriminator); Everspot's use on `Media` does not constrain tag type.

## Used By

Used on `Modules\Common\Models\Media`. Discoverable by `use HasTags` / `use Spatie\Tags\HasTags` in Everspot source.
