---
trait: InteractsWithMedia
owning_module: framework
framework: Spatie\MediaLibrary\InteractsWithMedia
source_paths:
  - vendor/spatie/laravel-medialibrary/src/InteractsWithMedia.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# InteractsWithMedia

**Namespace:** `Spatie\MediaLibrary\InteractsWithMedia`
**Package:** `spatie/laravel-medialibrary`
**Registry entry:** [index.md#interactswithmedia](./index.md#interactswithmedia)

## Purpose

The Spatie MediaLibrary trait for attaching files and images to Eloquent models. Stores file metadata in a shared `media` table and manages file storage (S3, local, etc.) via configurable disks. Supports media collections, conversions (e.g. thumbnails), and a rich API for adding, retrieving, and deleting media.

In Everspot, `InteractsWithMedia` is pulled in by the Everspot-owned `HasFiles` trait (`modules/Common/Traits/HasFiles.php`). Models that need file attachments should use `HasFiles` (not `InteractsWithMedia` directly), which adds dynamic collection management driven by `ListOption` database rows.

Direct use of `InteractsWithMedia` (without `HasFiles`) appears only on models like `Map` that have simple, static collection needs.

## Contributed Columns

No columns are added to the using model's table. All media metadata lives in the shared `media` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Description |
|--------|------|-------------|
| `media()` | `MorphMany` | All media records attached to this model (via `model_type` / `model_id` on the `media` table). |

## Contributed Methods (key subset)

| Method | Description |
|--------|-------------|
| `addMedia($file)` | Fluent builder to attach a file; call `.toMediaCollection('name')` to finalize. |
| `addMediaFromUrl($url)` | Add media from a URL. |
| `addMediaFromDisk($path, $disk)` | Add media from a disk path. |
| `getMedia($collection)` | Returns a `MediaCollection` of `Media` models for the given collection. |
| `getFirstMedia($collection)` | Returns the first `Media` in the collection. |
| `getFirstMediaUrl($collection, $conversion)` | Returns the URL of the first media item, optionally for a named conversion (e.g. thumbnail). |
| `clearMediaCollection($collection)` | Deletes all media in the given collection. |
| `registerMediaCollections()` | Override this to define named collections (called automatically). |
| `registerMediaConversions()` | Override this to define image conversion pipelines. |

## Configuration / Contract

Using models must implement the `HasMedia` interface from Spatie:

```php
use Spatie\MediaLibrary\HasMedia;
use Spatie\MediaLibrary\InteractsWithMedia;

class MyModel extends BaseModel implements HasMedia
{
    use InteractsWithMedia;

    public function registerMediaCollections(): void
    {
        $this->addMediaCollection('documents');
        $this->addMediaCollection('avatar')->singleFile();
    }
}
```

In Everspot, prefer using `HasFiles` (which wraps this trait) for module models. The `spatie/laravel-medialibrary` package must be installed and its `media` table migrated.

## Used By

Used indirectly via `HasFiles` by all models that attach files. Used directly on `Map` and `ExternalApprovalFile`. Discoverable by `use InteractsWithMedia` or `use HasFiles` in Everspot source.
