---
model: Signer
module: Signature
table: signers
connection: tenant
primary_source: modules/Signature/Models/Signer.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Signature/Models/DocumentEnvelope.php
  - modules/Customer/Models/Customer.php
traits:
  - HasFactory
  - SoftDeletes
related_models: [Customer, DocumentEnvelope]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, customer, integration]
---

# Signer

## Overview

The Signer model represents an individual who is required to sign the documents within a [DocumentEnvelope](./document-envelope.md). Signers are identified by a display `name` and may optionally be linked to an existing [Customer](../../customer/models/customer.md) record.

The optional `customer_id` link supports the common case where the person signing is a known Everspot customer (e.g. the family member authorizing an interment). When the signer is not in the customer registry — for example, an external funeral director — the link is left null and only the free-text `name` is used. Soft deletes preserve the signer record within the envelope's audit trail even after a signer is removed from an active workflow.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| customer_id | bigint | Yes | - | FK → customers: optional link to a customer record |
| document_envelope_id | bigint | No | - | FK → document_envelopes: the envelope this signer belongs to |
| name | varchar | No | - | Display name of the signer |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `customer_id` → `customers.id`; `document_envelope_id` → `document_envelopes.id`

**Indexes:** `signers_customer_id_foreign` on `customer_id`; `signers_document_envelope_id_foreign` on `document_envelope_id`

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['customer_id', 'document_envelope_id', 'name']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for test/seeder use
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — signers are soft-deleted (`deleted_at`), never hard-deleted, preserving the envelope audit trail

## Relationships

- `customer()` — belongs to [Customer](../../customer/models/customer.md) (`customer_id`): optional link to the Everspot customer who is signing; `null` for external signers
- `documentEnvelope()` — belongs to [DocumentEnvelope](./document-envelope.md) (`document_envelope_id`): the parent envelope for this signing participant

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
// Add a customer-linked signer to an envelope
$signer = Signer::create([
    'document_envelope_id' => $envelope->id,
    'customer_id'          => $customer->id,
    'name'                 => $customer->full_name,
]);

// Add an external (non-customer) signer
$externalSigner = Signer::create([
    'document_envelope_id' => $envelope->id,
    'customer_id'          => null,
    'name'                 => 'Jane Smith (Funeral Director)',
]);

// List all signers for an envelope
$signers = $envelope->signers;

// Check if a specific customer is a signer
$isSigner = $envelope->signers()->where('customer_id', $customer->id)->exists();

// Soft-delete a signer
$signer->delete();

// Restore a signer
$signer->restore();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
