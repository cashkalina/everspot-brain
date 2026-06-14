---
title: Product Module
module: Product
last_updated: 2026-06-14
---

# Product Module

The Product module (`modules/Product/`) manages Everspot's product catalog: the types, items, pricing tiers, tier prices, and per-cemetery tax rates that drive order line valuation, GL posting, recognition, trust, and commission calculations.

## Directory Contents

| Path | Contents |
|------|----------|
| [models/](./models/index.md) | All 5 documented Eloquent models |

## Module Architecture

### Two-Level Hierarchy

Products are organised in two levels:

- **[ProductType](./models/product-type.md)** — the category/template. Sets default prices, GL accounts, commission categories, recognition rules, trust schedule groups, and delivery preferences.
- **[Product](./models/product.md)** — the individual SKU. Can override any default from its parent type; if a field is null on the product, the value is inherited from the type at runtime.

### Pricing

All money columns store integer **cents**; `HasMoneyFields` converts to/from dollar floats. Three pricing layers interact at runtime:

1. **Standard price** — `sale_price` on the product (or type as fallback).
2. **Tier prices** — [PriceTierPrice](./models/price-tier-price.md) rows keyed by `(price_tier_id, product_id | product_type_id, cemetery_id?)`. Resolved by `Product::getPriceForTier()` and `ProductType::getPriceForTier()` in a six-step cascade.
3. **Tax rates** — [ProductTaxRate](./models/product-tax-rate.md) rows keyed by `(product_id | product_type_id, cemetery_id)`. Resolved by `getTaxRateForCemetery()` with product-then-type fallback.

### GL Accounts & Rules

Both `ProductType` and `Product` participate in polymorphic `accountable` and `recognition_rulable` pivot relationships with `GlAccount` and `RecognitionRule`. Products fall back to their type's assignments when their own pivot rows are absent.

## Key Source Paths

| File | Purpose |
|------|---------|
| `modules/Product/Models/Product.php` | Leaf product model |
| `modules/Product/Models/ProductType.php` | Product type / template model |
| `modules/Product/Models/PriceTier.php` | Pricing tier configuration |
| `modules/Product/Models/PriceTierPrice.php` | Tier × product/type × cemetery price rows |
| `modules/Product/Models/ProductTaxRate.php` | Per-cemetery tax rates |
| `modules/Product/Providers/ProductServiceProvider.php` | Registers `ProductObserver` and `ProductTypeObserver` |
| `modules/Product/Observers/ProductObserver.php` | Analytics tracking + pre-delete action |
| `modules/Product/Observers/ProductTypeObserver.php` | Analytics tracking + pre-delete action |
