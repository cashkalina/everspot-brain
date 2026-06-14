---
model: GlAccount
module: Accounting
table: gl_accounts
connection: tenant
primary_source: modules/Accounting/Models/GlAccount.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Accounting/Observers/GlAccountObserver.php
  - modules/Accounting/Providers/AccountingServiceProvider.php
  - modules/Product/Models/Product.php
traits:
  - HasFactory
  - HasSchemalessAttributes
  - HasSyncables
related_models: [GlAccount, Product]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, accounting, integration]
---

# GlAccount

## Overview

The `GlAccount` model represents a General Ledger (G/L) account in Everspot's accounting subsystem. G/L accounts are the chart-of-accounts entries that classify every financial transaction posted through the system — for example, a revenue account for cemetery lot sales or an expense account for maintenance costs.

Each account has a human-readable `name`, an optional alphanumeric `code` (used by many accounting systems for classification), and a `type` that categorizes the account (asset, liability, equity, revenue, expense, etc.). Accounts can be marked inactive (`is_active = false`), and the `inactivation_required` flag is set automatically by the observer when an account is deactivated, triggering a background job that migrates any associated records to the `backup_gl_account_id` fallback.

`GlAccount` integrates with Everspot's external-accounting-integration layer (QuickBooks and similar) via `HasSyncables`, which links account records to their counterparts in the external system. The `isFromCurrentSystem()` method checks whether a given account belongs to the currently active accounting integration. Product records are associated to G/L accounts through a polymorphic many-to-many `accountable` pivot, allowing each product to carry an account assignment with a `type` qualifier.

A global scope applied in `boot()` orders all queries by `code` (NULLs last), then alphabetically by `name`, giving a predictable chart-of-accounts ordering throughout the UI.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| type | varchar | Yes | - | Account type (e.g. asset, liability, revenue, expense) |
| name | varchar | No | - | Human-readable account name |
| code | varchar | Yes | - | Alphanumeric account code; used for external-system mapping |
| is_active | tinyint | No | 1 | Whether the account is active |
| inactivation_required | tinyint | No | 0 | Set `true` when deactivated; triggers `HandleGlAccountInactivation` job |
| backup_gl_account_id | bigint | Yes | - | FK → gl_accounts; fallback account when this one is inactivated |
| config_data | json | Yes | - | Arbitrary key-value config (via [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `backup_gl_account_id` → `gl_accounts.id`

**Indexes:** FK-backing index on `backup_gl_account_id`; primary key on `id`.

## Casts

- `is_active` → `boolean`
- `inactivation_required` → `boolean`

<!-- trait-contributed casts (e.g. from HasSchemalessAttributes) are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['type', 'name', 'code', 'is_active', 'backup_gl_account_id', 'config_data']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ — `is_active` defaults to `1` and `inactivation_required` to `0` at the database level.

## Accessors & Mutators

- `getSelectFieldNameAttribute(): string` — returns the result of `getModelFullTitle()` for use in select/autocomplete fields

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook; wired to `GlAccountFactory` via `newFactory()`
- [HasSchemalessAttributes](../../../system/traits/index.md#hasschemalessattributes) — `config_data` JSON column with dot-notation access for arbitrary key-value configuration
- [HasSyncables](../../../system/traits/index.md#hassyncables) — links each G/L account to its counterpart in an external accounting integration (e.g. QuickBooks)

## Relationships

- `products()` — morphedByMany [Product](../../product/models/product.md) via `accountable` (pivot `type`): products assigned to this G/L account
- `backupGlAccount()` — belongs to [GlAccount](./gl-account.md) (`backup_gl_account_id`): the fallback account to use when this one is inactivated

## Scopes

- **Global scope `order`** (applied in `boot()`) — orders all queries by `code IS NULL` ascending (non-null codes first), then `code` ascending, then `name` ascending; provides consistent chart-of-accounts ordering

## Events

_None defined on the model._ The `created` lifecycle event is handled by `GlAccountObserver`, which dispatches `GlAccountCreated` (see Observers).

## Observers

- `GlAccountObserver` — registered in `AccountingServiceProvider::registerObservers()` (`GlAccount::observe(GlAccountObserver::class)`). Handles:
  - `saved` — when `is_active` changes to `false` and `inactivation_required` is not already set, sets `inactivation_required = true` and re-saves; when `is_active` changes back to `true` and `inactivation_required` is set, clears it and re-saves; if `inactivation_required` is `true` and a `backup_gl_account_id` is set, dispatches `HandleGlAccountInactivation` job
  - `created` — dispatches `GlAccountCreated` event

## Key Methods

- `getModelIdentifier(): ?string` — returns `$this->code`; used by framework conventions for display/logging
- `getModelFullTitle(): ?string` — returns the model's display title (delegates to `getModelTitle()`)
- `isFromCurrentSystem(): bool` — returns `true` if this account has a syncable linking it to the currently active accounting integration and type `'Account'`

## Common Usage

```php
// Retrieve active accounts in chart-of-accounts order (global scope applied automatically)
$accounts = GlAccount::where('is_active', true)->get();

// Find an account by code
$revenue = GlAccount::where('code', '4000')->first();

// Assign a product to a GL account
$product->glAccounts()->attach($glAccount->id, ['type' => 'income']);

// Check if an account exists in the external accounting system
if ($glAccount->isFromCurrentSystem()) {
    // account is synced to QuickBooks / current integration
}

// Access config values
$glAccount->config_data->someKey;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
