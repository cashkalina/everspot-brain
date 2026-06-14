---
model: LiabilityLine
module: Liability
table: liability_lines
connection: tenant
primary_source: modules/Liability/Models/LiabilityLine.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Liability/Observers/LiabilityLineObserver.php
  - modules/Liability/Providers/LiabilityServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/DeliveryPreference.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/OwnerFile.php
  - modules/Customer/Models/Customer.php
  - modules/Order/Models/Order.php
  - modules/Order/Models/OrderLine.php
  - modules/Product/Models/Product.php
  - modules/Property/Models/Property.php
  - modules/Property/Models/PropertyCommitment.php
  - modules/Property/Models/PropertyGroup.php
  - modules/Cancellation/Models/CancellationLine.php
  - modules/Certificate/Models/CertificateLine.php
  - modules/Commission/Models/RepAssociation.php
  - modules/Delivery/Models/DeliveryLine.php
traits:
  - HasByUserFields
  - HasDateStatusFields
  - HasModelNumbering
  - HasMoneyFields
  - HasRecognition
  - HasSearch
  - HasTrusting
  - SoftDeletes
related_models: [CancellationLine, Cemetery, Certificate, CertificateLine, Customer, DeliveryLine, DeliveryPreference, ListOption, Order, OrderLine, OwnerFile, Product, Property, PropertyCommitment, PropertyGroup, RepAssociation]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract, inventory]
---

# LiabilityLine

## Overview

The LiabilityLine model represents a single line item on a sales liability — a product or service sold to a customer through the Everspot ordering system. It is one of the core transactional entities in the cemetery management workflow, bridging the relationship between a sales order, a product, a property, and the customers who hold financial responsibility.

Each liability line tracks the full lifecycle of an item from sale through delivery or cancellation: sale price, cost price, tax, accounts-receivable paid amount, and a set of date markers (sale date, delivery date, constructive date, cancellation date, certificate issuance date, paid-in-full date, and delivery preference date). Money columns are stored in cents and exposed as decimal dollars via the `HasMoneyFields` trait.

Customers are attached to a liability line through a many-to-many pivot with a `role` column (primary, assigned, additional). A denormalized `primary_customer_name` and `primary_customer_data` JSON snapshot is kept on the record for fast display without a join. The line can be linked to a specific property, a property group, a delivery preference, and generates a user-facing model number via `HasModelNumbering`.

