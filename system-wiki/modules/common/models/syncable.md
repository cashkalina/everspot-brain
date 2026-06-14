---
model: Syncable
module: Common
table: syncables
connection: tenant
primary_source: modules/Common/Models/Syncable.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/Integration.php
traits:
  - HasSchemalessAttributes
  - SoftDeletes
related_models: [Integration]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [integration]
---

# Syncable

## Overview

The Syncable model is the per-record sync state tracker for external integrations. Each row represents one Everspot record's connection to one external system entity. It links via polymorphic `syncable` (the Everspot model) to an [Integration](./integration.md), and stores the external system's `external_id`, the external model type, sync flags, timestamps, and error data.

The [HasSyncables](../../../system/traits/index.md#hassyncables) trait on other models provides the `syncable()`/`syncables()` relationships that reach these rows. Direct methods on `Syncable` expose force-push/pull operations against the integration's implementation.

A `Syncable` row is soft-deleted rather than hard-deleted when the sync link is removed.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| syncable_type | varchar | No | - | Morph type — the Everspot model class |
| syncable_id | varchar | No | - | Morph ID — the Everspot record's primary key |
| integration_id | bigint | No | - | FK → integrations: the external integration |
| external_id | varchar | Yes | - | ID of this record in the external system |
| external_model_type | varchar | No | - | The external system's entity type name |
| initial_sync_enabled | tinyint | No | - | Whether initial sync is enabled for this record |
| initial_sync_completed | tinyint | No | 0 | Whether the initial sync has completed |
| recurring_sync_enabled | tinyint | No | - | Whether recurring sync is enabled |
| last_synced_at | datetime | Yes | - | When this record was last synced |
| error_data | json | Yes | - | Sync error details |
| config_data | json | Yes | - | Sync configuration (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `integration_id` → `integrations.id`

**Indexes:** Composite index on (`syncable_type`, `syncable_id`); FK-backing index on `integration_id`.

## Casts

- `last_synced_at` → `TimezonedDateTime::class` (timezone-aware datetime)
- `error_data` → `array`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` JSON with dot-notation access for sync-specific configuration
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — syncable records are soft-deleted, never hard-deleted

## Relationships

- `syncable()` — morphTo: the Everspot model this sync row tracks
- `integration()` — belongs to [Integration](./integration.md) (`integration_id`): the external integration

## Scopes

- `forIntegration($query, Integration $integration): Builder` — filters by integration ID
- `forExternalType($query, $externalModelType): Builder` — filters by `external_model_type`
- `forInternalType($query, $internalModelType): Builder` — filters by `syncable_type`
- `forExternalId($query, $externalId): Builder` — filters by `external_id`
- `forExternalModel($query, $externalModelType, $externalId): Builder` — combines `forExternalType` + `forExternalId`
- `hasActiveIntegrationWith($query, $systemType): Builder` — whereHas on integration for active integrations of the given system type

## Events

_None._

## Observers

_None registered._

## Key Methods

- `isSynced(): bool` — returns `true` when `initial_sync_completed = true` and `last_synced_at` is not null
- `forcePushUpdate(): void` — calls `integration->getImplementation()->update()` with force flag to push this record's current state to the external system
- `forcePullUpdate(): void` — calls `integration->getImplementation()->pullUpdate()` to overwrite this record from the external system
- `forcePushDelete(): void` — calls `integration->getImplementation()->delete()` with force flag to delete this record in the external system

## Common Usage

```php
// Check if a record is synced to QuickBooks
$syncable = $customer->syncables()
    ->hasActiveIntegrationWith('qbo')
    ->first();

if ($syncable && $syncable->isSynced()) {
    echo "Customer is synced. External ID: {$syncable->external_id}";
}

// Force push an update to the external system
$syncable->forcePushUpdate();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
