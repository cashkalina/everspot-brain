---
model: OrderLine
module: Order
table: order_lines
connection: tenant
primary_source: modules/Order/Models/OrderLine.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Order/Observers/OrderLineObserver.php
  - modules/Order/Providers/OrderServiceProvider.php
  - modules/Common/Models/DeliveryPreference.php
  - modules/Common/Models/OwnerFile.php
  - modules/Customer/Models/Customer.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Order/Models/Order.php
  - modules/Product/Models/Product.php
  - modules/Property/Models/Property.php
  - modules/Property/Models/PropertyGroup.php
traits:
  - HasByUserFields
  - HasFactory
  - HasMoneyFields
  - HasSchemalessAttributes
related_models: [Customer, DeliveryPreference, LiabilityLine, Order, OwnerFile, Product, Property, PropertyGroup]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract]
---

# OrderLine

## Overview

The OrderLine model represents a single line item on an [Order](./order.md). Each line item records what was purchased (via a polymorphic `purchasable` relationship that may point to a `Product`, property, or other purchasable entity), the pricing breakdown, and optional assignment to a specific customer.

Line items generate [LiabilityLine](../../liability/models/liability-line.md) records that track the fulfillment lifecycle — each liability line can be marked as delivered, cancelled, or pending. The `availableLiabilityLines()`, `deliveredLiabilityLines()`, and `canceledLiabilityLines()` helpers segment these for UI and reporting.

Money columns (`unit_price`, `tax_total`, `total`, `unit_tax`, `unit_discount`, `sub_total`, `discount_total`) are stored as integer cents and transparently converted to dollars by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields). Extended configuration (e.g. delivery preference selections) is stored in the `config_data` JSON column via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes), accessed via dot notation.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| order_id | bigint | No | - | FK → orders: the parent order |
| assigned_customer_id | bigint | Yes | - | FK → customers: optional customer assigned to this line |
| property_id | bigint | Yes | - | FK → properties: the property sold on this line (if any) |
| property_group_id | bigint | Yes | - | FK → property_groups: the property group sold on this line (if any) |
| purchasable_type | varchar | No | - | Morph type for the purchasable polymorphic relationship |
| purchasable_id | bigint | No | - | Morph ID for the purchasable polymorphic relationship |
| name | text | No | - | Line item name (snapshotted at time of order) |
| description | text | Yes | - | Line item description |
| sku | varchar | No | - | Product SKU (snapshotted at time of order) |
| unit_price | int | No | 0 | Unit price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| unit_tax | int | No | 0 | Per-unit tax in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| unit_discount | int | No | 0 | Per-unit discount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| quantity | smallint | No | - | Number of units |
| sub_total | int | No | 0 | Line subtotal in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| discount_total | int | No | 0 | Total discounts for this line in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| tax_total | int | No | 0 | Total taxes for this line in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| total | int | No | 0 | Line grand total in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| notes | text | Yes | - | Free-text notes for this line |
| config_data | json | Yes | - | Extended configuration (delivery preferences, etc.) via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `order_id` → `orders.id`; `assigned_customer_id` → `customers.id`; `property_id` → `properties.id`; `property_group_id` → `property_groups.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `order_id`, `property_id`, `sku`, `total`; composite index on (`purchasable_type`, `purchasable_id`); FK-backing indexes on `assigned_customer_id`, `property_group_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

_None declared on the model._ (Money cent-to-dollar conversion is handled by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields); `config_data` schemaless access is handled by [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes).)

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Static config:**
```php
public $moneyAttributes = ['unit_price', 'tax_total', 'total', 'unit_tax', 'unit_discount', 'sub_total', 'discount_total'];

protected static $disabledReportColumns = ['config_data'];
```

## Accessors & Mutators

- `getDeliveryPreferenceAttribute(): ?DeliveryPreference` — looks up the `DeliveryPreference` record referenced by `config_data['delivery_preference_id']`; null if not set
- `getAvailableLiabQtyAttribute(): int` — count of liability lines that are not delivered and not cancelled
- `getDeliveredLiabQtyAttribute(): int` — count of delivered liability lines
- `getCanceledLiabQtyAttribute(): int` — count of cancelled liability lines
- `getDeliveryPreferenceDateAttribute(): ?string` — reads `config_data->delivery_preference_date` via dot notation

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `OrderLineFactory`)
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for all money columns
- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` JSON column with dot-notation access for extended line-item configuration

## Relationships

- `order()` — belongs to [Order](./order.md): the parent order
- `assignedCustomer()` — belongs to [Customer](../../customer/models/customer.md) (`assigned_customer_id`): the customer this line item is assigned to (optional)
- `purchasable()` — morphTo: the purchasable entity (commonly a [Product](../../product/models/product.md), resolved via `purchasable_type` / `purchasable_id`)
- `product()` — belongs to [Product](../../product/models/product.md) (`purchasable_id`): convenience relationship for when the purchasable is a product
- `property()` — belongs to [Property](../../property/models/property.md) (`property_id`): the property sold on this line (if any)
- `propertyGroup()` — belongs to [PropertyGroup](../../property/models/property-group.md) (`property_group_id`): the property group sold on this line (if any)
- `liabilityLines()` — has many [LiabilityLine](../../liability/models/liability-line.md): fulfillment tracking lines generated from this order line

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle events are dispatched by `OrderLineObserver`:
- `OrderLineCreating` dispatched on `creating`
- `OrderLineSaving` dispatched on `saving`
- `OrderLineSaved` dispatched on `saved`

## Observers

- `OrderLineObserver` — registered in `OrderServiceProvider::registerObservers()` (`OrderLine::observe(OrderLineObserver::class)`). Handles:
  - `creating` — dispatches `OrderLineCreating` event
  - `saving` — dispatches `OrderLineSaving` event
  - `saved` — dispatches `OrderLineSaved` event
  - `created` — fires `analytics()->track('Order Line Created')`
  - `deleting` — wraps deletion in a DB transaction; runs `PreDeleteOrderLine` checks

## Key Methods

- `ownerFile(): ?OwnerFile` — returns the owner file associated with the line's property (delegates to `$this->property?->ownerFile()`); not a standard Eloquent relationship method
- `availableLiabilityLines(): Collection` — filters `liabilityLines` in memory to those with no `delivery_date` and no `cancellation_date`
- `deliveredLiabilityLines(): Collection` — filters `liabilityLines` in memory to those with a non-null `delivery_date`
- `canceledLiabilityLines(): Collection` — filters `liabilityLines` in memory to those with a non-null `cancellation_date`

## Common Usage

```php
// Add a line item to an order
$line = $order->orderLines()->create([
    'purchasable_type' => Product::class,
    'purchasable_id'   => $product->id,
    'name'             => $product->name,
    'sku'              => $product->sku,
    'unit_price'       => 1000,   // cents; reads back as 10.00 via HasMoneyFields
    'quantity'         => 2,
    'sub_total'        => 2000,
    'total'            => 2000,
]);

// Assign a customer to a line
$line->update(['assigned_customer_id' => $customer->id]);

// Check fulfillment status
$pending   = $line->available_liab_qty;   // int
$delivered = $line->delivered_liab_qty;
$canceled  = $line->canceled_liab_qty;

// Access delivery preference from config_data
$prefDate = $line->delivery_preference_date;

// Get the owner file for the sold property
$ownerFile = $line->ownerFile();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
