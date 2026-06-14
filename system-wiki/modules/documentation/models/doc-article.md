---
model: DocArticle
module: Documentation
table: doc_articles
connection: central
primary_source: modules/Documentation/Models/DocArticle.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Documentation/Models/DocCategory.php
traits:
  - HasFactory
  - SoftDeletes
related_models: [DocCategory]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, admin]
---

# DocArticle

## Overview

The DocArticle model represents a single help or documentation article within Everspot's built-in knowledge base. Each article belongs to a [DocCategory](./doc-category.md) and contains authored content — a title, URL slug, optional description, and rich text body (`content`). Articles are published by setting a `published_at` timestamp; unpublished articles are accessible to administrators but hidden from front-end consumers.

This model lives on the **central** database connection, meaning articles are global to the Everspot platform rather than per-tenant. This makes sense because documentation content is authored by Everspot staff and shared across all cemetery tenants.

Route model binding resolves articles by `slug` rather than `id`, keeping URLs human-readable (e.g., `/docs/how-to-add-a-customer`).

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| doc_category_id | bigint | Yes | - | FK → doc_categories: the parent category (nullable for uncategorized articles) |
| order | int | No | 0 | Display sort order within the category |
| slug | varchar | No | - | URL-safe identifier; used as the route key |
| title | varchar | No | - | Article title |
| description | varchar | Yes | - | Short summary or excerpt |
| content | text | Yes | - | Full article body (rich text) |
| show_in_menu | tinyint | No | 1 | Whether the article appears in the documentation navigation menu |
| published_at | datetime | Yes | - | Publication timestamp; `null` means unpublished/draft |
| published_by | bigint | Yes | - | FK → users: the user who published the article |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `doc_category_id` → `doc_categories.id`; `published_by` → `users.id`

**Indexes:** FK-backing indexes on `doc_category_id`, `published_by`

## Casts

_None._

## Attributes

**Guarded:** _None declared_ (inherits from BaseModel)
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for seeding and testing
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — articles are soft-deleted rather than hard-deleted, preserving audit history

## Relationships

- `docCategory()` — belongs to [DocCategory](./doc-category.md): the category this article belongs to

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getRouteKeyName(): string` — returns `'slug'`; routes resolve articles by their URL slug rather than numeric `id`

## Routing

`getRouteKeyName()` returns `'slug'`, so route model binding resolves articles by their URL-safe slug.

## Common Usage

```php
// Find an article by slug (route model binding)
$article = DocArticle::where('slug', 'how-to-add-a-customer')->firstOrFail();

// Published articles in a category
$articles = DocCategory::where('slug', 'getting-started')
    ->first()
    ->publishedArticles()
    ->get();

// Create a draft article
$article = DocArticle::create([
    'doc_category_id' => $category->id,
    'slug'            => 'new-feature-guide',
    'title'           => 'New Feature Guide',
    'content'         => '<p>Content here...</p>',
    'show_in_menu'    => true,
]);

// Publish it
$article->update([
    'published_at' => now(),
    'published_by' => auth()->id(),
]);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
