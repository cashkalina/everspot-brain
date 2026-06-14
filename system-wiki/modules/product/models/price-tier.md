---
model: PriceTier
module: Product
table: price_tiers
connection: tenant
primary_source: modules/Product/Models/PriceTier.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Product/Models/PriceTierPrice.php
traits:
  - SoftDeletes
related_models: [PriceTierPrice]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, financial]
---

# PriceTier

## Overview

`PriceTier` represents a named pricing level that can be applied to products and product types across the cemetery. Common examples include tiers such as "Retail," "Member," "Veteran," or "Pre-need" — each assigned a unique `code` and an optional `description`. Tiers are ordered by `sort_order` and toggled active/inactive via `is_active`.

The distinguishing feature of a price tier is the `per_cemetery_pricing` flag. When enabled, `PriceTierPrice` rows for this tier carry a `cemetery_id`, allowing different prices to be set for each cemetery location. When disabled, all `PriceTierPrice` rows for this tier are location-agnostic (cemetery-based override rows are never written). This flag drives the cascade logic in `Product::getPriceForTier()` and `ProductType::getPriceForTier()`.

`PriceTier` is a soft-deleted administrative/configuration model. Tiers are created by cemetery administrators and then referenced throughout order line and pricing resolution.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Display name of the tier |
| code | varchar | No | - | Unique machine code for the tier |
| description | text | Yes | - | Optional longer description |
| per_cemetery_pricing | tinyint | No | 0 | Whether prices for this tier are per-cemetery (cast to boolean) |
| is_active | tinyint | No | 1 | Whether the tier is active (cast to boolean) |
| sort_order | int | No | 0 | Display sort order (cast to integer) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `price_tiers_code_unique` on `code`

**Indexes:** `price_tiers_is_active_index` on `is_active`; `price_tiers_sort_order_index` on `sort_order`

**Foreign keys:** _None._

## Casts

- `per_cemetery_pricing` → `boolean`
- `is_active` → `boolean`
- `sort_order` → `integer`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — price tiers are soft-deleted, never hard-deleted

## Relationships

- `prices()` — has many [PriceTierPrice](./price-tier-price.md): all prices defined for this tier
- `productPrices()` — has many [PriceTierPrice](./price-tier-price.md) (where `product_id` is not null): product-specific prices for this tier
- `productTypePrices()` — has many [PriceTierPrice](./price-tier-price.md) (where `product_type_id` is not null): product-type-level prices for this tier

## Scopes

- `active(Builder $query)` — filters to tiers where `is_active = true`
- `ordered(Builder $query)` — orders by `sort_order` then `name`

## Events

_None._

## Observers

_None registered._

## Key Methods

- `hasCemeteryPricing(): bool` — returns `true` when `per_cemetery_pricing` is set; used by callers before attempting cemetery-specific price lookups
- `getPriceForProduct(int $productId, ?int $cemeteryId = null): ?int` — retrieves the raw `sale_price` (in cents) for a specific product under this tier; tries cemetery-specific row first (when `per_cemetery_pricing` is true and `$cemeteryId` is provided), then falls back to the base row (`cemetery_id = null`)
- `getPriceForProductType(int $productTypeId, ?int $cemeteryId = null): ?int` — same cascade as `getPriceForProduct()` but for a product type; returns the raw price in cents or `null` if not found

## Common Usage

```php
// Fetch all active tiers in display order
$tiers = PriceTier::active()->ordered()->get();

// Check if a tier has per-cemetery pricing
if ($tier->hasCemeteryPricing()) {
    $price = $tier->getPriceForProduct($product->id, $cemetery->id);
} else {
    $price = $tier->getPriceForProduct($product->id);
}

// Get all prices for a tier
$prices = $tier->prices()->with(['product', 'productType', 'cemetery'])->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
