---
model: DocumentTemplate
module: Signature
table: document_templates
connection: tenant
primary_source: modules/Signature/Models/DocumentTemplate.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Signature/Models/Document.php
  - modules/Common/Models/User.php
traits:
  - HasFactory
  - SoftDeletes
related_models: [Document, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, integration]
---

# DocumentTemplate

## Overview

The DocumentTemplate model stores the reusable templates from which signature documents are generated. A template captures the raw `content` (the document body — likely HTML or a markup format), a `name` and optional `description` for identification, and a `config_data` JSON blob for flexible template-level configuration (such as field placement, signing zone definitions, or rendering options).

Templates are owned by the [User](../../common/models/user.md) who created them and can be reused across many [Document](./document.md) instances in different [DocumentEnvelope](./document-envelope.md)s. Soft deletes ensure that templates referenced by historical documents remain available for audit and regeneration purposes even after being retired.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| user_id | bigint | No | - | FK → users: the user who created this template |
| name | varchar | No | - | Template display name |
| description | text | Yes | - | Optional description of the template's purpose |
| content | text | No | - | Template body content (markup/HTML) |
| config_data | json | Yes | - | Flexible template configuration (field layout, signing zones, rendering options) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `user_id` → `users.id`

**Indexes:** `document_templates_user_id_foreign` on `user_id`

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['user_id', 'name', 'description', 'content', 'config_data']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for test/seeder use
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — templates are soft-deleted (`deleted_at`), never hard-deleted, so historical documents can still reference their originating template

## Relationships

- `user()` — belongs to [User](../../common/models/user.md) (`user_id`): the user who created this template
- `documents()` — has many [Document](./document.md): documents generated from this template

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._

## Common Usage

```php
// Create a new document template
$template = DocumentTemplate::create([
    'user_id'     => auth()->id(),
    'name'        => 'Interment Authorization',
    'description' => 'Standard interment authorization form for family signers.',
    'content'     => '<p>I hereby authorize...</p>',
    'config_data' => ['signing_zones' => [['page' => 1, 'x' => 72, 'y' => 640]]],
]);

// List all active templates
$templates = DocumentTemplate::all();

// Generate a document from this template inside an envelope
$document = $template->documents()->create([
    'document_envelope_id'  => $envelope->id,
    'storage_path_unsigned' => 'signatures/envelopes/3/doc-unsigned.pdf',
    'storage_path_signed'   => 'signatures/envelopes/3/doc-signed.pdf',
]);

// Soft-delete a retired template
$template->delete();

// Restore a template
$template->restore();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
