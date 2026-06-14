---
model: PriceTierPrice
module: Product
table: price_tier_prices
connection: tenant
primary_source: modules/Product/Models/PriceTierPrice.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Product/Models/PriceTier.php
  - modules/Product/Models/Product.php
  - modules/Product/Models/ProductType.php
  - modules/Common/Models/Cemetery.php
traits:
  - HasMoneyFields
related_models: [Cemetery, PriceTier, Product, ProductType]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, financial]
---

# PriceTierPrice

## Overview

`PriceTierPrice` is the many-to-many join between a [PriceTier](./price-tier.md) and a product or product type, optionally scoped to a specific cemetery. Each row stores the `sale_price` (in cents) for a given tier/target/location combination. The `HasMoneyFields` trait transparently converts the stored integer cents to and from dollar floats for all public access.

Exactly one of `product_id` or `product_type_id` must be set per row — not both and not neither. This is enforced at the Eloquent level in the `booted()` hook. When `cemetery_id` is null the row is the "base" price for that tier/target; when set it is an override for a specific cemetery. The combination of `(price_tier_id, product_id, product_type_id, cemetery_id)` is database-unique.

This model has no soft-deletes: rows are hard-deleted when a tier, product, product type, or cemetery is removed (all foreign keys cascade on delete).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| price_tier_id | bigint | No | - | FK → price_tiers: the tier this price belongs to |
| product_id | bigint | Yes | - | FK → products: the product (mutually exclusive with product_type_id) |
| product_type_id | bigint | Yes | - | FK → product_types: the product type (mutually exclusive with product_id) |
| cemetery_id | bigint | Yes | - | FK → cemeteries: cemetery-specific override; null = base price |
| sale_price | int | No | - | Price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Unique indexes:** `unique_tier_price` on `(price_tier_id, product_id, product_type_id, cemetery_id)`

**Indexes:** `price_tier_prices_price_tier_id_index` on `price_tier_id`; `price_tier_prices_product_id_index` on `product_id`; `price_tier_prices_product_type_id_index` on `product_type_id`; `price_tier_prices_cemetery_id_index` on `cemetery_id`

**Foreign keys:** `price_tier_id` → `price_tiers.id` (cascade delete); `product_id` → `products.id` (cascade delete); `product_type_id` → `product_types.id` (cascade delete); `cemetery_id` → `cemeteries.id` (cascade delete)

## Casts

- `sale_price` → `integer` — raw cents storage; dollar-float access provided by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants:**
```php
const LOCATION_BASE = 'base';
```

## Accessors & Mutators

_None._ (Dollar-float conversion is handled transparently by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) for `sale_price`.)

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparently converts `sale_price` between stored integer cents and dollar floats; `$moneyAttributes = ['sale_price']`

## Relationships

- `priceTier()` — belongs to [PriceTier](./price-tier.md) (`price_tier_id`): the tier this price row belongs to
- `product()` — belongs to [Product](./product.md) (`product_id`): the product this price is for (null when type-level)
- `productType()` — belongs to [ProductType](./product-type.md) (`product_type_id`): the product type this price is for (null when product-level)
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery override; null = base price

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `isProductPrice(): bool` — returns `true` when `product_id` is set (product-specific row)
- `isProductTypePrice(): bool` — returns `true` when `product_type_id` is set (product-type-level row)
- `isCemeterySpecific(): bool` — returns `true` when `cemetery_id` is set (location override vs base price)

## Common Usage

```php
// Create a base price (no cemetery override) for a product under a tier
PriceTierPrice::create([
    'price_tier_id' => $tier->id,
    'product_id'    => $product->id,
    'sale_price'    => 25000,  // stored in cents; $250.00
]);

// Create a cemetery-specific price for a product type
PriceTierPrice::create([
    'price_tier_id'   => $tier->id,
    'product_type_id' => $productType->id,
    'cemetery_id'     => $cemetery->id,
    'sale_price'      => 22000,  // $220.00
]);

// Access via dollar float (HasMoneyFields)
$price = PriceTierPrice::first();
echo $price->sale_price; // 250.0  (dollars, not cents)

// Check what kind of price row it is
$price->isProductPrice();        // true  / false
$price->isProductTypePrice();    // true  / false
$price->isCemeterySpecific();    // true  / false
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
