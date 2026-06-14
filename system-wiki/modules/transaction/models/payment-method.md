---
model: PaymentMethod
module: Transaction
table: payment_methods
connection: tenant
primary_source: modules/Transaction/Models/PaymentMethod.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Transaction/Observers/PaymentMethodObserver.php
  - modules/Transaction/Providers/TransactionServiceProvider.php
  - modules/Customer/Models/Customer.php
  - modules/Transaction/Models/Transaction.php
  - modules/Autopay/Models/Autopay.php
traits:
  - HasByUserFields
  - HasSyncables
  - SoftDeletes
related_models: [Autopay, Customer, Transaction]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction, integration]
---

# PaymentMethod

## Overview

PaymentMethod stores a customer's reusable payment credentials — a tokenized credit/debit card or bank account (checking or savings) — as registered with the active payment processor. Sensitive card details are never stored directly; the model holds only the metadata needed to display and use the method: type, last four digits, expiration (for cards), bank name and routing number (for bank accounts), cardholder name, brand, and a default flag.

Every PaymentMethod is linked to a specific [Customer](../../customer/models/customer.md) and is syncable to external payment processors via [HasSyncables](../../../system/traits/index.md#hassyncables) — the actual payment processor record (e.g. a Stripe payment method ID) is stored in the syncable. A global scope (`AvailablePaymentMethods`) automatically filters all queries to only payment methods that have a syncable linked to the current tenant's payment processor integration, ensuring that only methods usable with the active gateway are visible.

PaymentMethod supports soft-deletes and carries audit user stamps. When a record is deleted, `PaymentMethodObserver` runs `PreDeletePaymentMethod` inside a DB transaction to handle any cleanup (e.g. detaching from autopays).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| customer_id | bigint | No | - | FK → customers: the customer who owns this payment method |
| type | varchar | No | - | Method type: card, checking, savings |
| holder_name | varchar | Yes | - | Cardholder or account holder name |
| last_four | varchar | No | - | Last four digits of card number or account number |
| exp_month | varchar | Yes | - | Card expiration month (cards only) |
| exp_year | varchar | Yes | - | Card expiration year (cards only) |
| brand | varchar | Yes | - | Card brand: visa, mastercard, amex, discover (cards only) |
| bank_name | varchar | Yes | - | Bank name (bank accounts only) |
| routing_number | varchar | Yes | - | Bank routing number (bank accounts only) |
| is_default | tinyint | No | 0 | Whether this is the customer's default payment method |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `customer_id` → `customers.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** Single-column indexes on `type`, `customer_id`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `is_default` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getFormattedTypeAttribute(): string` — for cards: returns the formatted brand (Visa, MasterCard, etc.); for bank accounts: `'Checking Account'` or `'Savings Account'`; otherwise `'Unknown'`
- `getFormattedBrandAttribute(): string` — human-readable card brand from the `brand` field (Visa, MasterCard, American Express, Discover, or `'Credit/Debit Card'` for unknown brands)
- `getMethodIconAttribute(): string` — returns an HTML `<img>` or `<i>` icon element for the payment method, sized as `avatar-sm`; bank gets a Bootstrap bank icon, each card brand gets its branded SVG
- `getExpirationDateAttribute(): string` — `'MM/YYYY'` format for cards; `'N/A'` for bank accounts
- `getFullNameAttribute(): string` — display label combining type and last four digits (e.g. `'Visa - x4242'`)

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [HasSyncables](../../../system/traits/index.md#hassyncables) — links the payment method to external payment processor records (e.g. Stripe or other gateway IDs); the `AvailablePaymentMethods` global scope depends on this
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — payment methods are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `customer()` — belongs to [Customer](../../customer/models/customer.md) (`customer_id`): the customer who owns this payment method
- `transactions()` — has many [Transaction](./transaction.md) (`payment_method_id`): all transactions using this method
- `autopays()` — has many [Autopay](../../autopay/models/autopay.md): autopay configurations that use this payment method

## Scopes

- `bankAccounts(Builder $query)` — filters to `type IN ('checking', 'savings')`
- `cards(Builder $query)` — filters to `type = 'card'`

**Global scope (auto-applied):** `AvailablePaymentMethods` — filters all queries to only methods with a syncable linked to the current tenant's payment processor integration. Applied via `static::addGlobalScope(new AvailablePaymentMethods)` in `booted()`.

## Events

_None._

## Observers

- `PaymentMethodObserver` — registered in `TransactionServiceProvider::registerObservers()` (`PaymentMethod::observe(PaymentMethodObserver::class)`). Handles:
  - `deleting` — runs `PreDeletePaymentMethod::execute()` inside a DB transaction to clean up before deletion (e.g. disassociate autopays)

## Key Methods

- `isCard(): bool` — true if `type === 'card'`
- `isBank(): bool` — true if `type` is `'checking'` or `'savings'`
- `getFundingType(): string` — returns `'Card'` for credit cards, `'Checking Account'`/`'Savings Account'` for bank accounts, or `'Unknown'`; for cards it delegates to `paymentProcessor()->getFundingType($this)` to determine the actual funding type (credit/debit/prepaid)
- `getProcessingFeeType(): FundingType` — returns the `FundingType` enum value (`ACH`, or the processor-determined type for cards); used to calculate the correct processing fee
- `getZipCode(): ?string` — retrieves the billing zip code for this payment method from the active payment processor; returns `null` if no processor is configured

## Common Usage

```php
// Get all payment methods for a customer (automatically filtered to active processor)
$methods = $customer->paymentMethods;

// Get only credit/debit cards
$cards = $customer->paymentMethods()->cards()->get();

// Get only bank accounts
$banks = $customer->paymentMethods()->bankAccounts()->get();

// Display method info
echo $method->full_name;        // "Visa - x4242"
echo $method->expiration_date;  // "04/2027"
echo $method->method_icon;      // HTML <img> element

// Check method type
if ($method->isCard()) {
    $feeType = $method->getProcessingFeeType(); // FundingType enum
}

// Soft-delete (observer runs PreDeletePaymentMethod cleanup)
$method->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
