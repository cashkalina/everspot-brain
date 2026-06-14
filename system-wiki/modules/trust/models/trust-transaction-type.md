---
model: TrustTransactionType
module: Trust
table: trust_transaction_types
connection: tenant
primary_source: modules/Trust/Models/TrustTransactionType.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Trust/Casts/TransactionTypeFieldConfigCast.php
  - modules/Trust/Models/TrustApplicationStrategy.php
traits: []
related_models: [TrustApplicationStrategy]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, trust, admin]
---

# TrustTransactionType

## Overview

`TrustTransactionType` is a configuration model that defines the types of transactions allowed against a trust account — for example, "Deposit," "Withdrawal," "Income Distribution," or "Fee." Each type encodes three JSON configuration objects: `principal_config`, `income_config`, and `period_config`. These control what fields are required, optional, or read-only when a transaction of this type is being created, and supply the validation rules used in the UI.

Each type also references up to two `TrustApplicationStrategy` records: one for how principal amounts are applied (spread and weighted across elements) and one for income amounts. The boolean flags `block_principal_application` and `block_income_application` can disable application entirely for one or both fund classes. The `natural_sign` column (cast to the `NaturalSign` enum) indicates whether this type represents a credit or debit in the trust ledger.

The `is_active` flag controls whether the type is available for new transactions. The `canProcessAutomatic` method provides a hard-coded guard: only the type named `"Deposit"` can auto-process deposits, and only `"Withdrawal"` can auto-process withdrawals — ensuring that automatic processing flows can't be inadvertently enabled on custom types.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Transaction type name (e.g., "Deposit", "Withdrawal") |
| description | text | Yes | - | Human-readable description |
| principal_application_strategy_id | bigint | Yes | - | FK → trust_application_strategies: strategy for applying principal amounts |
| income_application_strategy_id | bigint | Yes | - | FK → trust_application_strategies: strategy for applying income amounts |
| natural_sign | varchar | No | - | Credit or debit sign for ledger (cast to `NaturalSign` enum) |
| principal_config | json | No | - | Principal field configuration (deserialized via TransactionTypeFieldConfigCast) |
| income_config | json | No | - | Income field configuration (deserialized via TransactionTypeFieldConfigCast) |
| period_config | json | No | - | Period field configuration (deserialized via TransactionTypeFieldConfigCast) |
| block_principal_application | tinyint | No | 0 | If true, disables principal-application processing for this type |
| block_income_application | tinyint | No | 0 | If true, disables income-application processing for this type |
| is_active | tinyint | No | 1 | Whether this type is available for new transactions |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `principal_application_strategy_id` → `trust_application_strategies.id`; `income_application_strategy_id` → `trust_application_strategies.id`

**Indexes:** `pas_id` on `principal_application_strategy_id`; `ias_id` on `income_application_strategy_id`.

## Casts

- `natural_sign` → `NaturalSign::class` — cast to `Modules\Trust\Enums\NaturalSign` enum
- `principal_config` → `TransactionTypeFieldConfigCast::class` — deserializes JSON to a typed config object with validation support
- `income_config` → `TransactionTypeFieldConfigCast::class` — deserializes JSON to a typed config object with validation support
- `period_config` → `TransactionTypeFieldConfigCast::class` — deserializes JSON to a typed config object with validation support
- `block_principal_application` → `'boolean'`
- `block_income_application` → `'boolean'`
- `is_active` → `'boolean'`

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

_None._

## Relationships

- `principalApplicationStrategy()` — belongs to [TrustApplicationStrategy](./trust-application-strategy.md) (`principal_application_strategy_id`): the strategy used to spread and weight principal application across elements
- `incomeApplicationStrategy()` — belongs to [TrustApplicationStrategy](./trust-application-strategy.md) (`income_application_strategy_id`): the strategy used to spread and weight income application across elements

## Scopes

- `allowsApplicationForType(Builder $query, string $type): void` — constrains the query to types where application is allowed for the given fund class (`'principal'` filters to `block_principal_application = false`; `'income'` filters to `block_income_application = false`)

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getConfigRules(string $config, string $rules = ''): string` — builds a pipe-separated Laravel validation rule string from the validation entries of the named config field (`'principal_config'`, `'income_config'`, or `'period_config'`); used by form request validation
- `canProcessAutomatic(TransactionType $type): bool` — hard-coded guard: returns `true` only when this type's `name` is `'Deposit'` for `TransactionType::DEPOSIT` or `'Withdrawal'` for `TransactionType::WITHDRAWAL`; prevents automatic processing from running against custom types

## Common Usage

```php
// Get all active transaction types
$types = TrustTransactionType::where('is_active', true)->get();

// Get the deposit type
$depositType = TrustTransactionType::where('name', 'Deposit')->first();

// Check if auto-processing is allowed
if ($depositType->canProcessAutomatic(TransactionType::DEPOSIT)) {
    // Run automatic deposit processing
}

// Get validation rules for the principal config
$rules = $depositType->getConfigRules('principal_config');
// e.g., "required|numeric|min:0"

// Check application blocking
if (!$type->block_principal_application) {
    // Principal application is allowed for this type
}

// Fetch types that allow income application
$incomeTypes = TrustTransactionType::allowsApplicationForType('income')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
