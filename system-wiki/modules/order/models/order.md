---
model: Order
module: Order
table: orders
connection: tenant
primary_source: modules/Order/Models/Order.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Order/Observers/OrderObserver.php
  - modules/Order/Providers/OrderServiceProvider.php
  - modules/Commission/Models/RepAssociation.php
  - modules/Common/Models/Address.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Customer/Models/Customer.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Order/Models/OrderLine.php
  - modules/PaymentPlan/Models/PaymentPlan.php
  - modules/Property/Models/Property.php
  - modules/Property/Models/PropertyCommitment.php
  - modules/Property/Models/PropertyGroup.php
traits:
  - HasApprovals
  - HasByUserFields
  - HasExternalApprovals
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasMoneyFields
  - HasSearch
  - HasTransactions
  - HasTransactionService
  - SoftDeletes
related_models: [Address, Cemetery, Customer, LiabilityLine, ListOption, Note, Order, OrderLine, PaymentPlan, Property, PropertyCommitment, PropertyGroup, RepAssociation]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, contract, core]
---

# Order

## Overview

The Order model represents a sales contract between the cemetery and one or more customers. It is a central financial document in Everspot, capturing the items purchased (via `OrderLine`), the total amounts, payment arrangements, and the approval workflow required to post (finalize) the contract.

Orders move through a simple status lifecycle: `pending` while being configured, `posted` after approval and accounting posting, and `voided` if cancelled. Posting an order is gated by the `HasApprovals` / `HasExternalApprovals` workflow — specifically, the order must have a full payment arrangement (down payment + payment plan, if applicable) and valid G/L accounts before it can be approved and posted via the `PostOrder` action.

