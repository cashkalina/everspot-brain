---
model: Integration
module: Common
table: integrations
connection: tenant
primary_source: modules/Common/Models/Integration.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/IntegrationObserver.php
  - modules/Common/Models/Syncable.php
  - modules/Common/Models/Token.php
traits:
  - HasSchemalessAttributes
related_models: [Syncable, Token]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [integration, core]
---

# Integration

## Overview

The Integration model represents a connection between the tenant and an external system — such as QuickBooks Online (`qbo`), Stripe (`stripe`), or a default accounting/payment implementation. Each row stores the system type, an optional system-specific ID, connection/disconnection timestamps, and a `pause_syncing` flag for temporarily halting sync operations. The `config_data` JSON column (via `HasSchemalessAttributes`) holds integration-specific configuration.

Only one active integration per `system_type` is allowed at a time (enforced by `failIfOtherActiveIntegration()`). The `getImplementation()` factory method returns the appropriate integration implementation object for use in sync operations. Each integration links to its OAuth or API token via a polymorphic `Token`, and has many [Syncable](./syncable.md) rows tracking per-record sync state.

Lifecycle events are handled by `IntegrationObserver`, registered in `CommonServiceProvider`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| system_type | varchar | No | - | Integration type identifier (e.g. `qbo`, `stripe`) |
| system_id | varchar | Yes | - | External system account/company ID |
| connected_at | datetime | No | - | When the integration was connected |
| disconnected_at | datetime | Yes | - | When the integration was disconnected (null = still active) |
| pause_syncing | tinyint | No | 0 | When true, sync operations are paused |
| config_data | json | Yes | - | Integration-specific config (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

- `connected_at` → `TimezonedDateTime::class` — timezone-aware datetime
- `disconnected_at` → `TimezonedDateTime::class` — timezone-aware datetime
- `pause_syncing` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['system_type', 'system_id', 'connected_at', 'disconnected_at', 'pause_syncing']`

**Disabled report columns:** `config_data`

## Accessors & Mutators

_None._

## Traits

- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` JSON with dot-notation access for integration-specific configuration

## Relationships

- `token()` — morphOne [Token](./token.md) (`tokenable`): the OAuth/API token for this integration
- `syncables()` — has many [Syncable](./syncable.md): per-record sync state rows for this integration

## Scopes

- `active($query): Builder` — connected integrations (`connected_at` not null, `disconnected_at` is null)
- `mostRecentSameSystems($query, $systemType, $systemId): Builder` — recently disconnected integrations matching the same system type and ID, ordered by `disconnected_at` descending

## Events

_None._

## Observers

- `IntegrationObserver` — registered in `CommonServiceProvider::registerObservers()` (`Integration::observe(IntegrationObserver::class)`). Handles:
  - `saving`, `saved` — pre/post save hooks (e.g. validation, cache clearing)
  - `created`, `updated`, `deleted`, `restored`, `forceDeleted` — lifecycle side effects

## Key Methods

- `failIfOtherActiveIntegration(): void` — throws `\Exception` if another active integration of the same `system_type` exists (enforces the one-active-per-type rule)
- `getImplementation(): \Modules\Common\Support\Integrations\Integration` — factory method; returns the concrete implementation instance for this integration's `system_type` (matches `qbo` → `QBOAccountingSystem`, `stripe` → `StripePaymentProcessor`, etc.)
- `getModelInferredName(): ?string` — returns `system_type` as the display name

## Common Usage

```php
// Check for an active QuickBooks integration
$qbo = Integration::active()->where('system_type', 'qbo')->first();

// Get the implementation for sync operations
$impl = $qbo->getImplementation();

// Pause syncing temporarily
$qbo->update(['pause_syncing' => true]);

// Enforce single-active-per-type before connecting
$newIntegration = new Integration(['system_type' => 'qbo', ...]);
$newIntegration->failIfOtherActiveIntegration();
$newIntegration->save();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
