---
model: TrustAccount
module: Trust
table: trust_accounts
connection: tenant
primary_source: modules/Trust/Models/TrustAccount.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Accounting/Models/GlAccount.php
  - modules/Trust/Models/TrustElement.php
  - modules/Trust/Models/TrustArrangement.php
  - modules/Trust/Models/TrustAccountTransaction.php
  - modules/Trust/Models/TrustApproval.php
traits:
  - HasMoneyFields
  - HasSearch
related_models: [GlAccount, TrustApproval, TrustArrangement, TrustAccountTransaction, TrustElement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, core]
---

# TrustAccount

## Overview

`TrustAccount` represents a cemetery's trust fund account — the financial vehicle used to hold pre-need funds in escrow on behalf of customers. Each account is typed as either a Merchandise/Services trust or a Perpetual Care trust (`merch` or `perpetual-care`), reflecting the two major regulatory categories of cemetery pre-need trust obligations.

The model stores the account's identifying information (name, account name as it appears at the bank, routing/account numbers, bank name) and links to a general-ledger account (`GlAccount`) for accounting integration. A `config_data` JSON column holds flexible account-level configuration that drives downstream behavior such as disbursement rules and schedule defaults.

`TrustAccount` is the root of the trust data hierarchy. Trust arrangements (per-contract escrow tracking), trust elements (individual deposit/withdrawal line items), transaction batches, and pending approvals all hang off a single `TrustAccount`. The `HasSearch` trait makes accounts discoverable in global search, and `HasMoneyFields` provides transparent cents-to-dollars conversion for financial computations.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| gl_account_id | bigint | Yes | - | FK → gl_accounts: linked general-ledger account |
| type | varchar | No | - | Account type (`merch` = Merchandise/Services, `perpetual-care` = Perpetual Care) |
| name | varchar | No | - | Account display name |
| name_on_account | varchar | Yes | - | Name as it appears on the bank account |
| routing_number | varchar | Yes | - | Bank routing number |
| account_number | varchar | Yes | - | Bank account number |
| bank_name | varchar | Yes | - | Name of the financial institution |
| config_data | json | Yes | - | Flexible account-level configuration (disbursement rules, schedule defaults) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `gl_account_id` → `gl_accounts.id`

**Indexes:** FK-backing index on `gl_account_id`.

## Casts

_None declared on the model._ (Money-column conversion is handled by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc.)

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants:**
```php
const TYPES = [
    'merch'          => 'Merchandise/Services',
    'perpetual-care' => 'Perpetual Care',
];
```

## Accessors & Mutators

- `getFormattedTypeAttribute(): string` — human-readable label for the account type, resolved from `TYPES` constant
- `getCurrentBalanceAttribute(): float` — sum of `total_balance` across all related `TrustAccountTransaction` records (computed from already-loaded collection; eager-load `trustAccountTransactions` for efficiency)

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for financial amount columns declared in `$moneyAttributes`
- [HasSearch](../../../system/traits/index.md#hassearch) — indexes this account in global search

## Relationships

- `glAccount()` — belongs to [GlAccount](../../accounting/models/gl-account.md) (`gl_account_id`): the general-ledger account used for double-entry accounting integration
- `trustElements()` — has many [TrustElement](./trust-element.md): all individual trust element records under this account
- `trustArrangements()` — has many [TrustArrangement](./trust-arrangement.md): all per-contract trust arrangements tied to this account
- `trustAccountTransactions()` — has many [TrustAccountTransaction](./trust-account-transaction.md): all posted transaction batches for this account
- `trustApprovals()` — has many [TrustApproval](./trust-approval.md): all pending and processed approval records for this account
- `pendingTransactions()` — has many [TrustApproval](./trust-approval.md) (constrained to `trust_account_transaction_id IS NULL`): approvals not yet matched to a posted transaction

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getFormattedTypeAttribute(): string` — returns the display label for the account type (see Accessors & Mutators)
- `getCurrentBalanceAttribute(): float` — sums `total_balance` over all loaded `trustAccountTransactions` (see Accessors & Mutators)

## Common Usage

```php
// Create a perpetual care trust account
$account = TrustAccount::create([
    'type'            => 'perpetual-care',
    'name'            => 'Perpetual Care Fund',
    'name_on_account' => 'ABC Cemetery PC Trust',
    'bank_name'       => 'First National Bank',
    'routing_number'  => '021000021',
    'account_number'  => '123456789',
    'gl_account_id'   => $glAccount->id,
]);

// Display account type
echo $account->formatted_type; // "Perpetual Care"

// Current balance (load transactions first)
$account->load('trustAccountTransactions');
echo $account->current_balance; // sum of all total_balance in cents (converted by HasMoneyFields)

// All pending approvals
$pending = $account->trustApprovals()->pending()->get();

// All arrangements for this account
$arrangements = $account->trustArrangements()->with('trustElements')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
