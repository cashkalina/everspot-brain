---
title: Product Module — Model Index
module: Product
last_updated: 2026-06-14
---

# Product Module — Models

This directory contains documentation for all concrete Eloquent models in the `modules/Product` module.

## Models

| Model | Table | Description |
|-------|-------|-------------|
| [PriceTier](./price-tier.md) | `price_tiers` | Named pricing levels (e.g. Retail, Member, Veteran); controls whether per-cemetery pricing is active |
| [PriceTierPrice](./price-tier-price.md) | `price_tier_prices` | Per-tier prices for a product or product type, optionally scoped to a cemetery |
| [Product](./product.md) | `products` | Leaf-level catalog items; inherits defaults from ProductType |
| [ProductTaxRate](./product-tax-rate.md) | `product_tax_rates` | Per-cemetery tax rates for a product or product type |
| [ProductType](./product-type.md) | `product_types` | Parent-level product groupings; provides default pricing, GL accounts, and rules for Products |

## Module Overview

The Product module defines Everspot's two-level product catalog. **ProductType** acts as the template (default prices, GL accounts, commission categories, recognition rules, trust schedule groups, delivery preferences). **Product** is the leaf-level item that inherits from its type and can override any attribute.

Pricing is stored in integer cents and surfaced as dollar floats via `HasMoneyFields`. Tiered pricing is managed through **PriceTier** + **PriceTierPrice**, with a multi-level cascade (product → product type; cemetery-specific → base). Per-cemetery **ProductTaxRate** rows provide tax rates, also with a product → product type fallback.

See [modules/product/index.md](../index.md) for module-level context.
