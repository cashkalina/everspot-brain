---
model: TrustAccountTransaction
module: Trust
table: trust_account_transactions
connection: tenant
primary_source: modules/Trust/Models/TrustAccountTransaction.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Trust/Observers/TrustAccountTransactionObserver.php
  - modules/Trust/Providers/TrustServiceProvider.php
  - modules/Trust/Models/TrustTransactionType.php
  - modules/Trust/Models/TrustAccount.php
  - modules/Trust/Models/TrustApproval.php
  - modules/Trust/Models/TrustElement.php
  - modules/Trust/Models/TrustAccountTransactionApplication.php
traits:
  - HasMoneyFields
  - HasByUserFields
related_models: [TrustAccount, TrustAccountTransactionApplication, TrustApproval, TrustElement, TrustTransactionType]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, transaction]
---

# TrustAccountTransaction

## Overview

`TrustAccountTransaction` represents a posted (batched) transaction against a trust account — a single debit or credit event that moves money in or out of the trust. Where `TrustApproval` tracks individual pending approval items, `TrustAccountTransaction` records the finalized transaction batch once those approvals are processed and committed to the ledger.

Each transaction captures the date, period (start/end dates for period-based entries), and three pairs of financial amounts — principal and income amounts plus balances — held as integer cents and transparently converted by `HasMoneyFields`. The transaction type (`type_id` → `TrustTransactionType`) classifies the entry (e.g., Deposit, Withdrawal, Fee) and drives how it is handled downstream.

Audit user stamps (`created_by`, `updated_by`, `deleted_by`) from `HasByUserFields` record which staff member initiated each transaction. The observer dispatches `TrustAccountTransactionSaved` on every save, and `TrustAccountTransactionDeleted` on deletion, enabling downstream balance recalculations and reporting. Applications (`TrustAccountTransactionApplication`) link this transaction to others it offsets or is offset by, supporting net-application accounting flows.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| trust_account_id | bigint | No | - | FK → trust_accounts: the account this transaction belongs to |
| type_id | bigint | No | - | FK → trust_transaction_types: the transaction type |
| period_start_date | date | Yes | - | Start of the period this transaction covers (via TimezonedDateTime cast) |
| period_end_date | date | Yes | - | End of the period this transaction covers (via TimezonedDateTime cast) |
| date | date | No | - | Transaction effective date (via TimezonedDateTime cast) |
| principal_amt | int | No | 0 | Principal amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| income_amt | int | No | 0 | Income amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| total_amt | int | No | 0 | Total amount in cents — sum of principal + income (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| principal_balance | int | No | 0 | Running principal balance in cents after this transaction (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| income_balance | int | No | 0 | Running income balance in cents after this transaction (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| total_balance | int | No | 0 | Total running balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| created_by | bigint | Yes | - | User who created this transaction (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated this transaction (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who deleted this transaction (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `trust_account_id` → `trust_accounts.id`; `type_id` → `trust_transaction_types.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** single-column indexes on `date`, `principal_balance`, `income_balance`, `total_balance`, `trust_account_id`, `type_id`; period indexes on `period_start_date`, `period_end_date`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `TimezonedDateTime::class` — transaction effective date with timezone-aware handling
- `period_start_date` → `TimezonedDateTime::class` — period start date with timezone-aware handling
- `period_end_date` → `TimezonedDateTime::class` — period end date with timezone-aware handling

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['principal_amt', 'income_amt', 'total_amt', 'principal_balance', 'income_balance', 'total_balance']` — these are processed by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for the six money columns declared in `$moneyAttributes`
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit relationships backed by `created_by` / `updated_by` / `deleted_by`

## Relationships

- `type()` — belongs to [TrustTransactionType](./trust-transaction-type.md) (`type_id`): the transaction type defining how this entry is classified and processed
- `trustAccount()` — belongs to [TrustAccount](./trust-account.md) (`trust_account_id`): the trust account this transaction belongs to
- `trustApprovals()` — has many [TrustApproval](./trust-approval.md): the approval records that were batched into this transaction
- `trustElements()` — has many [TrustElement](./trust-element.md): the individual trust element line items that make up this transaction
- `applyingApplications()` — has many [TrustAccountTransactionApplication](./trust-account-transaction-application.md) (`applying_id`): applications where this transaction is the one being applied (outgoing/source side)
- `appliedToApplications()` — has many [TrustAccountTransactionApplication](./trust-account-transaction-application.md) (`applied_to_id`): applications where this transaction is the one being applied to (incoming/target side)

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle events are dispatched by `TrustAccountTransactionObserver` (see Observers).

## Observers

- `TrustAccountTransactionObserver` — registered in `TrustServiceProvider::registerObservers()` (`TrustAccountTransaction::observe(TrustAccountTransactionObserver::class)`). Handles:
  - `saved` — dispatches `TrustAccountTransactionSaved` event
  - `deleted` — dispatches `TrustAccountTransactionDeleted` event
  - `saving`, `creating`, `created`, `updated`, `restored`, `forceDeleted` — present as stubs with no active logic

## Key Methods

- `hasDetail(): bool` — returns `true` if this transaction has any associated `TrustElement` records (used to show/hide detail views)
- `updateTotalAmount(): void` — recalculates `total_amt` as `principal_amt + income_amt` and saves if the value has changed; ensures the total stays in sync with component parts

## Common Usage

```php
// Retrieve transactions for a trust account, ordered by date
$transactions = TrustAccountTransaction::where('trust_account_id', $account->id)
    ->with(['type', 'trustElements', 'trustApprovals'])
    ->orderBy('date', 'desc')
    ->get();

// Check if a transaction has element-level detail
if ($transaction->hasDetail()) {
    $elements = $transaction->trustElements;
}

// Ensure total_amt stays in sync after adjusting principal/income
$transaction->principal_amt = 5000; // in cents
$transaction->income_amt = 200;     // in cents
$transaction->updateTotalAmount();  // sets total_amt = 5200 and saves

// Access the type
echo $transaction->type->name; // "Deposit"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
