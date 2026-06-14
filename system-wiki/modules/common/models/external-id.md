---
model: ExternalId
module: Common
table: external_ids
connection: tenant
primary_source: modules/Common/Models/ExternalId.php
source_paths:
  - app/Models/BaseModel.php
traits: []
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [integration]
---

# ExternalId

## Overview

The ExternalId model provides a generic polymorphic store for mapping Everspot records to identifiers in external systems. Any model can have one or more ExternalId rows — each row names the external `system` (e.g. `'quickbooks'`) and stores the corresponding `external_id` string. The companion [HasExternalIds](../../../system/traits/index.md#hasexternalids) trait exposes convenience methods (`addExternalId()`, `getExternalId()`, `hasExternalId()`) on models that opt in.

The model is used directly as a lookup table: given a system name and an external ID, `findModelByExternalId()` resolves the Everspot record. The `scopeForSystem()` scope narrows queries to a specific system.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_type | varchar | No | - | Morph type — the Everspot model class |
| model_id | bigint | No | - | Morph ID — the Everspot record's primary key |
| system | varchar | No | - | External system name (e.g. `quickbooks`) |
| external_id | varchar | No | - | ID of the record in the external system |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** None (polymorphic — no enforced FK constraint)

**Indexes:** Composite index on (`model_type`, `model_id`) implied by morph conventions.

## Casts

_None._

## Attributes

**Fillable:** `['model_type', 'model_id', 'system', 'external_id']`

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `model()` — morphTo: the Everspot record this external ID belongs to (any model using [HasExternalIds](../../../system/traits/index.md#hasexternalids))

## Scopes

- `forSystem(Builder $query, string $system): Builder` — filters to a specific external system name

## Events

_None._

## Observers

_None registered._

## Key Methods

- `findModelByExternalId(string $system, string $externalId): ?object` *(static)* — looks up an `ExternalId` row by system and external ID, then resolves and returns the associated Everspot model (or `null` if not found)

## Common Usage

```php
// Store an external ID for a customer
ExternalId::create([
    'model_type'  => Customer::class,
    'model_id'    => $customer->id,
    'system'      => 'quickbooks',
    'external_id' => 'QB-10042',
]);

// Look up an Everspot model from an external ID
$model = ExternalId::findModelByExternalId('quickbooks', 'QB-10042');

// Query all external IDs for QuickBooks
$qbIds = ExternalId::forSystem('quickbooks')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
