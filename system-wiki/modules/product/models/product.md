---
model: Product
module: Product
table: products
connection: tenant
primary_source: modules/Product/Models/Product.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Product/Observers/ProductObserver.php
  - modules/Product/Providers/ProductServiceProvider.php
  - modules/Product/Models/ProductType.php
  - modules/Product/Models/ProductTaxRate.php
  - modules/Product/Models/PriceTierPrice.php
  - modules/Accounting/Models/GlAccount.php
  - modules/Commission/Models/CommissionCategory.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/DeliveryPreference.php
  - modules/Property/Models/PropertyGroup.php
  - modules/Recognition/Models/RecognitionRule.php
  - modules/Trust/Models/TrustingScheduleGroup.php
traits:
  - HasByUserFields
  - HasFactory
  - HasMoneyFields
  - HasSchemalessAttributes
  - HasSearch
  - SoftDeletes
related_models: [Cemetery, CommissionCategory, DeliveryPreference, GlAccount, PriceTierPrice, ProductTaxRate, ProductType, PropertyGroup, RecognitionRule, TrustingScheduleGroup]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, financial, core]
---

# Product

## Overview

`Product` is the leaf-level catalog item in Everspot's product hierarchy. Every sellable thing — a burial plot, an urn, a services package, a memorial inscription — is a `Product`. Products belong to a [ProductType](./product-type.md), which acts as a default-value parent: any pricing, GL account assignment, commission category, recognition rule, trusting schedule, or delivery preference not explicitly set on a product is inherited from its type at runtime via the `getDefaultableValue()` / `getPriceForTier()` / `getGlAccountByType()` cascade.

Pricing is stored in cents (integer) and converted to dollar floats via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields). Products can participate in tiered pricing via [PriceTierPrice](./price-tier-price.md) rows, and cemetery-specific tax rates via [ProductTaxRate](./product-tax-rate.md). The `config_data` JSON column holds arbitrary schemaless configuration via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes).

