---
model: DocumentEnvelope
module: Signature
table: document_envelopes
connection: tenant
primary_source: modules/Signature/Models/DocumentEnvelope.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Signature/Models/Document.php
  - modules/Signature/Models/Signer.php
  - modules/Signature/Models/SignatureRequest.php
  - modules/Common/Models/User.php
traits:
  - HasFactory
  - SoftDeletes
related_models: [Document, SignatureRequest, Signer, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, integration]
---

# DocumentEnvelope

## Overview

The DocumentEnvelope model is the central orchestrating record for a signature workflow in Everspot. An envelope bundles one or more [Document](./document.md)s together and manages their signing lifecycle from creation through completion.

An envelope tracks its overall `status`, storage paths for both the combined unsigned and signed versions, and is owned by the [User](../../common/models/user.md) who created it. Each envelope has a set of [Signer](./signer.md)s — the individuals who must sign — and a set of [SignatureRequest](./signature-request.md)s that drive delivery and tracking of signing tasks to each user or contact.

The model carries soft deletes so that envelopes removed from active workflows are archived with their associated audit data intact.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| user_id | bigint | No | - | FK → users: the user who created this envelope |
| status | varchar | No | - | Envelope lifecycle status |
| storage_path_unsigned | varchar | No | - | Storage path for the combined unsigned document(s) |
| storage_path_signed | varchar | No | - | Storage path for the combined signed document(s) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `user_id` → `users.id`

**Indexes:** `document_envelopes_status_index` on `status`; `document_envelopes_user_id_foreign` on `user_id`

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['user_id', 'status', 'storage_path_unsigned', 'storage_path_signed']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for test/seeder use
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — envelopes are soft-deleted (`deleted_at`), never hard-deleted, preserving the complete signature audit trail

## Relationships

- `user()` — belongs to [User](../../common/models/user.md) (`user_id`): the user who created this envelope
- `documents()` — has many [Document](./document.md): the documents bundled in this envelope
- `signers()` — has many [Signer](./signer.md): the individuals required to sign documents in this envelope
- `signatureRequests()` — has many [SignatureRequest](./signature-request.md): the individual signing requests sent to users for this envelope

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
// Create a new envelope
$envelope = DocumentEnvelope::create([
    'user_id'               => auth()->id(),
    'status'                => 'draft',
    'storage_path_unsigned' => 'signatures/envelopes/1/combined-unsigned.pdf',
    'storage_path_signed'   => 'signatures/envelopes/1/combined-signed.pdf',
]);

// Add documents to the envelope
$envelope->documents()->create([
    'document_template_id'  => $template->id,
    'storage_path_unsigned' => 'signatures/envelopes/1/doc-unsigned.pdf',
    'storage_path_signed'   => 'signatures/envelopes/1/doc-signed.pdf',
]);

// Add signers
$envelope->signers()->create([
    'customer_id' => $customer->id,
    'name'        => $customer->full_name,
]);

// Retrieve all signature requests for an envelope
$requests = $envelope->signatureRequests;

// Query envelopes by status
$pending = DocumentEnvelope::where('status', 'pending')->get();

// Soft-delete an envelope
$envelope->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
