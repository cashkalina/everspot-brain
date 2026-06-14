---
model: TrustArrangement
module: Trust
table: trust_arrangements
connection: tenant
primary_source: modules/Trust/Models/TrustArrangement.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Trust/Observers/TrustArrangementObserver.php
  - modules/Trust/Providers/TrustServiceProvider.php
  - modules/Trust/Models/TrustAccount.php
  - modules/Trust/Models/TrustElement.php
traits:
  - HasMoneyFields
  - HasSchemalessAttributes
related_models: [TrustAccount, TrustElement]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, contract]
---

# TrustArrangement

## Overview

`TrustArrangement` represents the per-contract trust obligation record — the link between a specific pre-need arrangement (an order, property commitment, or other arrangeable entity) and the trust account holding its funds. It tracks the full lifecycle of one contract's trust activity: the scheduled amount owed, how much has been deposited (incoming) and withdrawn (outgoing), running balances, and all relevant lifecycle dates.

Each `TrustArrangement` is polymorphically related to its owning entity via `trust_arrangeable_type` / `trust_arrangeable_id` (the `trustArrangeable()` morphTo). The `type` column mirrors the trust account type (`merch` or `perpetual-care`). Two status fields, `incoming_status` and `outgoing_status`, track the deposit and withdrawal progress independently through the `INOUTSTATUSES` lifecycle (`not-triggered` → `awaiting-element` → `in-progress` → `completed`).

