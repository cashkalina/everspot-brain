---
model: Token
module: Common
table: tokens
connection: tenant
primary_source: modules/Common/Models/Token.php
source_paths:
  - app/Models/BaseModel.php
traits:
  - HasSchemalessAttributes
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [integration, admin]
---

# Token

## Overview

The Token model stores OAuth or API tokens for external integrations via a polymorphic `tokenable` relationship. It is primarily used by [Integration](./integration.md), which has a `morphOne(Token::class, 'tokenable')` relationship. The `token` column holds the raw token value and is hidden from serialization. Additional configuration for the token is stored in `config_data` via `HasSchemalessAttributes`.

The model is soft-deleted (column present in schema) and inherits BaseModel behavior. No observers or observers are registered for it.

Note: The schema shows a `deleted_at` column on `tokens` based on the snapshot.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| tokenable_type | varchar | No | - | Morph type — the owning model class |
| tokenable_id | bigint | No | - | Morph ID — the owning model's primary key |
| token | text | No | - | The raw token value (hidden in serialization) |
| config_data | json | Yes | - | Token-specific configuration (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp |

**Primary key:** `id`

**Foreign keys:** None (polymorphic — no enforced FK constraint)

**Indexes:** Composite index on (`tokenable_type`, `tokenable_id`).

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['tokenable_type', 'tokenable_id', 'token', 'config_data']`

**Hidden:** `['token']` — the raw token value is excluded from array/JSON serialization

## Accessors & Mutators

_None._

## Traits

- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` JSON with dot-notation access for token-specific configuration

## Relationships

- `tokenable()` — morphTo: the model this token belongs to (typically an [Integration](./integration.md))

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getModelTitleSuffix(): ?string` — returns the owning model's full title (without suffix) for display in admin UI contexts

## Common Usage

```php
// Get the token for an integration
$token = $integration->token;
$rawToken = $token->token;   // the raw value

// Store additional configuration
$token->config_data['refresh_token'] = $refreshToken;
$token->save();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
