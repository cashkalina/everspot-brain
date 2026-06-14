---
model: TrustAccountTransactionApplication
module: Trust
table: trust_account_transaction_applications
connection: tenant
primary_source: modules/Trust/Models/TrustAccountTransactionApplication.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Trust/Observers/TrustAccountTransactionApplicationObserver.php
  - modules/Trust/Providers/TrustServiceProvider.php
  - modules/Trust/Models/TrustAccountTransaction.php
  - modules/Trust/Models/TrustElement.php
traits:
  - HasMoneyFields
related_models: [TrustAccountTransaction, TrustElement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, transaction]
---

# TrustAccountTransactionApplication

## Overview

`TrustAccountTransactionApplication` represents the application of one trust transaction against another — a linking record that tracks how funds from one `TrustAccountTransaction` (the "applying" side) are matched and offset against a different `TrustAccountTransaction` (the "applied-to" side). This supports net-application accounting, where a deposit or withdrawal partially or fully offsets a previously posted transaction.

Each application record captures the date of the application and the principal and income amounts moved in that application pass. Optionally, the two corresponding `TrustElement` records that were matched (`element_applying_id` and `element_applied_to_id`) are also linked, providing element-level traceability for the application.

The observer dispatches `TrustAccountTransactionApplicationSaved` on every save and `TrustAccountTransactionApplicationDeleted` on deletion, enabling downstream recalculations of balances and summary views that depend on net applications.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| applying_id | bigint | No | - | FK → trust_account_transactions: the transaction doing the applying (source) |
| applied_to_id | bigint | No | - | FK → trust_account_transactions: the transaction being applied to (target) |
| element_applying_id | bigint | Yes | - | FK → trust_elements: the element on the applying side (nullable) |
| element_applied_to_id | bigint | Yes | - | FK → trust_elements: the element on the applied-to side (nullable) |
| date | date | No | - | Date the application was made |
| principal_amt | int | No | - | Principal amount applied in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| income_amt | int | No | - | Income amount applied in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `applying_id` → `trust_account_transactions.id` (cascade delete); `applied_to_id` → `trust_account_transactions.id` (cascade delete); `element_applying_id` → `trust_elements.id` (set null); `element_applied_to_id` → `trust_elements.id` (set null)

**Indexes:** `idx_applying_id` on `applying_id`; `idx_applied_to_id` on `applied_to_id`; `idx_elem_applying_id` on `element_applying_id`; `idx_elem_applied_to_id` on `element_applied_to_id`; `idx_date` on `date`.

## Casts

- `date` → `'date'` — application date cast to Carbon date

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['principal_amt', 'income_amt']` — processed by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `principal_amt` and `income_amt`

## Relationships

- `applyingTransaction()` — belongs to [TrustAccountTransaction](./trust-account-transaction.md) (`applying_id`): the transaction that is doing the applying (source/outgoing side)
- `appliedToTransaction()` — belongs to [TrustAccountTransaction](./trust-account-transaction.md) (`applied_to_id`): the transaction being applied against (target/incoming side)
- `applyingElement()` — belongs to [TrustElement](./trust-element.md) (`element_applying_id`): the trust element on the applying side (nullable)
- `appliedToElement()` — belongs to [TrustElement](./trust-element.md) (`element_applied_to_id`): the trust element on the applied-to side (nullable)

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle events are dispatched by `TrustAccountTransactionApplicationObserver` (see Observers).

## Observers

- `TrustAccountTransactionApplicationObserver` — registered in `TrustServiceProvider::registerObservers()` (`TrustAccountTransactionApplication::observe(TrustAccountTransactionApplicationObserver::class)`). Handles:
  - `saved` — dispatches `TrustAccountTransactionApplicationSaved` event
  - `deleted` — dispatches `TrustAccountTransactionApplicationDeleted` event
  - `created`, `updated`, `restored`, `forceDeleted` — no active logic

## Key Methods

_None beyond standard Eloquent._

## Common Usage

```php
// Create an application linking two transactions
$application = TrustAccountTransactionApplication::create([
    'applying_id'          => $depositTransaction->id,
    'applied_to_id'        => $withdrawalTransaction->id,
    'element_applying_id'  => $depositElement->id,
    'element_applied_to_id'=> $withdrawalElement->id,
    'date'                 => now()->toDateString(),
    'principal_amt'        => 10000, // cents
    'income_amt'           => 500,   // cents
]);

// Find all applications where a transaction is the source
$outgoing = TrustAccountTransactionApplication::where('applying_id', $txn->id)->get();

// Find all applications where a transaction is the target
$incoming = TrustAccountTransactionApplication::where('applied_to_id', $txn->id)->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
