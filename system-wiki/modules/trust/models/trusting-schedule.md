---
model: TrustingSchedule
module: Trust
table: trusting_schedules
connection: tenant
primary_source: modules/Trust/Models/TrustingSchedule.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Support/Timezone/Casts/TimezonedDateTime.php
  - modules/Common/Models/Cemetery.php
  - modules/Trust/Models/TrustAccount.php
  - modules/Trust/Models/TrustingScheduleGroup.php
traits:
  - HasSchemalessAttributes
  - HasMoneyFields
related_models: [Cemetery, TrustAccount, TrustingScheduleGroup]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, admin]
---

# TrustingSchedule

## Overview

`TrustingSchedule` defines the rules for how much must be put into trust for a given product or service type — in other words, the "schedule" of trust obligations. Each schedule specifies a trust account to collect into, a type (mirroring the trust account type), an effective date range, and one or more calculation modes: a fixed dollar amount, a percentage of revenue, a percentage of cost, or a custom formula, optionally with a minimum total.

Schedules are organized into groups (`TrustingScheduleGroup`) and can be scoped to specific cemeteries via the `cemeteries()` many-to-many relationship, or left global (`is_global = true`) to apply across all cemeteries. Trigger configurations (`incoming_trigger`, `outgoing_trigger`) control when deposits and withdrawals fire for arrangements created under this schedule. A soft-deleted `deleted_at` column is present in the schema, although the model does not declare `SoftDeletes` in the source — this is likely a migration artifact or legacy column.

The `HasSchemalessAttributes` trait exposes the `config_data` JSON column for arbitrary additional configuration, and `HasMoneyFields` provides cents-to-dollars conversion for the `fixed_dollar` and `min_total` money columns.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| trusting_schedule_group_id | bigint | No | - | FK → trusting_schedule_groups: the group this schedule belongs to |
| name | varchar | No | - | Schedule name |
| type | varchar | No | - | Trust type (`merch` or `perpetual-care`) |
| trust_account_id | bigint | No | - | FK → trust_accounts: the trust account funds are collected into |
| is_global | tinyint | No | 0 | Whether this schedule applies to all cemeteries (overrides cemetery scoping) |
| effective_start_date | date | No | - | Date this schedule becomes effective (via TimezonedDateTime cast) |
| effective_end_date | date | Yes | - | Date this schedule expires, if any (via TimezonedDateTime cast) |
| incoming_trigger | json | Yes | - | Deposit trigger configuration |
| outgoing_trigger | json | Yes | - | Withdrawal trigger configuration |
| custom_incoming_trigger | text | Yes | - | Custom incoming trigger expression (overrides incoming_trigger) |
| custom_outgoing_trigger | text | Yes | - | Custom outgoing trigger expression (overrides outgoing_trigger) |
| enable_custom_calc | tinyint | No | 0 | Whether a custom calculation formula is active |
| custom_calc | text | Yes | - | Custom calculation formula expression |
| enable_fixed_dollar | tinyint | No | 0 | Whether a fixed dollar component is active |
| enable_pct_revenue | tinyint | No | 0 | Whether a percentage-of-revenue component is active |
| enable_pct_cost | tinyint | No | 0 | Whether a percentage-of-cost component is active |
| fixed_dollar | int | Yes | - | Fixed dollar amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| pct_revenue | decimal | Yes | - | Percentage of revenue (as a decimal, e.g., 0.05 for 5%) |
| pct_cost | decimal | Yes | - | Percentage of cost (as a decimal) |
| min_total | int | Yes | - | Minimum total amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| config_data | json | Yes | - | Schemaless additional configuration (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (column present in schema; SoftDeletes not declared in model) |

**Primary key:** `id`

**Foreign keys:** `trusting_schedule_group_id` → `trusting_schedule_groups.id`; `trust_account_id` → `trust_accounts.id`

**Indexes:** FK-backing indexes on `trusting_schedule_group_id`, `trust_account_id`.

## Casts

- `effective_start_date` → `TimezonedDateTime::class` — effective start date with timezone-aware handling
- `effective_end_date` → `TimezonedDateTime::class` — effective end date with timezone-aware handling
- `incoming_trigger` → `'array'` — deposit trigger config decoded as PHP array
- `outgoing_trigger` → `'array'` — withdrawal trigger config decoded as PHP array

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** _None declared_ (inherits from BaseModel; no `$fillable` or `$guarded` override)
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['fixed_dollar', 'min_total']` — processed by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — dot-notation access to the `config_data` JSON column for arbitrary schedule configuration
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `fixed_dollar` and `min_total`

## Relationships

- `trustAccount()` — belongs to [TrustAccount](./trust-account.md) (`trust_account_id`): the trust account this schedule collects funds into
- `trustingScheduleGroup()` — belongs to [TrustingScheduleGroup](./trusting-schedule-group.md) (`trusting_schedule_group_id`): the group organizing this schedule
- `cemeteries()` — belongs-to-many [Cemetery](../../common/models/cemetery.md): the cemeteries this schedule applies to (empty when `is_global = true`)

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None beyond standard Eloquent._

## Common Usage

```php
// All active schedules for a trust account
$schedules = TrustingSchedule::where('trust_account_id', $account->id)
    ->whereNull('deleted_at')
    ->with(['cemeteries', 'trustingScheduleGroup'])
    ->get();

// Global schedules only
$global = TrustingSchedule::where('is_global', true)->get();

// Schedules for a specific cemetery (non-global)
$cemeterySchedules = TrustingSchedule::whereHas('cemeteries', function ($q) use ($cemetery) {
    $q->where('cemeteries.id', $cemetery->id);
})->get();

// Access money fields (converted from cents)
echo $schedule->fixed_dollar; // float in dollars
echo $schedule->min_total;    // float in dollars

// Access schemaless config
$term = $schedule->config_data->trust_req_by_term;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
