---
model: PdfTemplate
module: Common
table: pdf_templates
connection: tenant
primary_source: modules/Common/Models/PdfTemplate.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/Cemetery.php
traits:
  - SoftDeletes
related_models: [Cemetery]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, admin]
---

# PdfTemplate

## Overview

The PdfTemplate model stores configurable PDF template definitions used throughout the system (invoices, certificates, owner files, etc.). Each template is associated with a model class (`model_class`), has a human-readable name and title, a URL-safe `slug`, optional HTML `content`, and an optional `pdf_attachments` JSON array for multi-page or appended documents.

Templates can be scoped to specific cemeteries via a `cemetery_pdf_template` pivot table, or apply to all cemeteries when no cemetery is associated (`appliesToAllCemeteries()`). Paper size and orientation defaults are `'letter'` and `'portrait'` respectively when not explicitly set.

The `is_advanced` flag enables a rich editor mode. The model supports soft deletes. It has no observers.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_class | varchar | No | - | Fully qualified model class this template renders |
| name | varchar | No | - | Internal template name |
| title | varchar | No | - | Display title |
| slug | varchar | No | - | URL-safe identifier used in routes |
| content | text | Yes | - | HTML template content |
| pdf_attachments | json | Yes | - | Array of attached PDF definitions with `position` and `order` |
| paper_size | varchar | Yes | - | Paper size (default: `letter`) |
| paper_orientation | varchar | Yes | - | Paper orientation (default: `portrait`) |
| is_active | tinyint | No | 1 | Whether this template is active |
| is_advanced | tinyint | No | 0 | Whether advanced editing mode is enabled |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

- `is_active` → `boolean`
- `is_advanced` → `boolean`
- `pdf_attachments` → `array`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — PDF templates are soft-deleted, never hard-deleted

## Relationships

- `cemeteries()` — belongs-to-many [Cemetery](./cemetery.md) via `cemetery_pdf_template`: cemeteries this template applies to (empty = applies to all)

## Scopes

- `active($query): Builder` — filters to `is_active = true`
- `forCemeteryId($query, int $cemeteryId): Builder` — active templates that either have no cemetery restriction or include the given cemetery
- `forModel($query, Model $model): Builder` — active templates for the given model's class; if model has a `cemetery` relation, further restricts to `forCemeteryId`
- `forModelClass($query, string $modelClass): Builder` — active templates for the given model class string

## Events

_None._

## Observers

_None registered._

## Key Methods

- `appliesToAllCemeteries(): bool` — returns `true` when the template has no associated cemeteries
- `isAdvanced(): bool` — returns `true` when `is_advanced` is set
- `hasAttachments(): bool` — returns `true` when `pdf_attachments` is non-empty
- `hasContent(): bool` — returns `true` when `content` is non-empty
- `getBeforeAttachments(): array` — returns the subset of `pdf_attachments` with `position = 'before'`, sorted by `order`
- `getAfterAttachments(): array` — returns the subset of `pdf_attachments` with `position = 'after'`, sorted by `order`
- `getPaperSize(): string` — returns `paper_size` or `'letter'` if not set
- `getPaperOrientation(): string` — returns `paper_orientation` or `'portrait'` if not set
- `getUrlForModel($model): string` — generates the route URL for rendering this template for a given model instance (`app.pdf.view` route)

## Common Usage

```php
// Find a template for an Order at a specific cemetery
$template = PdfTemplate::forModel($order)->first();

// Generate the PDF view URL
$url = $template->getUrlForModel($order);

// Enumerate before/after attachments
$before = $template->getBeforeAttachments();
$after  = $template->getAfterAttachments();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
