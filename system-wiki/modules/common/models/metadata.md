---
model: Metadata
module: Common
table: metadata
connection: tenant
primary_source: modules/Common/Models/Metadata.php
source_paths:
  - app/Models/BaseModel.php
traits:
  - SoftDeletes
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Metadata

## Overview

The Metadata model is a general-purpose contextual annotation store. It records a piece of metadata **for** one entity (the "owner", `for_type`/`for_id`) **on** another entity (the "subject", `on_type`/`on_id`), classified by a `MetadataType` enum value. Both sides are polymorphic morph-to relationships, and either can be `null` for global metadata that is not scoped to a specific owner.

The primary use case is tracking report run times: `setReportLastRun()` creates a global record and a per-user record when a report is executed, allowing the UI to show "last run" information. The model's static helpers (`setMetadata`, `getMetadata`, `removeMetadata`, `toggleMetadata`) provide a CRUD-style API over the polymorphic structure.

Activity logging is explicitly disabled (`$enableLoggingModelsEvents = false`) to prevent recursive logging. The model's `$table` is explicitly `'metadata'` (avoiding the `metadatas` Laravel default).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| for_type | varchar | Yes | - | Morph type of the owning entity (null for global metadata) |
| for_id | varchar | Yes | - | Morph ID of the owning entity (null for global metadata) |
| on_type | varchar | Yes | - | Morph type of the subject entity |
| on_id | varchar | Yes | - | Morph ID of the subject entity |
| type | varchar | No | - | Metadata type (cast to `MetadataType` enum) |
| data | json | Yes | - | Arbitrary metadata payload |
| performed_at | timestamp | Yes | - | Timestamp relevant to this metadata (e.g. report run time) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** None (polymorphic — no enforced FK constraints)

**Indexes:** None beyond primary key.

## Casts

- `data` → `array`
- `type` → `MetadataType::class` (enum)
- `performed_at` → `datetime`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — metadata records are soft-deleted, never hard-deleted

## Relationships

- `forRelation()` — morphTo (`for_type`/`for_id`): the owning entity this metadata belongs to
- `onRelation()` — morphTo (`on_type`/`on_id`): the subject entity this metadata is about

## Scopes

- `for($query, $forType, $forId)` — filters by owning entity
- `on($query, $onType, $onId)` — filters by subject entity
- `ofType($query, MetadataType $type)` — filters by metadata type

## Events

_None._

## Observers

_None registered._

## Key Methods

- `setMetadata($forType, $forId, $onType, $onId, MetadataType $type, ?array $data): BaseModel` *(static)* — upserts a metadata record
- `getMetadata($forType, $forId, $onType, $onId, MetadataType $type): ?BaseModel` *(static)* — retrieves a metadata record
- `removeMetadata($forType, $forId, $onType, $onId, MetadataType $type): bool` *(static)* — deletes a metadata record
- `toggleMetadata($forType, $forId, $onType, $onId, MetadataType $type, ?array $data): bool` *(static)* — creates the record if absent, deletes it if present; returns `true` if created
- `setReportLastRun($report, $user): void` *(static)* — creates/updates both a global and a per-user `LAST_RUN` metadata record for a report
- `getGlobalLastRun($report): ?self` *(static)* — retrieves the global `LAST_RUN` metadata for a report
- `getUserLastRun($report, $user): ?self` *(static)* — retrieves the per-user `LAST_RUN` metadata for a report
- `getActivitylogOptions(): LogOptions` — disables activity logging for this model

## Common Usage

```php
// Record that a user ran a report
Metadata::setReportLastRun($report, $user);

// Retrieve when a report was last run globally
$lastRun = Metadata::getGlobalLastRun($report);
echo $lastRun?->performed_at;

// Store arbitrary metadata for a model
Metadata::setMetadata(
    User::class, $userId,
    Order::class, $orderId,
    MetadataType::FAVORITE
);

// Toggle a favorite
$created = Metadata::toggleMetadata(User::class, $userId, Order::class, $orderId, MetadataType::FAVORITE);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
