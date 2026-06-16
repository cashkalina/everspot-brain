---
model: Media
module: Common
table: media
connection: tenant
primary_source: modules/Common/Models/Media.php
source_paths:
  - modules/Common/Models/ListOption.php
traits:
  - HasExternalIds
  - HasTags
  - SoftDeletes
related_models: [ListOption]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, core]
---

# Media

## Overview

The Media model is Everspot's customized extension of Spatie MediaLibrary's base `Media` model. It adds three cross-cutting concerns on top of the standard media table: external ID tracking ([HasExternalIds](../../../system/traits/index.md#hasexternalids)), polymorphic tagging ([HasTags](../../../system/traits/index.md#hastags)), and soft deletes ([SoftDeletes](../../../system/traits/index.md#softdeletes)).

In addition to inherited fields, Everspot adds an `is_public` flag that controls whether files are publicly accessible. The `getFormattedCollectionNameAttribute()` accessor resolves the collection's display name from a [ListOption](./list-option.md) row when possible, falling back to a human-formatted string. The `getFileTypeIconURL()` method provides a file-type icon URL for the UI based on file extension.

The model inherits the full Spatie MediaLibrary feature set (file storage, conversions, responsive images) from its parent, and adds `['tags', 'model']` to `$with` for eager loading.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_type | varchar | No | - | Morph type — the owning model class |
| model_id | bigint | No | - | Morph ID — the owning model's primary key |
| uuid | char | Yes | - | Unique identifier for the media file |
| collection_name | varchar | No | - | Media collection name (e.g. `avatar`, `custom_documents`) |
| name | varchar | No | - | Display name |
| file_name | varchar | No | - | File name on disk |
| mime_type | varchar | Yes | - | MIME type |
| disk | varchar | No | - | Storage disk identifier |
| conversions_disk | varchar | Yes | - | Disk for image conversions |
| size | bigint | No | - | File size in bytes |
| manipulations | json | No | - | Image manipulation instructions |
| custom_properties | json | No | - | Custom metadata properties |
| is_public | tinyint | No | 0 | Whether this file is publicly accessible |
| generated_conversions | json | No | - | Conversion generation status |
| responsive_images | json | No | - | Responsive image srcset data |
| order_column | int | Yes | - | Sort order within the collection |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** None (polymorphic — no enforced FK constraint)

**Indexes:** Composite index on (`model_type`, `model_id`).

## Casts

- `is_public` → `boolean` (merged with parent's casts via `array_merge(parent::casts(), [...])`)

<!-- trait-contributed casts and parent BaseMedia casts are documented in the respective trait/library docs, not here -->

## Attributes

**Fillable:** `['name', 'collection_name', 'is_public']`

**Eager loads (`$with`):** `['tags', 'model']`

## Accessors & Mutators

- `getFormattedCollectionNameAttribute(): string` — resolves the collection's display name; if `model` is loaded, looks up a `ListOption` by type `media_collection_{model_class_snake}` and key `{type_key}-{collection_name}`; falls back to Str::title of `collection_name` with `custom_` prefix stripped
- `getFileTypeIconURL(): string` — returns a path to a file-type icon based on extension (pdf, cad, dwg, ttf, txt, doc/docx, xls/xlsx, ppt/pptx, jpg/jpeg, png, mp4/avi/mov, mp3/wav, zip/rar; generic placeholder for others)

## Traits

- [HasExternalIds](../../../system/traits/index.md#hasexternalids) — polymorphic external ID storage for cross-system file tracking
- [HasTags](../../../system/traits/index.md#hastags) — Spatie Tags for polymorphic tagging of media files
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — media records are soft-deleted, never hard-deleted

## Relationships

Inherits `model()` (morphTo: the owning model) from BaseMedia.

## Scopes

- `public($query)` — filters to `is_public = true`

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getAllUniqueTags(): Collection` *(static)* — returns a collection of all unique tag names across all media records
- `getFileTypeIconURL(): string` — returns the URL path for a file-type icon based on this file's extension

## Common Usage

```php
// Get public media
$publicFiles = Media::public()->get();

// Get all unique tags used on media
$tags = Media::getAllUniqueTags();

// Get file icon URL
$icon = $media->getFileTypeIconURL();  // '/assets/svg/brands/pdf-icon.svg'

// Get formatted collection name
echo $media->formatted_collection_name;   // 'Customer Documents'
```

## Imports

This model can be created/updated via spreadsheet import. See **[media](../imports/media.md)** for the column reference (valid headers, required fields, types, and conditional rules).

The import mechanism (upload → queued job → Excel) is documented in the [import subsystem](../../../system/imports.md).

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
