---
trait: HasFiles
owning_module: Common
source_paths:
  - modules/Common/Traits/HasFiles.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasFiles

**Source:** `modules/Common/Traits/HasFiles.php`
**Registry entry:** [system/traits/index.md#hasfiles](../../../system/traits/index.md#hasfiles)

## Purpose

Wraps [Spatie MediaLibrary](https://spatie.be/docs/laravel-medialibrary) (`spatie/laravel-medialibrary`) to add file and image attachment support to Everspot models. Uses `InteractsWithMedia` internally, then adds dynamic media collection registration driven by `ListOption` database rows (keyed `media_collection_<model_snake_case>`), so collections can be managed by admin users without code deploys.

The User model is a special case: it uses a static `$fileCollections` property instead of dynamic discovery, since the User model may be loaded before the database is available.

Known single-file collections (`signed_authorization`, `obituary`, `signed_contract`, `avatar`) are automatically flagged `singleFile()`.

## Contributed Columns

No columns are added to the using model's table. MediaLibrary stores file metadata in the shared `media` table.

## Contributed Casts

None.

## Contributed Relationships

`InteractsWithMedia` (pulled in by this trait) adds a polymorphic `media()` relationship to the shared `media` table. File retrieval uses Spatie's standard `getMedia($collection)` / `getFirstMedia($collection)` API.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `registerMediaCollections()` | `(): void` | Called by Spatie at model instantiation. Registers dynamic collections from `ListOption` rows; falls back to static `$fileCollections` for the User model. |
| `getDynamicMediaCollections()` | `(): Collection` | Looks up `ListOption` rows typed `media_collection_<model_key>` and returns a `name → 'multiple'` map. Returns empty Collection if the type does not exist. |
| `isKnownSingleCollection()` | `(string $name): bool` | Returns `true` for `signed_authorization`, `obituary`, `signed_contract`, `avatar`. |
| `getAvailableMediaCollectionsAttribute()` | `(): array` | Accessor: returns `['collectionName' => 'Label']` map for use in UI selectors, driven by the same `ListOption` source. |
| `getCollectionLabel()` | `(string $collectionName): string` | Looks up the human-readable label for a collection from `ListOption`, falling back to `Str::headline($name)`. |

## Configuration / Contract

Using models must implement the `HasMedia` interface from Spatie:

```php
use Spatie\MediaLibrary\HasMedia;
use Modules\Common\Traits\HasFiles;

class Customer extends BaseModel implements HasMedia
{
    use HasFiles;
}
```

Collection definitions live in `ListOption` rows (type `media_collection_<snake_model>`). No static array is needed unless the model is the User model.

The Spatie MediaLibrary package must be installed and its `media` table migrated.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasFiles` across model docs, or `use HasFiles` in Everspot source.
