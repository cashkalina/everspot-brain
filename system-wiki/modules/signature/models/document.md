---
model: Document
module: Signature
table: documents
connection: tenant
primary_source: modules/Signature/Models/Document.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Signature/Models/DocumentEnvelope.php
  - modules/Signature/Models/DocumentTemplate.php
traits:
  - HasFactory
  - SoftDeletes
related_models: [DocumentEnvelope, DocumentTemplate]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, integration]
---

# Document

## Overview

The Document model represents a single document within a signature workflow. Each document is produced from a [DocumentTemplate](./document-template.md) and belongs to a [DocumentEnvelope](./document-envelope.md) — the envelope groups one or more documents together for a single signing event.

The model tracks two storage paths: one for the unsigned version of the document (the PDF before any signers have acted on it) and one for the final signed version. Documents carry soft deletes, meaning removed documents are archived rather than purged, which preserves the audit trail for completed signature events.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| document_envelope_id | bigint | No | - | FK → document_envelopes: the parent envelope |
| document_template_id | bigint | No | - | FK → document_templates: the template this document was generated from |
| storage_path_unsigned | varchar | No | - | Storage path for the unsigned document |
| storage_path_signed | varchar | No | - | Storage path for the signed document |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `document_envelope_id` → `document_envelopes.id`; `document_template_id` → `document_templates.id`

**Indexes:** `documents_document_envelope_id_foreign` on `document_envelope_id`; `documents_document_template_id_foreign` on `document_template_id`

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['document_envelope_id', 'document_template_id', 'storage_path_unsigned', 'storage_path_signed']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for test/seeder use
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — documents are soft-deleted (`deleted_at`), never hard-deleted, preserving the signed-document audit trail

## Relationships

- `documentEnvelope()` — belongs to [DocumentEnvelope](./document-envelope.md) (`document_envelope_id`): the parent envelope grouping this document into a signing event
- `documentTemplate()` — belongs to [DocumentTemplate](./document-template.md) (`document_template_id`): the template from which this document was generated

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
// Retrieve all documents for an envelope
$documents = $envelope->documents;

// Create a document from a template within an envelope
$document = Document::create([
    'document_envelope_id'  => $envelope->id,
    'document_template_id'  => $template->id,
    'storage_path_unsigned' => 'signatures/envelopes/1/doc-unsigned.pdf',
    'storage_path_signed'   => 'signatures/envelopes/1/doc-signed.pdf',
]);

// Soft-delete a document (archived, not destroyed)
$document->delete();

// Restore a soft-deleted document
$document->restore();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