LiabilityLine also participates in the Recognition and Trust modules: JSON `recognition_config` and `trusting_config` columns store per-line configuration, and the traits wire up the corresponding module relationships. Commission tracking is supported through a polymorphic `RepAssociation` morph.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| date | date | No | - | Record date (the base date for this liability line) |
| model_no | varchar | Yes | - | User-facing liability line number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| cemetery_id | bigint | No | - | FK → cemeteries |
| order_type_id | bigint | Yes | - | FK → list_options: order type (e.g. Pre-Need, At-Need) |
| order_id | bigint | Yes | - | FK → orders |
| order_line_id | bigint | Yes | - | FK → order_lines |
| product_id | bigint | Yes | - | FK → products |
| commission_category_id | bigint | Yes | - | FK → commission_categories |
| property_id | bigint | Yes | - | FK → properties: associated property |
| property_group_id | bigint | Yes | - | FK → property_groups |
| delivery_preference_id | bigint | Yes | - | FK → delivery_preferences |
| primary_customer_name | varchar | Yes | - | Denormalized name of the primary customer |
| primary_customer_data | json | Yes | - | Denormalized snapshot of primary customer data |
| delivery_pref_date | date | Yes | - | Requested delivery preference date |
| recognition_config | json | Yes | - | Per-line recognition module configuration (via [HasRecognition](../../../system/traits/index.md#hasrecognition) — see trait doc) |
| trusting_config | json | Yes | - | Per-line trust module configuration (via [HasTrusting](../../../system/traits/index.md#hastrusting) — see trait doc) |
| sale_date | date | Yes | - | Date the item was sold |
| constructive_date | date | Yes | - | Constructive delivery date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| delivery_date | date | Yes | - | Actual physical delivery date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| cancellation_date | date | Yes | - | Cancellation date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| certificate_issuance_date | date | Yes | - | Date the certificate was issued |
| pif_date | date | Yes | - | Paid-in-full date |
| ar_paid_amt | int | No | 0 | AR paid amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| order_reference | varchar | Yes | - | Human-readable order reference string |
| product_sku | varchar | Yes | - | Product SKU at time of sale (denormalized) |
| product_name | varchar | No | - | Product name at time of sale (denormalized) |
| product_description | text | Yes | - | Product description at time of sale (denormalized) |
| sale_price | int | No | - | Sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| cost_price | int | No | 0 | Cost price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| tax | int | No | - | Tax amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| is_manual | tinyint | No | - | Whether this line was manually entered |
| source | varchar | No | - | Source of the line (e.g. order, manual) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `commission_category_id` → `commission_categories.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`; `delivery_preference_id` → `delivery_preferences.id`; `order_id` → `orders.id`; `order_line_id` → `order_lines.id`; `order_type_id` → `list_options.id`; `product_id` → `products.id`; `property_group_id` → `property_groups.id`; `property_id` → `properties.id`

**Indexes:** single-column indexes on `cancellation_date`, `cemetery_id`, `certificate_issuance_date`, `constructive_date`, `delivery_date`, `delivery_pref_date`, `delivery_preference_id`, `model_no`, `order_id`, `order_reference`, `order_type_id`, `pif_date`, `primary_customer_name`, `product_id`, `property_id`, `sale_date`; FK-backing indexes on `commission_category_id`, `created_by`, `deleted_by`, `order_line_id`, `property_group_id`, `updated_by`.

## Casts

- `recognition_config` → `array`
- `trusting_config` → `array`
- `primary_customer_data` → `array`
- `date` → `date`
- `sale_date` → `date`
- `delivery_date` → `date`
- `cancellation_date` → `date`
- `certificate_issuance_date` → `date`
- `delivery_pref_date` → `date`
- `constructive_date` → `date`
- `pif_date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes (cents storage, dollars access):** `ar_paid_amt`, `sale_price`, `cost_price`, `tax` — declared in `$moneyAttributes` for [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

- `getProductFullNameAttribute(): ?string` — concatenates `product_sku` and `product_name` into a single display string (space-separated, trimmed)
- `getOrderTypeBadgeAttribute(): string` — HTML badge: `bg-soft-info` for Pre-Need, `bg-soft-dark` for other types
- `getFormattedDeliveryPreferenceAttribute(): string` — combines the delivery preference name with the formatted `delivery_pref_date`
- `getBalanceRemainingAmtAttribute(): float` — `sale_price - ar_paid_amt` (balance still owed)

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — date-driven fulfillment status from delivery/constructive/cancellation/deed date columns; `open()` and `notCanceled()` scopes
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `ar_paid_amt`, `sale_price`, `cost_price`, `tax`
- [HasRecognition](../../../system/traits/index.md#hasrecognition) — wires up Recognition module relationships for this line
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; searchable payload built in `addToSearchData()`
- [HasTrusting](../../../system/traits/index.md#hastrusting) — wires up Trust module relationships for this line
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — liability lines are soft-deleted, never hard-deleted

## Relationships

**Customers:**
- `customers()` — belongs-to-many [Customer](../../customer/models/customer.md) via `customer_liability_line` (pivot `role`): all customers attached to this line with their role

**Order:**
- `order()` — belongs to [Order](../../order/models/order.md): the parent order
- `orderLine()` — belongs to [OrderLine](../../order/models/order-line.md): the originating order line
- `orderType()` — belongs to [ListOption](../../common/models/list-option.md) (`order_type_id`): order type

**Product & property:**
- `product()` — belongs to [Product](../../product/models/product.md): the product sold
- `property()` — belongs to [Property](../../property/models/property.md): associated property (if applicable)
- `propertyGroup()` — belongs to [PropertyGroup](../../property/models/property-group.md): associated property group
- `propertyCommitments()` — morphMany [PropertyCommitment](../../property/models/property-commitment.md) (`parent`): property commitments parented to this line
- `deliveryPreference()` — belongs to [DeliveryPreference](../../common/models/delivery-preference.md): preferred delivery method/timing

**Fulfillment:**
- `deliveryLines()` — has many [DeliveryLine](../../delivery/models/delivery-line.md): delivery records for this line
- `cancellationLines()` — has many [CancellationLine](../../cancellation/models/cancellation-line.md): cancellation records for this line
- `certificateLines()` — has many [CertificateLine](../../certificate/models/certificate-line.md): certificate lines generated from this liability line

**Other:**
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery this line belongs to
- `repAssociations()` — morphMany [RepAssociation](../../commission/models/rep-association.md) (`repable`): commission rep associations

## Scopes

- `hasProperty(Builder $query)` — filters to lines where `property_id` is not null

Fulfillment status scopes (`open()`, `notCanceled()`) are contributed by [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) (see trait doc).

## Events

_None defined on the model._ Lifecycle behavior is handled by `LiabilityLineObserver` (see Observers).

## Observers

- `LiabilityLineObserver` — registered in `LiabilityServiceProvider::registerObservers()` (`LiabilityLine::observe(LiabilityLineObserver::class)`). Handles:
  - `saved` — dispatches `LiabilityLineSaved` event
  - `deleting` — wraps deletion in a DB transaction running `PreDeleteLiabilityLine` checks

## Key Methods

- `primaryCustomer(): ?Customer` — returns the customer with `role = primary` from the `customers()` pivot
- `assignedCustomer(): ?Customer` — returns the customer with `role = assigned` from the `customers()` pivot
- `additionalCustomers(): Collection` — returns all customers with `role = additional`
- `ownerFile(): ?OwnerFile` — delegates to `$this->property?->ownerFile()`; returns the owner file for the associated property
- `isPaid(): bool` — returns `true` when `balance_remaining_amt <= 0`
- `isDeliverable(): bool` — returns `true` when the line is not date-canceled and not date-delivered
- `updatedDelivery(): void` — triggers `UpdateDeliveryDate` action to recalculate delivery status
- `updatedCancellation(): void` — triggers `UpdateCancellationDate` action to recalculate cancellation status
- `updateCustomers(array $data): void` — delegates to `UpdateCustomers` action with primary/assigned/additional customer arrays
- `updateProperty($propertyId): void` — delegates to `UpdateProperty` action
- `getFulfillmentHistoryRecords(): Collection` — delegates to `GetFulfillmentHistoryRecords` action; returns chronological fulfillment history
- `getRecognitionEntity(): Customer` — returns the primary customer; used by the Recognition trait to resolve the entity for this line
- `addToSearchData(): array` — provides `order_reference` and `primary_customer_name` to the search index
- `getModelTitleSuffix(): ?string` — returns `primary_customer_name` for use in model number generation
- `getAppRouteByType($type, $id = null): ?string` *(static)* — returns a named route URL for the given liability-line route type/id, or `null` if the route does not exist

## Common Usage

```php
// Load a liability line with its primary customer
$line = LiabilityLine::with('customers')->find($id);
$primary = $line->primaryCustomer();

// Check balance and delivery eligibility
if ($line->isPaid() && $line->isDeliverable()) {
    $line->updatedDelivery();
}

// Attach customers with roles
$line->updateCustomers([
    'primary_customer'    => $primaryCustomer,
    'assigned_customer'   => $assignedCustomer,
    'additional_customers' => [$customer3],
]);

// Scope to lines with an associated property
$withProperty = LiabilityLine::hasProperty()->get();

// Fulfillment history
$history = $line->getFulfillmentHistoryRecords();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
