---
model: Cemetery
module: Common
table: cemeteries
connection: tenant
primary_source: modules/Common/Models/Cemetery.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/CemeteryObserver.php
  - modules/Common/Models/State.php
  - modules/Common/Database/Factories/CemeteryFactory.php
  - modules/Interment/Models/Interment.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Mapping/Models/Map.php
  - modules/Order/Models/Order.php
  - modules/Product/Models/Product.php
traits:
  - HasFactory
  - HasSchemalessAttributes
  - HasSearch
  - HasSettings
  - HasSyncables
  - SoftDeletes
related_models: [Interment, LiabilityLine, Map, Order, Product, State]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin, location]
---

# Cemetery

## Overview

The Cemetery model represents a physical cemetery location within the Everspot system. It is one of the foundational entities — users are assigned to a cemetery, orders and interments are associated with a cemetery, and many system settings are scoped at the cemetery level.

Each cemetery record holds its name (including optional legal and short names), address, contact details, and two JSON columns: `attribute_data` (EAV-style custom attributes, contributed by `HasSchemalessAttributes`) and `config_data` (key-value configuration, also via `HasSchemalessAttributes` and used by `HasSettings`). Several GL account accessors proxy through the `setting()` helper to expose cemetery-level accounting configuration.

The model carries soft deletes, supports search indexing, external-integration sync linkage, and a model factory. Lifecycle events are handled by `CemeteryObserver` registered in `CommonServiceProvider`. The `booted()` hook also fires a direct analytics track on creation.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Cemetery display name |
| legal_name | varchar | Yes | - | Official legal name |
| short_name | varchar | Yes | - | Abbreviated name |
| address_line_one | varchar | No | - | Street address line 1 |
| address_line_two | varchar | Yes | - | Street address line 2 |
| city | varchar | No | - | City |
| state_id | bigint | Yes | - | FK → states |
| zip_code | varchar | No | - | ZIP / postal code |
| contact_phone | varchar | Yes | - | Contact phone number |
| contact_email | varchar | Yes | - | Contact email address |
| website | varchar | Yes | - | Website URL |
| attribute_data | json | No | - | EAV custom attribute data (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| config_data | json | Yes | - | Key-value config store (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) / [HasSettings](../../../system/traits/index.md#hassettings) — see trait docs) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `state_id` → `states.id`

**Indexes:** FK-backing index on `state_id`.

## Casts

_None declared on the model._

<!-- HasSchemalessAttributes contributes casting for config_data/attribute_data — see trait doc. Trait-contributed casts are omitted here. -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

**Disabled report columns:** `config_data`, `attribute_data`, `deleted_at` (excluded from model reports)

## Accessors & Mutators

The following accessors proxy `setting()` to retrieve cemetery-level GL account settings:

- `getArAccountAttribute(): ?GlAccount` — AR account setting
- `getCommissionsPayableAccountAttribute(): ?GlAccount` — commissions payable account setting
- `getCashAccountAttribute(): ?GlAccount` — cash account setting
- `getUndepositedFundsAccountAttribute(): ?GlAccount` — undeposited funds account setting
- `getChargeIncomeAccountAttribute(): ?GlAccount` — charge income account setting
- `getCreditExpenseAccountAttribute(): ?GlAccount` — credit expense account setting
- `getInterestIncomeAccountAttribute(): ?GlAccount` — interest income account setting
- `getRefundsPayableAccountAttribute(): ?GlAccount` — refunds payable account setting
- `getTaxPayableAccountAttribute(): ?GlAccount` — tax payable account setting
- `getCancellationIncomeAccountAttribute(): ?GlAccount` — cancellation income account setting
- `getProcessingFeeIncomeAccountAttribute(): ?GlAccount` — processing fee income account setting

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `CemeteryFactory` via `newFactory()`)
- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` / `attribute_data` JSON columns with dot-notation access
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing for cemetery records
- [HasSettings](../../../system/traits/index.md#hassettings) — key-value settings store via the polymorphic `Setting` model; enables `setting()` helper scoped to this cemetery
- [HasSyncables](../../../system/traits/index.md#hassyncables) — links cemetery to external-integration records
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — cemeteries are soft-deleted, never hard-deleted

## Relationships

- `products()` — belongs-to-many [Product](../../product/models/product.md) (via `cemetery_product`): products available at this cemetery
- `orders()` — has many [Order](../../order/models/order.md): orders placed against this cemetery
- `interments()` — has many [Interment](../../interment/models/interment.md): interments at this cemetery
- `liabilityLines()` — has many [LiabilityLine](../../liability/models/liability-line.md): liability lines for this cemetery
- `state()` — belongs to [State](./state.md) (`state_id`): state/province
- `maps()` — has many [Map](../../mapping/models/map.md): cemetery maps

## Scopes

_None._

## Events

- `booted()` — on `created`: fires `analytics()->track('Cemetery Created')`

## Observers

- `CemeteryObserver` — registered in `CommonServiceProvider::registerObservers()` (`Cemetery::observe(CemeteryObserver::class)`). Handles:
  - `created` — post-creation side effects
  - `deleted`, `restored`, `forceDeleted` — cleanup hooks

## Key Methods

- `getModelTitle(): ?string` — returns the cemetery's inferred display name
- `getModelFullTitle(): ?string` — returns the full display name (delegates to `getModelTitle()`)

## Common Usage

```php
// Get all active cemeteries
$cemeteries = Cemetery::all();

// Access GL account settings
$arAccount = $cemetery->ar_account;

// Cemetery-scoped setting
$timezone = setting('timezone', $cemetery);

// Associated orders
$orders = $cemetery->orders()->recent()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
