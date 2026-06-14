---
model: TrustApproval
module: Trust
table: trust_approvals
connection: tenant
primary_source: modules/Trust/Models/TrustApproval.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Trust/Observers/TrustApprovalObserver.php
  - modules/Trust/Providers/TrustServiceProvider.php
  - modules/Trust/Models/TrustAccount.php
  - modules/Trust/Models/TrustElement.php
  - modules/Trust/Models/TrustAccountTransaction.php
  - modules/Trust/Models/TrustTransactionType.php
traits:
  - HasMoneyFields
  - HasSearch
  - HasByUserFields
related_models: [TrustAccount, TrustAccountTransaction, TrustElement, TrustTransactionType]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, transaction]
---

# TrustApproval

## Overview

`TrustApproval` represents a pending or processed approval record in the trust workflow — the staging area between individual trust element triggers and a finalized posted transaction. When trust elements become ready for processing, they are grouped into a `TrustApproval` (batched by type and date) that waits for an administrator to review and approve before being committed to a `TrustAccountTransaction`.

Each approval record captures the trust account, transaction type (deposit or withdrawal, stored as the `TransactionType` enum in `transaction_type`), the effective date, an as-of date, and an optional memo. Once approved and posted, the `trust_account_transaction_id` is populated; while that field is null, the approval is "pending." Audit stamps (`created_by`, `updated_by`, `deleted_by`) from `HasByUserFields` record which staff members interacted with the approval.

The model provides computed accessors for the total principal, income, and combined amounts by summing across its related `TrustElement` records. The `TrustApprovalObserver` dispatches `TrustApprovalSaved` on every save, enabling downstream balance and status recalculations.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| trust_account_id | bigint | No | - | FK → trust_accounts: the trust account this approval belongs to |
| trust_account_transaction_id | bigint | Yes | - | FK → trust_account_transactions: the posted transaction (null = still pending) |
| transaction_type | varchar | No | - | Deposit or withdrawal direction (cast to `TransactionType` enum) |
| date | date | No | - | Effective date of the approval |
| as_of_date | date | No | - | As-of date for balance calculations |
| memo | varchar | Yes | - | Optional memo or description |
| created_by | bigint | Yes | - | User who created this approval (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated this approval (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who deleted this approval (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `trust_account_id` → `trust_accounts.id`; `trust_account_transaction_id` → `trust_account_transactions.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** single-column indexes on `trust_account_id`, `trust_account_transaction_id`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `'date'` — effective date cast to Carbon date
- `as_of_date` → `'date'` — as-of date cast to Carbon date
- `transaction_type` → `TransactionType::class` — cast to `Modules\Trust\Enums\TransactionType` enum (`DEPOSIT`, `WITHDRAWAL`)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getTotalPrincipalAmtAttribute(): float` — sum of `principal_amt` across all related `trustElements` (computed from loaded collection)
- `getTotalIncomeAmtAttribute(): float` — sum of `income_amt` across all related `trustElements` (computed from loaded collection)
- `getTotalAmtAttribute(): float` — `total_income_amt + total_principal_amt` (uses the two computed accessors above)

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for money columns
- [HasSearch](../../../system/traits/index.md#hassearch) — indexes trust approvals in global search
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backed by `created_by` / `updated_by` / `deleted_by`

## Relationships

- `trustAccount()` — belongs to [TrustAccount](./trust-account.md) (`trust_account_id`): the trust account this approval relates to
- `trustElements()` — has many [TrustElement](./trust-element.md): the trust element line items grouped into this approval
- `trustAccountTransaction()` — belongs to [TrustAccountTransaction](./trust-account-transaction.md) (`trust_account_transaction_id`): the posted transaction created from this approval (null when still pending)

## Scopes

- `pending(Builder $query)` — filters to approvals where `trust_account_transaction_id IS NULL` (not yet posted)
- `forTrustTransactionType(Builder $query, TrustTransactionType $type)` — filters by the transaction direction(s) that the given `TrustTransactionType` supports automatic processing for; handles deposit-only, withdrawal-only, and both-direction types

## Events

_None defined on the model._ Lifecycle events are dispatched by `TrustApprovalObserver` (see Observers).

## Observers

- `TrustApprovalObserver` — registered in `TrustServiceProvider::registerObservers()` (`TrustApproval::observe(TrustApprovalObserver::class)`). Handles:
  - `saved` — dispatches `TrustApprovalSaved` event
  - `creating`, `created`, `updated`, `deleted`, `restored`, `forceDeleted` — present as stubs with no active logic

## Key Methods

- `isPendingTransaction(): bool` — returns `true` when `trust_account_transaction_id` is null, indicating this approval has not yet been posted to a transaction

## Common Usage

```php
// All pending approvals for a trust account
$pending = TrustApproval::where('trust_account_id', $account->id)
    ->pending()
    ->with('trustElements')
    ->get();

// Check pending status
if ($approval->isPendingTransaction()) {
    // Route to approval review UI
}

// Compute totals (requires trustElements to be loaded)
$approval->load('trustElements');
echo $approval->total_principal_amt; // float, converted from cents
echo $approval->total_income_amt;
echo $approval->total_amt;

// Filter by transaction type for a specific TrustTransactionType
$depositApprovals = TrustApproval::forTrustTransactionType($depositType)->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
