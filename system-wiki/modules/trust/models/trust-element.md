---
model: TrustElement
module: Trust
table: trust_elements
connection: tenant
primary_source: modules/Trust/Models/TrustElement.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Trust/Observers/TrustElementObserver.php
  - modules/Trust/Providers/TrustServiceProvider.php
  - modules/Trust/Models/TrustAccountTransactionApplication.php
  - modules/Trust/Models/TrustArrangement.php
  - modules/Trust/Models/TrustAccountTransaction.php
  - modules/Trust/Models/TrustAccount.php
  - modules/Trust/Models/TrustApproval.php
traits:
  - HasMoneyFields
related_models: [TrustAccount, TrustAccountTransaction, TrustAccountTransactionApplication, TrustApproval, TrustArrangement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, transaction]
---

# TrustElement

## Overview

`TrustElement` is the atomic line-item record in the trust processing pipeline — a single deposit or withdrawal action associated with a specific `TrustArrangement`. Where `TrustArrangement` tracks the aggregate obligation, `TrustElement` records the individual triggered amounts that flow through approval and into a posted transaction.

Each element carries the `transaction_type` (deposit or withdrawal, as `TransactionType` enum), a `triggered_date`, and amounts (principal and income, stored in cents). It is also polymorphically linked to the same arrangeable entity as its parent `TrustArrangement` via `trust_arrangeable_type` / `trust_arrangeable_id`. The element progresses through a lifecycle tracked by three boolean flags: `is_awaiting_deposit`, `is_ready` (ready for approval), and `is_completed` (posted to a transaction).

The observer initializes `principal_balance` and `income_balance` to match `principal_amt` and `income_amt` on creation. When `is_ready` transitions to `true`, `TrustElementReady` is dispatched to notify downstream processors. `TrustElementSaved` fires on every save, and `TrustElementDeleted` on deletion, enabling cascading balance updates on `TrustArrangement`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| trust_arrangement_id | bigint | No | - | FK → trust_arrangements: the parent arrangement this element belongs to |
| trust_arrangeable_type | varchar | No | - | Polymorphic parent entity class (mirrored from arrangement) |
| trust_arrangeable_id | bigint | No | - | Polymorphic parent entity ID (mirrored from arrangement) |
| trust_account_id | bigint | No | - | FK → trust_accounts: the trust account for this element |
| trust_approval_id | bigint | Yes | - | FK → trust_approvals: the approval this element is batched into (null = not yet approved) |
| trust_account_transaction_id | bigint | Yes | - | FK → trust_account_transactions: the posted transaction (null = not yet posted) |
| type | varchar | No | - | Element type classification (e.g., schedule type identifier) |
| transaction_type | varchar | No | - | Deposit or withdrawal direction (cast to `TransactionType` enum) |
| triggered_date | date | No | - | Date this element was triggered (via TimezonedDateTime cast) |
| principal_amt | int | No | - | Principal amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| income_amt | int | No | - | Income amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| principal_balance | int | No | - | Remaining principal balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| income_balance | int | No | - | Remaining income balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| is_awaiting_deposit | tinyint | No | 0 | Whether the element is waiting for a deposit prerequisite |
| is_ready | tinyint | No | 0 | Whether the element is ready to be processed for approval |
| is_completed | tinyint | No | 0 | Whether the element has been posted to a transaction |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `trust_arrangement_id` → `trust_arrangements.id`; `trust_account_id` → `trust_accounts.id`; `trust_approval_id` → `trust_approvals.id`; `trust_account_transaction_id` → `trust_account_transactions.id`

**Indexes:** single-column indexes on `is_awaiting_deposit`, `is_ready`, `is_completed`, `trust_account_id`, `trust_account_transaction_id`, `trust_approval_id`, `trust_arrangement_id`; composite index on (`trust_arrangeable_type`, `trust_arrangeable_id`).

## Casts