Products are associated with cemeteries via a many-to-many pivot (the `cemetery_product` table), which controls which cemeteries offer a given product. They link to [PropertyGroup](../../property/models/property-group.md) hierarchies for inventory items backed by physical property. The [HasSearch](../../../system/traits/index.md#hassearch) trait makes products full-text-searchable. Soft deletes are used — a `PreDeleteProduct` action runs inside a transaction via the observer before the record is removed.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| product_type_id | bigint | No | - | FK → product_types: the parent product type |
| commission_category_id | bigint | Yes | - | FK → commission_categories: override commission category (inherits from type if null) |
| trusting_schedule_group_id | bigint | Yes | - | FK → trusting_schedule_groups: override trust schedule (inherits from type if null) |
| delivery_preference_id | bigint | Yes | - | FK → delivery_preferences: override delivery preference (inherits from type if null) |
| name | varchar | No | - | Display name of the product |
| description | text | Yes | - | Optional longer description |
| sku | varchar | Yes | - | Stock-keeping unit code |
| sale_price | int | Yes | - | Sale price in cents; null = inherit from product type (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| cost_price | int | Yes | - | Cost price in cents; null = inherit from product type (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| trust_cost | int | Yes | - | Trust cost in cents; null = inherit from product type (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| config_data | json | Yes | - | Schemaless config (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| is_active | tinyint | No | 0 | Whether the product is active |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `product_type_id` → `product_types.id`; `commission_category_id` → `commission_categories.id`; `trusting_schedule_group_id` → `trusting_schedule_groups.id`; `delivery_preference_id` → `delivery_preferences.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `products_name_index` on `name`; `products_sku_index` on `sku`; `products_is_active_index` on `is_active`; FK-backing indexes on `product_type_id`, `commission_category_id`, `trusting_schedule_group_id`, `delivery_preference_id`, `created_by`, `updated_by`, `deleted_by`

## Casts

_None declared on the model._ Money columns (`sale_price`, `cost_price`, `trust_cost`) are accessed via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) dollar-float conversion, not via `$casts`.

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes (HasMoneyFields):** `$moneyAttributes = ['sale_price', 'cost_price', 'trust_cost', 'raw_sale_price', 'raw_cost_price', 'raw_trust_cost']`

## Accessors & Mutators

- `getSalePriceAttribute(): ?float` — product's `sale_price` falling back to `productType->sale_price` when null; returns dollars via `HasMoneyFields`
- `getCostPriceAttribute(): ?float` — product's `cost_price` falling back to `productType->cost_price` when null; returns dollars
- `getTrustCostAttribute(): ?float` — product's `trust_cost` falling back to `productType->trust_cost` when null; returns dollars
- `getRawSalePriceAttribute(): ?float` — product's own `sale_price` without type fallback (null if unset)
- `getRawCostPriceAttribute(): ?float` — product's own `cost_price` without type fallback
- `getRawTrustCostAttribute(): ?float` — product's own `trust_cost` without type fallback
- `getFullNameAttribute(): string` — `"<sku> - <name>"` concatenation

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `ProductFactory` via `newFactory()`)
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — cents-to-dollars conversion for `sale_price`, `cost_price`, `trust_cost` and their raw variants
- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — dot-notation access to the `config_data` JSON column
- [HasSearch](../../../system/traits/index.md#hassearch) — full-text search indexing
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — products are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `productType()` — belongs to [ProductType](./product-type.md) (`product_type_id`): the parent product type that provides default values
- `commissionCategoryRelation()` — belongs to [CommissionCategory](../../commission/models/commission-category.md) (`commission_category_id`): product-specific commission category override
- `trustingScheduleGroupRelation()` — belongs to [TrustingScheduleGroup](../../trust/models/trusting-schedule-group.md) (`trusting_schedule_group_id`): product-specific trust schedule group override
- `deliveryPreferenceRelation()` — belongs to [DeliveryPreference](../../common/models/delivery-preference.md) (`delivery_preference_id`): product-specific delivery preference override
- `cemeteries()` — belongs-to-many [Cemetery](../../common/models/cemetery.md) via `cemetery_product`: cemeteries that offer this product
- `glAccounts()` — morph-to-many [GlAccount](../../accounting/models/gl-account.md) via `accountable` (pivot `type`): GL accounts assigned to this product by account type
- `recognitionRules()` — morph-to-many [RecognitionRule](../../recognition/models/recognition-rule.md) via `recognition_rulable` (pivot `type`): revenue/expense/commission/tax recognition rules
- `propertyGroups()` — has many [PropertyGroup](../../property/models/property-group.md): property groups whose inventory is backed by this product
- `taxRates()` — has many [ProductTaxRate](./product-tax-rate.md): per-cemetery tax rate overrides for this product
- `tierPrices()` — has many [PriceTierPrice](./price-tier-price.md): tier-specific price rows for this product

## Scopes

- `active($query): Builder` — filters to `is_active = true`
- `forCemetery($query, $cemeteryId): Builder` — filters to active products associated with the given cemetery (via `cemeteries` relationship)

## Events

_None._

## Observers

- `ProductObserver` — registered in `ProductServiceProvider::registerObservers()` (`Product::observe(ProductObserver::class)`). Handles:
  - `created` — fires `analytics()->track('Product Created')`
  - `deleting` — wraps deletion in a DB transaction running `PreDeleteProduct` action
  - `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs

## Key Methods

- `commissionCategory(bool $withDefault = true)` — returns the product's own [CommissionCategory](../../commission/models/commission-category.md) or falls back to the product type's when `$withDefault` is true
- `trustingScheduleGroup(bool $withDefault = true)` — returns the product's own [TrustingScheduleGroup](../../trust/models/trusting-schedule-group.md) or falls back to the product type's
- `deliveryPreference(bool $withDefault = true)` — returns the product's own [DeliveryPreference](../../common/models/delivery-preference.md) or falls back to the product type's
- `incomeAccount(bool $withDefault = true): ?GlAccount` — returns the `income`-type GL account, falling back to product type
- `cogsAccount(bool $withDefault = true): ?GlAccount` — returns the `cogs`-type GL account, falling back to product type
- `commissionExpenseAccount(bool $withDefault = true): ?GlAccount` — returns the `commission_expense`-type GL account, falling back to product type
- `assetAccount(bool $withDefault = true): ?GlAccount` — returns the `asset`-type GL account, falling back to product type
- `deferredRevenueAccount(bool $withDefault = true): ?GlAccount` — returns the `deferred_revenue`-type GL account, falling back to product type
- `deferredExpenseAccount(bool $withDefault = true): ?GlAccount` — `deferred_expense` GL account with type fallback
- `deferredCommissionAccount(bool $withDefault = true): ?GlAccount` — `deferred_commission` GL account with type fallback
- `deferredTaxAccount(bool $withDefault = true): ?GlAccount` — `deferred_tax` GL account with type fallback
- `getGlAccountByType($type, bool $withDefault = true): ?GlAccount` — core GL lookup by pivot `type`; falls back to product type
- `getDeferralAccountByRecType($type): ?GlAccount` — maps recognition type string (`revenue`, `expense`, `commission`, `tax`) to the appropriate deferred GL account
- `getRecognitionAccountByRecType($type): ?GlAccount` — maps recognition type string to the appropriate recognition (income/cogs/commission) GL account
- `revRecRule(bool $withDefault = true): ?RecognitionRule` — revenue recognition rule with type fallback
- `expRecRule(bool $withDefault = true): ?RecognitionRule` — expense recognition rule with type fallback
- `commRecRule(bool $withDefault = true): ?RecognitionRule` — commission recognition rule with type fallback
- `taxRecRule(bool $withDefault = true): ?RecognitionRule` — tax recognition rule with type fallback
- `getRecognitionRuleByType($type, bool $withDefault = true): ?RecognitionRule` — core recognition-rule lookup by pivot `type`; falls back to product type
- `properties(): Builder` — returns a query builder for all [Property](../../property/models/property.md) rows under any of this product's property groups (recursively through child groups)
- `availableProperties(): Builder` — narrows `properties()` to available-only
- `getDefaultableValue($field): mixed` — returns `$this->$field ?? $this->productType?->$field`; the generic product→type fallback
- `getAllPropertyGroupIds(): array` — recursively collects all property group IDs under this product (depth-first, unique)
- `getProductPropertyValue($propertyId, $propertyField, $productField = null): mixed` — resolves a display/config value for a specific property by walking property → property group → parent groups → product default
- `getProductPropertyGroupValue($propertyGroupId, $propertyGroupField, $productField = null): mixed` — same cascade but starting from a property group
- `getTaxRateForCemetery(int $cemeteryId): float` — returns the applicable tax rate for a cemetery; checks product-specific tax rates first, then falls back to product type; returns 0.0 if none found
- `getPriceForTier(int $tierId, ?int $cemeteryId = null): ?float` — full pricing cascade: product tier (cemetery) → product tier (base) → product type tier (cemetery) → product type tier (base) → product sale_price → product type sale_price; returns dollars or null
- `getModelIdentifier(): ?string` — returns `sku` if set, otherwise `id`; used in admin/reporting display
- `getModelInferredName(): ?string` — returns `name`

## Common Usage

```php
// Create a product under a type
$product = Product::create([
    'product_type_id' => $type->id,
    'name'            => 'Companion Niche',
    'sku'             => 'NI-COMP-001',
    'sale_price'      => 350000,  // $3,500.00 in cents
    'is_active'       => true,
]);

// Price accessor with type fallback (returns dollars)
echo $product->sale_price;      // 3500.0
echo $product->raw_sale_price;  // 3500.0 if set on product; null otherwise

// Get price for a tier with cemetery override
$price = $product->getPriceForTier($tier->id, $cemetery->id);

// GL account resolution with product-type fallback
$income = $product->incomeAccount();

// Tax rate for a cemetery
$rate = $product->getTaxRateForCemetery($cemetery->id); // 0.075

// Filter products offered by a cemetery
$available = Product::forCemetery($cemetery->id)->get();

// All properties backed by this product
$props = $product->availableProperties()->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