The arrangement stores the complete trust calculation schedule as a JSON `schedule` column (the rules used to compute the `full_trust_amt`), trigger configurations for when deposits and withdrawals fire (`incoming_trigger`, `outgoing_trigger`), and key date fields copied from the parent arrangeable. The `HasSchemalessAttributes` trait exposes `config_data` for arbitrary key-value configuration (e.g., `trust_req_by_term`, `trust_req_by_start`, delay rules). All money columns are stored in cents and transparently converted by `HasMoneyFields`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| trust_arrangeable_id | bigint | No | - | Polymorphic parent entity ID (FK → arrangeable) |
| trust_arrangeable_type | varchar | No | - | Polymorphic parent entity class |
| trust_account_id | bigint | Yes | - | FK → trust_accounts: the trust account holding funds for this arrangement |
| type | varchar | No | - | Trust type (`merch` or `perpetual-care`) — mirrors the account type |
| incoming_status | varchar | No | - | Deposit status (`not-triggered`, `awaiting-element`, `in-progress`, `completed`) |
| outgoing_status | varchar | Yes | - | Withdrawal status (same lifecycle as incoming_status) |
| incoming_trigger | json | No | - | Configuration for when deposits are triggered |
| outgoing_trigger | json | Yes | - | Configuration for when withdrawals are triggered |
| sale_date | date | Yes | - | Date of sale (synced from parent arrangeable) |
| constructive_date | date | Yes | - | Constructive receipt date (synced from parent) |
| delivery_date | date | Yes | - | Delivery date (via TimezonedDateTime cast; synced from parent) |
| cancellation_date | date | Yes | - | Cancellation date (via TimezonedDateTime cast; synced from parent) |
| certificate_issuance_date | date | Yes | - | Certificate issuance date (via TimezonedDateTime cast; synced from parent) |
| ar_paid_amt | int | No | 0 | Accounts receivable paid amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| trust_req_by_date | date | Yes | - | Date by which trust deposit is required (via TimezonedDateTime cast) |
| sale_price | int | No | 0 | Sale price in cents used in trust amount calculation (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| trust_cost | int | No | 0 | Trust cost in cents used in calculation (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| schedule | json | No | - | Trust calculation schedule configuration (rules for computing full_trust_amt) |
| full_trust_amt | int | Yes | - | Computed full trust obligation amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| deposited_principal | int | No | 0 | Total principal deposited to date in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| deposited_income | int | No | 0 | Total income deposited to date in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| withdrawn_principal | int | No | 0 | Total principal withdrawn to date in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| withdrawn_income | int | No | 0 | Total income withdrawn to date in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| principal_balance | int | No | 0 | Current principal balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| income_balance | int | No | 0 | Current income balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| config_data | json | Yes | - | Schemaless key-value configuration (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `trust_account_id` → `trust_accounts.id`

**Indexes:** composite index `trust_arrangeable_idx` on (`trust_arrangeable_type`, `trust_arrangeable_id`); single-column indexes on `incoming_status`, `outgoing_status`, `sale_date`, `constructive_date`, `delivery_date`, `cancellation_date`, `certificate_issuance_date`, `ar_paid_amt`, `trust_req_by_date`; FK-backing index on `trust_account_id`.

## Casts

- `schedule` → `'array'` — trust calculation schedule decoded as PHP array
- `incoming_trigger` → `'array'` — deposit trigger configuration decoded as PHP array
- `outgoing_trigger` → `'array'` — withdrawal trigger configuration decoded as PHP array
- `sale_date` → `'date'` — sale date as Carbon date
- `delivery_date` → `TimezonedDateTime::class` — delivery date with timezone-aware handling
- `cancellation_date` → `TimezonedDateTime::class` — cancellation date with timezone-aware handling
- `certificate_issuance_date` → `TimezonedDateTime::class` — certificate issuance date with timezone-aware handling
- `trust_req_by_date` → `TimezonedDateTime::class` — required-by date with timezone-aware handling

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['ar_paid_amt', 'sale_price', 'trust_cost', 'deposited_principal', 'withdrawn_principal', 'deposited_income', 'withdrawn_income', 'principal_balance', 'income_balance']` — processed by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

**Constants:**
```php
const INOUTSTATUSES = [
    'not-triggered'   => ['incoming_label' => 'Not Deposited',            'outgoing_label' => 'Not Withdrawn',            'color' => 'warning'],
    'awaiting-element'=> ['incoming_label' => 'Not Deposited',            'outgoing_label' => 'Not Withdrawn',            'color' => 'warning'],
    'in-progress'     => ['incoming_label' => 'Deposit(s) in Progress',   'outgoing_label' => 'Withdrawal(s) in Progress','color' => 'info'],
    'completed'       => ['incoming_label' => 'Deposited',                'outgoing_label' => 'Withdrawn',                'color' => 'success'],
];
```

## Accessors & Mutators

- `getFormattedTypeAttribute(): ?string` — human-readable label for the trust type (`merch` → `'Merchandise/Services'`, `perpetual-care` → `'Perpetual Care'`, unknown → `null`)
- `getOutgoingStatusBadgeAttribute(): string` — HTML Bootstrap badge representing the current withdrawal status
- `getIncomingStatusBadgeAttribute(): string` — HTML Bootstrap badge representing the current deposit status

## Traits

- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for all money columns
- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — dot-notation access to the `config_data` JSON column for flexible configuration (e.g., delay rules, trust_req_by_term)

## Relationships

- `trustArrangeable()` — morphTo: the parent entity this arrangement belongs to (may be an Order, PropertyCommitment, or another arrangeable model)
- `trustAccount()` — belongs to [TrustAccount](./trust-account.md) (`trust_account_id`): the trust account holding funds for this arrangement
- `trustElements()` — has many [TrustElement](./trust-element.md): all element-level deposit/withdrawal records for this arrangement
- `depositElements()` — has many [TrustElement](./trust-element.md) (constrained to `transaction_type = DEPOSIT`): deposit elements only
- `withdrawalElements()` — has many [TrustElement](./trust-element.md) (constrained to `transaction_type = WITHDRAWAL`): withdrawal elements only

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle events are handled by `TrustArrangementObserver` (see Observers).

## Observers

- `TrustArrangementObserver` — registered in `TrustServiceProvider::registerObservers()` (`TrustArrangement::observe(TrustArrangementObserver::class)`). Handles:
  - `saved` — calls `TrustingService::trustArrangementSaved($trustArrangement)` to cascade updates to the parent arrangeable and trigger balance recalculations
  - `created`, `updated`, `deleted`, `restored`, `forceDeleted` — present as stubs with no active logic

## Key Methods

- `updatedTrustArrangeable($model): void` — syncs key date and amount fields from the parent arrangeable model (`sale_date`, `constructive_date`, `delivery_date`, `cancellation_date`, `certificate_issuance_date`, `ar_paid_amt`) and saves if any field changed
- `calculateTrustReqByDate(): void` — computes `trust_req_by_date` based on `config_data->trust_req_by_term` (number of days) and `config_data->trust_req_by_start` (currently only `'sale'` is supported); sets the field if conditions are met
- `calculateFullTrustAmount(): void` — computes `full_trust_amt` from the `schedule` config by summing fixed-dollar, percent-of-revenue, and percent-of-cost components, subject to a minimum total
- `getStatusBadgeByDirection(string $direction): string` — returns an HTML Bootstrap badge for the given direction (`'incoming'` or `'outgoing'`) based on the current status value and `INOUTSTATUSES` labels
- `getDelayDays(string $direction, string $triggerType): int` — reads the delay-days configuration from `config_data` for a given direction and trigger type (defaults to `0`)

## Common Usage

```php
// Load an arrangement with elements and account
$arrangement = TrustArrangement::with(['trustAccount', 'trustElements', 'trustArrangeable'])->find($id);

// Check deposit and withdrawal status
echo $arrangement->incoming_status;         // "in-progress"
echo $arrangement->incoming_status_badge;   // HTML badge
echo $arrangement->outgoing_status_badge;

// Sync dates from the parent model
$arrangement->updatedTrustArrangeable($order);

// Compute the required trust amount
$arrangement->calculateFullTrustAmount();
echo $arrangement->full_trust_amt; // float (cents converted to dollars)

// Compute the required-by date
$arrangement->calculateTrustReqByDate();

// Get delay days from config
$depositDelay = $arrangement->getDelayDays('incoming', 'sale');

// Access deposit and withdrawal elements separately
$deposits    = $arrangement->depositElements;
$withdrawals = $arrangement->withdrawalElements;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