- `triggered_date` → `TimezonedDateTime::class` — triggered date with timezone-aware handling
- `transaction_type` → `TransactionType::class` — cast to `Modules\Trust\Enums\TransactionType` enum (`DEPOSIT`, `WITHDRAWAL`)
- `is_awaiting_deposit` → `'boolean'`
- `is_ready` → `'boolean'`
- `is_completed` → `'boolean'`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['principal_amt', 'income_amt', 'principal_balance', 'income_balance']` — processed by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

- `getTotalAmountAttribute(): float` — `principal_amt + income_amt` (sum of the two amount fields)
- `getTotalBalanceAttribute(): float` — `principal_balance + income_balance` (sum of the two balance fields)
- `getApprovedBadgeAttribute(): string` — HTML Bootstrap badge: green "Approved" if `isApproved()`, amber "Not Approved" otherwise
- `getTransactedBadgeAttribute(): ?string` — HTML Bootstrap badge indicating deposit/withdrawal completed status; returns `null` if `transaction_type` is neither

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `principal_amt`, `income_amt`, `principal_balance`, and `income_balance`

## Relationships

- `applyingApplications()` — has many [TrustAccountTransactionApplication](./trust-account-transaction-application.md) (`element_applying_id`): applications where this element is the source
- `appliedToApplications()` — has many [TrustAccountTransactionApplication](./trust-account-transaction-application.md) (`element_applied_to_id`): applications where this element is the target
- `trustArrangement()` — belongs to [TrustArrangement](./trust-arrangement.md) (`trust_arrangement_id`): the parent arrangement
- `trustAccountTransaction()` — belongs to [TrustAccountTransaction](./trust-account-transaction.md) (`trust_account_transaction_id`): the posted transaction this element is part of (null if not yet posted)
- `trustAccount()` — belongs to [TrustAccount](./trust-account.md) (`trust_account_id`): the trust account
- `trustArrangeable()` — morphTo: the parent arrangeable entity (same model as `trustArrangement()->trustArrangeable()`)
- `trustApproval()` — belongs to [TrustApproval](./trust-approval.md) (`trust_approval_id`): the approval batch this element belongs to (null if not yet approved)
- `relatedElements()` — has many [TrustElement](./trust-element.md) (all elements sharing the same `trust_arrangement_id`): sibling elements in the same arrangement

## Scopes

- `pending(Builder $query)` — filters to elements where `trust_account_transaction_id IS NULL` AND `is_ready = true` (ready for processing but not yet posted)
- `completed(Builder $query)` — filters to elements where `trust_account_transaction_id IS NOT NULL` (posted to a transaction)
- `awaitingApproval(Builder $query)` — filters to elements where `trust_approval_id IS NULL` (not yet batched into an approval)

## Events

_None defined on the model._ Lifecycle events are dispatched by `TrustElementObserver` (see Observers).

## Observers

- `TrustElementObserver` — registered in `TrustServiceProvider::registerObservers()` (`TrustElement::observe(TrustElementObserver::class)`). Handles:
  - `creating` — sets `principal_balance = principal_amt` and `income_balance = income_amt` (initializes balances to match amounts)
  - `created` — dispatches `TrustElementReady` if `is_ready = 1` at creation time
  - `saved` — dispatches `TrustElementSaved` event
  - `updated` — dispatches `TrustElementReady` when `is_ready` transitions from `0`/null to `1`
  - `deleted` — dispatches `TrustElementDeleted` event
  - `restored`, `forceDeleted` — no active logic

## Key Methods

- `isApproved(): bool` — returns `true` when `trust_approval_id` is set (element has been batched into an approval)
- `isTransacted(): bool` — returns `true` when `trust_account_transaction_id` is set (element has been posted to a transaction)

## Common Usage

```php
// All pending elements for an arrangement (ready but not posted)
$pending = TrustElement::where('trust_arrangement_id', $arrangement->id)
    ->pending()
    ->get();

// All elements awaiting approval
$unapproved = TrustElement::where('trust_account_id', $account->id)
    ->awaitingApproval()
    ->get();

// Check lifecycle state
if ($element->isApproved() && !$element->isTransacted()) {
    // Approved but still waiting to be posted
}

// Access computed totals
echo $element->total_amount;  // principal_amt + income_amt (in dollars)
echo $element->total_balance; // principal_balance + income_balance

// Display badges
echo $element->approved_badge;   // HTML badge
echo $element->transacted_badge; // HTML badge

// Sibling elements in the same arrangement
$siblings = $element->relatedElements;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
