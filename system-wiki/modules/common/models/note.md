---
model: Note
module: Common
table: notes
connection: tenant
primary_source: modules/Common/Models/Note.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Scopes/MostRecentlyCreatedSort.php
  - modules/Common/Models/User.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# Note

## Overview

The Note model stores free-text notes that can be attached to any notable entity via a polymorphic `notable` relationship. Notes appear throughout the system on Customers, OwnerFiles, Entities, Opportunities, and other models that define a `notes()` morphMany relationship.

Each note tracks the authoring user (`user_id` / `user()` relationship), the authored timestamp (`authored_at`, defaulted to `now()` on create if not provided), and optional alert behavior (`is_alert`, `alert_expires_at`). An alert note is visually surfaced to users and optionally expires at a set time. The `isActiveAlert()` method encapsulates this expiry logic.

A global scope (`MostRecentlyCreatedSort`) is applied in `booted()`, so note queries are ordered newest-first by default. Notes carry soft deletes and audit user stamps via traits.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| user_id | bigint | No | - | FK → users: the user who authored this note |
| authored_at | datetime | Yes | - | When the note was authored (defaults to now() on create) |
| content | text | No | - | Note content |
| is_alert | tinyint | No | 0 | Whether this note is an active alert |
| alert_expires_at | datetime | Yes | - | When the alert expires (null = never expires) |
| notable_type | varchar | No | - | Morph type — the class name of the owning model |
| notable_id | bigint | No | - | Morph ID — the owning model's primary key |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `user_id` → `users.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** Composite index on (`notable_type`, `notable_id`); FK-backing indexes on `user_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `is_alert` → `boolean`
- `alert_expires_at` → `TimezonedDateTime::class` (timezone-aware datetime)
- `authored_at` → `TimezonedDateTime::class` (timezone-aware datetime)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — notes are soft-deleted, never hard-deleted

## Relationships

- `notable()` — morphTo: the owning model (may be Customer, OwnerFile, Entity, Opportunity, or any notable model)
- `user()` — belongs to [User](./user.md) (`user_id`): the user who authored the note

## Scopes

**Global scope:** `MostRecentlyCreatedSort` — applied in `booted()`; orders all Note queries by `created_at` descending by default.

## Events

- `booted()` — `creating` hook: sets `authored_at = now()` if not already set

## Observers

_None registered._

## Key Methods

- `isEdited(): bool` — returns `true` when `created_at` and `updated_at` both exist and are not equal (i.e. the note has been modified after creation)
- `isActiveAlert(): bool` — returns `false` when not an alert; `true` when alert has no expiry or expiry is in the future

## Common Usage

```php
// Add a note to a customer
$customer->notes()->create([
    'user_id'  => auth()->id(),
    'content'  => 'Called to confirm appointment.',
]);

// Add an expiring alert note
$customer->notes()->create([
    'user_id'          => auth()->id(),
    'content'          => 'Outstanding balance — contact before service.',
    'is_alert'         => true,
    'alert_expires_at' => now()->addDays(30),
]);

// Check if a note is an active alert
if ($note->isActiveAlert()) {
    // display alert banner
}

// Notes come back newest-first by default (global scope)
$recentNotes = $customer->notes()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