Money columns (`sub_total`, `total`, `tax_total`, `discount_total`) are stored as integer cents and transparently converted to dollars by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields). The model also carries soft deletes, audit user stamps, model numbering, Spatie MediaLibrary file attachments, search indexing, and external-integration sync — all via traits (see [Traits](#traits)).

An order can have multiple customers in different roles (via the `customer_order` pivot). The `primary_customer_id` column and `primaryCustomer()` relationship are an additional direct FK used for display and title suffix purposes; the richer role-based many-to-many relationship is `customers()`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| date | date | Yes | - | Order date |
| model_no | varchar | Yes | - | User-facing order number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery this order belongs to |
| primary_customer_id | bigint | Yes | - | FK → customers: the primary customer on the order |
| order_type_id | bigint | Yes | - | FK → list_options: order type (e.g. pre-need, at-need) |
| status | varchar | No | - | Order status (`pending`, `posted`, `voided`) |
| sub_total | int | No | 0 | Line-item subtotal in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| discount_total | int | No | 0 | Total discounts in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| tax_total | int | No | 0 | Total taxes in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| total | int | No | 0 | Order grand total in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| comments | text | Yes | - | Free-text comments |
| sale_date | date | Yes | - | Date of sale (may differ from order date) |
| no_comm_sale | tinyint | No | 0 | Whether this sale is excluded from commission calculations |
| meta | json | Yes | - | Additional metadata |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `model_no`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `primary_customer_id` → `customers.id`; `order_type_id` → `list_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `cemetery_id`, `order_type_id`, `status`, `total`; FK-backing indexes on `primary_customer_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `date`
- `sale_date` → `date`
- `no_comm_sale` → `boolean`

<!-- trait-contributed casts (money cents/dollars conversion via HasMoneyFields) are documented in the trait doc, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
const STATUSES = [
    'pending' => ['label' => 'Pending', 'color' => 'warning'],
    'posted'  => ['label' => 'Posted',  'color' => 'success'],
    'voided'  => ['label' => 'Voided',  'color' => 'secondary'],
];

public $moneyAttributes = ['sub_total', 'total', 'tax_total', 'discount_total'];
```

## Accessors & Mutators

- `getOrderTypeBadgeAttribute(): string` — HTML badge for the order type (pre-need gets `bg-soft-info`, others get `bg-soft-dark`)
- `getShippingAddressAttribute(): ?Address` — the shipping address from the polymorphic addresses collection (`shipping_default = 1`)
- `getBillingAddressAttribute(): ?Address` — the billing address from the polymorphic addresses collection (`billing_default = 1`)
- `getOrderTypeAttribute(): ?string` — name of the related order-type [ListOption](../../common/models/list-option.md)
- `getOrderLinesCountAttribute(): int` — count of associated order lines
- `getAmountFinancedTotalAttribute(): float` — the `amount_financed` from the associated payment plan (0 if no plan)
- `getDownPaymentTotalAttribute(): float` — total down payments (sum of non-financing-transfer transactions, negated, in dollars)
- `getTotalPrincipalPaidAttribute(): float` — sum of down payment total and payment plan principal paid
- `getAmountDueAttribute(): float` — order total minus the arranged amount (financed + down payment)

## Traits

- [HasApprovals](../../../system/traits/index.md#hasapprovals) — internal approval workflow; posting an order goes through the approval gate (implements `onApprovalRequestApproval()` and `canApproveApproval()`)
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasExternalApprovals](../../../system/traits/index.md#hasexternalapprovals) — external approval workflow (e.g. for customer-facing approval of order terms)
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `OrderFactory`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments for order documents
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` for the order
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `sub_total`, `total`, `tax_total`, `discount_total`
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; searchable payload built in `addToSearchData()` (primary customer's full name)
- [HasTransactions](../../../system/traits/index.md#hastransactions) — polymorphic `transactions()` and `payments()` relationships (transactionable morph)
- [HasTransactionService](../../../system/traits/index.md#hastransactionservice) — access to `TransactionService` for creating charges, credits, and cancellation credits
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — orders are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

**Customers:**
- `customers()` — belongs-to-many [Customer](../../customer/models/customer.md) via `customer_order` (pivot `role`): all customers associated with this order in any role
- `primaryCustomer()` — belongs to [Customer](../../customer/models/customer.md) (`primary_customer_id`): the primary customer (denormalized FK for display)
- `additionalCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) via `customer_order` where `role = additional`: additional customers only

**Line items:**
- `orderLines()` — has many [OrderLine](./order-line.md): the individual line items on this order

**Financial:**
- `liabilityLines()` — has-many-through [LiabilityLine](../../liability/models/liability-line.md) (through OrderLine): all liability lines for this order
- `liabilityLinesWithDeliveries()` — has-many-through [LiabilityLine](../../liability/models/liability-line.md) scoped to lines that have delivery lines (eager-loaded)
- `paymentPlan()` — has one [PaymentPlan](../../payment-plan/models/payment-plan.md): the financing arrangement for this order

**Property:**
- `properties()` — has-many-through [Property](../../property/models/property.md) (through OrderLine via `property_id`): properties sold on this order
- `propertyGroups()` — has-many-through [PropertyGroup](../../property/models/property-group.md) (through OrderLine via `property_group_id`): property groups on this order
- `propertyCommitments()` — morphMany [PropertyCommitment](../../property/models/property-commitment.md) (`parent`): property ownership commitments created for this order

**Administrative:**
- `repAssociations()` — morphMany [RepAssociation](../../commission/models/rep-association.md) (`repable`): sales rep associations for commission tracking
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): order notes
- `addresses()` — morphMany [Address](../../common/models/address.md) (`addressable`): all addresses (billing, shipping)
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the cemetery this order belongs to
- `orderTypeOption()` — belongs to [ListOption](../../common/models/list-option.md) (`order_type_id`): the order type

## Scopes

- `inProgress($query): Builder` — filters to orders with status not in `['voided', 'posted']`, ordered by status

## Events

_None defined on the model._ Lifecycle events are dispatched by `OrderObserver`:
- `OrderSaving` dispatched on `saving`
- `OrderSaved` dispatched on `saved`

## Observers

- `OrderObserver` — registered in `OrderServiceProvider::registerObservers()` (`Order::observe(OrderObserver::class)`). Handles:
  - `saving` — dispatches `OrderSaving` event
  - `saved` — dispatches `OrderSaved` event
  - `created` — fires `analytics()->track('Order Created')`
  - `deleting` — wraps deletion in a DB transaction; runs `PreDeleteOrder` checks

## Key Methods

- `handlePropertyCommitments(): void` — executes `HandlePropertyCommitmentsForOrder` to create/update property commitments based on the order's property lines
- `transactionUpdated($transaction): void` — called by `HasTransactionService` when a transaction changes; executes `ReportPaidAmtToLiabilityLines` to sync paid amounts to liability lines
- `calculatePrincipalPaidPct(): float` — returns the fraction of `total` that has been paid (0–1; returns 1 when total ≤ 0)
- `hasPaymentArrangement(): bool` — true if the order has a payment plan OR a down payment
- `hasPaymentPlan(): bool` — true if a `PaymentPlan` instance is associated
- `hasDownPayment(): bool` — true if there are any payment transactions
- `hasFullPaymentArrangement(): bool` — true when `amount_due == 0`
- `canAcceptDeposits(): bool` — true when `amount_due > 0`
- `canSetupPaymentPlan(): bool` — true when the payment-plan feature is enabled and `amount_due > 0`
- `onApprovalRequestApproval(): void` — executes `PostOrder` when the internal approval is approved; throws on inactive G/L account
- `getQuickApproveActionName(): string` — returns `'Post Contract'` (the label for the quick-approve action)
- `canApproveApproval(): void` — validates that the order is pending, has full payment arrangement, and has valid G/L accounts; throws `CannotExecuteAction` otherwise
- `canPostOrder(): bool` — true if `canApproveApproval()` passes without exception
- `canBeReopened(): bool` — delegates to the modification strategy
- `onVoided(): void` — deletes the associated payment plan when the order is voided
- `createOrUpdateBillingAddress(Address $address): void` — upserts the billing address (replicates the supplied address, sets `billing_default = true`)
- `createOrUpdateShippingAddress(Address $address): void` — upserts the shipping address (replicates the supplied address, sets `shipping_default = true`)
- `addToSearchData(): array` — returns `['customer_full_name' => ...]` for [HasSearch](../../../system/traits/index.md#hassearch)
- `getModelTitleSuffix(): ?string` — returns the primary customer's full name (used by model numbering display)

## Common Usage

```php
// Create a new order
$order = Order::create([
    'cemetery_id'        => $cemetery->id,
    'primary_customer_id' => $customer->id,
    'order_type_id'      => $orderTypeOption->id,
    'date'               => today(),
    'status'             => 'pending',
]);

// Check if the order is ready to post
if ($order->canPostOrder()) {
    $order->onApprovalRequestApproval();
}

// Payment arrangement checks
if (!$order->hasFullPaymentArrangement()) {
    $remaining = $order->amount_due; // dollars, via HasMoneyFields
}

// Query scopes
$openOrders = Order::inProgress()->get();

// Billing/shipping address helpers
$order->createOrUpdateBillingAddress($customer->defaultBillingAddress);
$billing = $order->billing_address;
$shipping = $order->shipping_address;

// Soft delete (runs PreDeleteOrder via observer)
$order->delete();
```

## Imports

This model can be created/updated via spreadsheet import. See **[order](../imports/order.md)** for the column reference (valid headers, required fields, types, and conditional rules).

The import mechanism (upload → queued job → Excel) is documented in the [import subsystem](../../../system/imports.md).

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
