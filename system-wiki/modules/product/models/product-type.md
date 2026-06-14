---
model: ProductType
module: Product
table: product_types
connection: tenant
primary_source: modules/Product/Models/ProductType.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Product/Observers/ProductTypeObserver.php
  - modules/Product/Providers/ProductServiceProvider.php
  - modules/Product/Models/ProductTaxRate.php
  - modules/Product/Models/PriceTierPrice.php
  - modules/Accounting/Models/GlAccount.php
  - modules/Commission/Models/CommissionCategory.php
  - modules/Common/Models/DeliveryPreference.php
  - modules/Recognition/Models/RecognitionRule.php
  - modules/Trust/Models/TrustingScheduleGroup.php
traits:
  - HasByUserFields
  - HasFactory
  - HasMoneyFields
  - SoftDeletes
related_models: [CommissionCategory, DeliveryPreference, GlAccount, PriceTierPrice, ProductTaxRate, RecognitionRule, TrustingScheduleGroup]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, financial]
---

# ProductType

## Overview

`ProductType` is the parent-level grouping in Everspot's product catalog hierarchy. It sits above individual [Product](./product.md) records and acts as the default template: any pricing, GL account assignment, commission category, recognition rule, trusting schedule group, or delivery preference set on the type is inherited by all its products when those products do not have their own override value.

Pricing columns (`sale_price`, `cost_price`, `trust_cost`) are stored as integer cents and accessed as dollar floats via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields). The `config_data` JSON column holds additional schemaless configuration. Unlike [Product](./product.md), `ProductType` does not use [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — the `config_data` column is stored but accessed raw.

The type is also the second-level fallback in tiered pricing: `ProductType::getPriceForTier()` implements the cemetery → base → standard-price cascade for the type itself, and this is called from `Product::getPriceForTier()` when the product has no explicit tier price.

Soft deletes are used. `ProductTypeObserver` runs a `PreDeleteProductType` action in a transaction on the `deleting` event.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| commission_category_id | bigint | Yes | - | FK → commission_categories: default commission category for products of this type |
| trusting_schedule_group_id | bigint | Yes | - | FK → trusting_schedule_groups: default trust schedule for products of this type |
| delivery_preference_id | bigint | Yes | - | FK → delivery_preferences: default delivery preference for products of this type |
| name | varchar | No | - | Display name of the product type |
| sale_price | int | No | - | Default sale price in cents for products of this type (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| cost_price | int | No | - | Default cost price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| trust_cost | int | No | - | Default trust cost in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| config_data | json | Yes | - | Additional schemaless configuration |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `commission_category_id` → `commission_categories.id`; `trusting_schedule_group_id` → `trusting_schedule_groups.id`; `delivery_preference_id` → `delivery_preferences.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `product_types_name_index` on `name`; FK-backing indexes on `commission_category_id`, `trusting_schedule_group_id`, `delivery_preference_id`, `created_by`, `updated_by`, `deleted_by`

## Casts

_None declared on the model._ Money columns (`sale_price`, `cost_price`, `trust_cost`) are handled by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes (HasMoneyFields):** `$moneyAttributes = ['sale_price', 'cost_price', 'trust_cost']`

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `ProductTypeFactory` via `newFactory()`)
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — cents-to-dollars conversion for `sale_price`, `cost_price`, `trust_cost`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — product types are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `commissionCategory()` — belongs to [CommissionCategory](../../commission/models/commission-category.md) (`commission_category_id`): default commission category
- `trustingScheduleGroup()` — belongs to [TrustingScheduleGroup](../../trust/models/trusting-schedule-group.md) (`trusting_schedule_group_id`): default trust schedule group
- `deliveryPreference()` — belongs to [DeliveryPreference](../../common/models/delivery-preference.md) (`delivery_preference_id`): default delivery preference
- `glAccounts()` — morph-to-many [GlAccount](../../accounting/models/gl-account.md) via `accountable` (pivot `type`): GL accounts assigned to this type by account type
- `recognitionRules()` — morph-to-many [RecognitionRule](../../recognition/models/recognition-rule.md) via `recognition_rulable` (pivot `type`): revenue/expense/commission/tax recognition rules
- `taxRates()` — has many [ProductTaxRate](./product-tax-rate.md): per-cemetery tax rate defaults for this product type
- `tierPrices()` — has many [PriceTierPrice](./price-tier-price.md): tier-specific price rows for this product type

## Scopes

_None._

## Events

_None._

## Observers

- `ProductTypeObserver` — registered in `ProductServiceProvider::registerObservers()` (`ProductType::observe(ProductTypeObserver::class)`). Handles:
  - `created` — fires `analytics()->track('Product Type Created')`
  - `deleting` — wraps deletion in a DB transaction running `PreDeleteProductType` action
  - `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs

## Key Methods

- `incomeAccount(): ?GlAccount` — returns the `income`-type GL account for this product type
- `cogsAccount(): ?GlAccount` — returns the `cogs`-type GL account
- `commissionExpenseAccount(): ?GlAccount` — returns the `commission_expense`-type GL account
- `assetAccount(): ?GlAccount` — returns the `asset`-type GL account
- `deferredRevenueAccount(): ?GlAccount` — returns the `deferred_revenue`-type GL account
- `deferredExpenseAccount(): ?GlAccount` — returns the `deferred_expense`-type GL account
- `deferredCommissionAccount(): ?GlAccount` — returns the `deferred_commission`-type GL account
- `deferredTaxAccount(): ?GlAccount` — returns the `deferred_tax`-type GL account
- `getGlAccountByType($type): ?GlAccount` — core GL account lookup by pivot `type` (no fallback — types are the leaf of the GL inheritance chain)
- `revRecRule(): ?RecognitionRule` — revenue recognition rule for this type
- `expRecRule(): ?RecognitionRule` — expense recognition rule for this type
- `commRecRule(): ?RecognitionRule` — commission recognition rule for this type
- `taxRecRule(): ?RecognitionRule` — tax recognition rule for this type
- `getRecognitionRuleByType($type): ?RecognitionRule` — core recognition-rule lookup by pivot `type`
- `getTaxRateForCemetery(int $cemeteryId): float` — returns the tax rate for the given cemetery from `taxRates`; returns `0.0` if none found
- `getPriceForTier(int $tierId, ?int $cemeteryId = null): ?float` — tier price cascade at the type level: cemetery-specific tier row → base tier row → standard `sale_price`; returns dollars or null if tier not found

## Common Usage

```php
// Create a product type
$type = ProductType::create([
    'name'       => 'Burial Vaults',
    'sale_price' => 180000,  // $1,800.00 in cents
    'cost_price' => 90000,   // $900.00
    'trust_cost' => 27000,   // $270.00
]);

// Assign a GL account
$type->glAccounts()->attach($incomeAccount->id, ['type' => 'income']);

// Get the income GL account
$gl = $type->incomeAccount();

// Tier pricing cascade for a type
$price = $type->getPriceForTier($tier->id, $cemetery->id);

// Tax rate for a cemetery
$rate = $type->getTaxRateForCemetery($cemetery->id); // e.g. 0.075

// Fetch all product types (including soft-deleted)
$all = ProductType::withTrashed()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
