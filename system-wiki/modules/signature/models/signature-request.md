---
model: SignatureRequest
module: Signature
table: signature_requests
connection: tenant
primary_source: modules/Signature/Models/SignatureRequest.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Signature/Models/DocumentEnvelope.php
  - modules/Common/Models/User.php
traits:
  - HasFactory
related_models: [DocumentEnvelope, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, integration]
---

# SignatureRequest

## Overview

The SignatureRequest model represents a single request sent to a user to sign a [DocumentEnvelope](./document-envelope.md). It tracks the full lifecycle of one signing event: delivery (how and where the request was sent), the unique security `key` used to authenticate the signer's session, status progression (`sent`, `viewed`, `signed`, `expired`, etc.), and forensic metadata captured at the moment of signing (device, operating system, browser, and IP address).

Each [DocumentEnvelope](./document-envelope.md) may have multiple SignatureRequests — one per signer who is notified via a user account. The `delivery_method` and `delivery_address` fields record whether the request was delivered by email, SMS, or another channel. The timestamped activity fields (`sent_at`, `viewed_at`, `signed_at`, `expired_at`) provide a complete audit trail.

**Note:** The `signature_requests` table contains a `deleted_at` column in the database schema, but the model does not use the `SoftDeletes` trait. This column exists in the schema (likely from a migration) but is not activated at the model layer — no soft-delete behavior is in effect.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| document_envelope_id | bigint | No | - | FK → document_envelopes: the parent envelope this request belongs to |
| user_id | bigint | No | - | FK → users: the user being asked to sign |
| key | varchar | No | - | Unique security key for authenticating the signer's session |
| status | varchar | No | - | Request lifecycle status (e.g. `sent`, `viewed`, `signed`, `expired`) |
| delivery_method | varchar | No | - | How the request was delivered (e.g. `email`, `sms`) |
| delivery_address | varchar | Yes | - | The address the request was delivered to (email address, phone number, etc.) |
| sent_at | datetime | Yes | - | Timestamp when the request was sent |
| viewed_at | datetime | Yes | - | Timestamp when the signer first viewed the document |
| signed_at | datetime | Yes | - | Timestamp when the document was signed |
| expired_at | datetime | Yes | - | Timestamp when the request expired |
| signing_device | varchar | Yes | - | Device type detected at signing time |
| signing_os | varchar | Yes | - | Operating system detected at signing time |
| signing_browser | varchar | Yes | - | Browser detected at signing time |
| signing_ip | varchar | Yes | - | IP address from which the document was signed |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Present in schema but SoftDeletes trait is NOT used on this model |

**Primary key:** `id`

**Foreign keys:** `document_envelope_id` → `document_envelopes.id`; `user_id` → `users.id`

**Indexes:** `signature_requests_status_index` on `status`; `signature_requests_document_envelope_id_foreign` on `document_envelope_id`; `signature_requests_user_id_foreign` on `user_id`

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['document_envelope_id', 'user_id', 'key', 'status', 'delivery_method', 'delivery_address', 'sent_at', 'viewed_at', 'signed_at', 'expired_at', 'signing_device', 'signing_os', 'signing_browser', 'signing_ip']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for test/seeder use

## Relationships

- `user()` — belongs to [User](../../common/models/user.md) (`user_id`): the user being asked to sign the envelope
- `documentEnvelope()` — belongs to [DocumentEnvelope](./document-envelope.md) (`document_envelope_id`): the envelope this signing request is associated with

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
// Create a signature request for a user on an envelope
$request = SignatureRequest::create([
    'document_envelope_id' => $envelope->id,
    'user_id'              => $user->id,
    'key'                  => \Str::uuid(),
    'status'               => 'pending',
    'delivery_method'      => 'email',
    'delivery_address'     => $user->email,
    'sent_at'              => now(),
]);

// Mark as viewed
$request->update(['status' => 'viewed', 'viewed_at' => now()]);

// Mark as signed with forensic data
$request->update([
    'status'          => 'signed',
    'signed_at'       => now(),
    'signing_device'  => 'desktop',
    'signing_os'      => 'macOS 14',
    'signing_browser' => 'Chrome 124',
    'signing_ip'      => request()->ip(),
]);

// Query all signed requests for an envelope
$signed = $envelope->signatureRequests()->where('status', 'signed')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
