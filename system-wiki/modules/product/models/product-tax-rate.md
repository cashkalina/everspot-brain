---
model: ProductTaxRate
module: Product
table: product_tax_rates
connection: tenant
primary_source: modules/Product/Models/ProductTaxRate.php
source_paths:
  - modules/Product/Models/Product.php
  - modules/Product/Models/ProductType.php
  - modules/Common/Models/Cemetery.php
traits: []
related_models: [Cemetery, Product, ProductType]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [inventory, financial]
---

# ProductTaxRate

## Overview

`ProductTaxRate` stores the tax rate that applies to a product or product type when sold in a specific cemetery. The `tax_rate` column holds the rate as a decimal fraction (e.g. `0.075` for 7.5%). A virtual accessor/mutator pair (`tax_rate_percentage`) converts between the stored fraction and a human-readable percentage for display and input.

Each row targets exactly one of `product_id` or `product_type_id` — not both and not neither. This is enforced by the model's `boot()` hook. The unique constraints (`product_cemetery_unique` and `product_type_cemetery_unique`) ensure there is at most one rate per product/type × cemetery combination.

Resolution is hierarchical: `Product::getTaxRateForCemetery()` checks for a product-level row first, then falls back to the product type's row, then to `0.0`. All three foreign keys cascade on delete, so removing a cemetery, product, or product type automatically cleans up its tax rate rows.

`ProductTaxRate` extends `Illuminate\Database\Eloquent\Model` directly (not `BaseModel`), so it does not carry audit stamps, soft deletes, or the other traits `BaseModel` provides.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| product_id | bigint | Yes | - | FK → products (mutually exclusive with product_type_id) |
| product_type_id | bigint | Yes | - | FK → product_types (mutually exclusive with product_id) |
| cemetery_id | bigint | No | - | FK → cemeteries: cemetery this rate applies to |
| tax_rate | decimal | No | 0.000000 | Tax rate as a decimal fraction (e.g. 0.075 = 7.5%) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Unique indexes:** `product_cemetery_unique` on `(product_id, cemetery_id)`; `product_type_cemetery_unique` on `(product_type_id, cemetery_id)`

**Foreign keys:** `product_id` → `products.id` (cascade delete); `product_type_id` → `product_types.id` (cascade delete); `cemetery_id` → `cemeteries.id` (cascade delete)

## Casts

- `tax_rate` → `float`

## Attributes

**Fillable:** `['product_id', 'product_type_id', 'cemetery_id', 'tax_rate']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getTaxRatePercentageAttribute(): float` — **accessor**: returns `tax_rate * 100` (e.g. `0.075` → `7.5`)
- `setTaxRatePercentageAttribute(float $value): void` — **mutator**: stores `$value / 100` into `tax_rate` (e.g. `7.5` → `0.075`)

## Traits

_None._

## Relationships

- `product()` — belongs to [Product](./product.md) (`product_id`): the product this tax rate applies to (null when type-level)
- `productType()` — belongs to [ProductType](./product-type.md) (`product_type_id`): the product type this tax rate applies to (null when product-level)
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery where this rate applies

## Scopes

- `forProduct($query, int $productId)` — filters to rows for a specific product
- `forProductType($query, int $productTypeId)` — filters to rows for a specific product type
- `forCemetery($query, int $cemeteryId)` — filters to rows for a specific cemetery

## Events

- `saving` — boot hook validates mutual exclusivity: exactly one of `product_id` or `product_type_id` must be set; throws `\InvalidArgumentException` on violation

## Observers

_None registered._

## Key Methods

_None beyond accessors, scopes, and the standard Eloquent interface._

## Common Usage

```php
// Create a product-level tax rate for a cemetery
ProductTaxRate::create([
    'product_id'  => $product->id,
    'cemetery_id' => $cemetery->id,
    'tax_rate'    => 0.075,  // 7.5%
]);

// Create a product-type-level rate using the percentage mutator
$taxRate = new ProductTaxRate([
    'product_type_id' => $productType->id,
    'cemetery_id'     => $cemetery->id,
]);
$taxRate->tax_rate_percentage = 8.25;  // stores 0.0825
$taxRate->save();

// Read back as percentage
echo $taxRate->tax_rate_percentage; // 8.25

// Resolve the applicable rate for a product in a cemetery
$rate = $product->getTaxRateForCemetery($cemetery->id);

// Query all rates for a specific cemetery
$rates = ProductTaxRate::forCemetery($cemetery->id)->with(['product', 'productType'])->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
