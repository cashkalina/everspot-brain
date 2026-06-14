---
model: DocCategory
module: Documentation
table: doc_categories
connection: central
primary_source: modules/Documentation/Models/DocCategory.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Documentation/Models/DocArticle.php
traits:
  - HasFactory
  - SoftDeletes
related_models: [DocArticle]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, admin]
---

# DocCategory

## Overview

The DocCategory model groups [DocArticle](./doc-article.md)s into logical sections within Everspot's built-in knowledge base. A category has a URL slug, a display name, a sort order, and a flag controlling whether it appears in the documentation navigation menu. Categories may be soft-deleted without removing their articles (the FK is nullable on `doc_articles`).

Like DocArticle, this model lives on the **central** database connection — documentation content is platform-wide, shared across all cemetery tenants.

Route model binding resolves categories by `slug` for human-readable URLs.

The `$defaultSort` property (`'order asc'`) is a custom sorting hint consumed by the application layer; categories are presented in ascending `order` value by default. The `publishedArticles()` relationship provides a pre-filtered view of articles whose `published_at` is in the past or present, ordered by `order` ascending — ready to serve directly to the documentation UI.

## Schema

<!-- rendered from schema/central.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| order | int | No | 0 | Sort order for display in the navigation menu |
| slug | varchar | No | - | URL-safe identifier; used as the route key |
| name | varchar | No | - | Human-readable category name |
| show_in_menu | tinyint | No | 1 | Whether the category appears in the documentation navigation menu |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** _None._

**Indexes:** Primary key only.

## Casts

_None._

## Attributes

**Guarded:** _None declared_ (inherits from BaseModel)
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `$defaultSort = 'order asc'` — application-layer sort hint (not a DB default)

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for seeding and testing
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — categories are soft-deleted rather than hard-deleted

## Relationships

- `docArticles()` — has many [DocArticle](./doc-article.md): all articles (including unpublished) in this category
- `publishedArticles()` — has many [DocArticle](./doc-article.md): articles with `published_at ≤ now()`, ordered by `order` ascending; the primary consumer-facing relationship

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getRouteKeyName(): string` — returns `'slug'`; routes resolve categories by their URL slug rather than numeric `id`

## Routing

`getRouteKeyName()` returns `'slug'`, so route model binding resolves categories by their URL-safe slug.

## Common Usage

```php
// Find a category by slug
$category = DocCategory::where('slug', 'getting-started')->firstOrFail();

// All published articles in order
$articles = $category->publishedArticles()->get();

// All categories shown in menu, sorted by order
$menuCategories = DocCategory::where('show_in_menu', true)
    ->orderBy('order')
    ->get();

// Create a new category
$category = DocCategory::create([
    'slug'         => 'advanced-features',
    'name'         => 'Advanced Features',
    'order'        => 10,
    'show_in_menu' => true,
]);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
