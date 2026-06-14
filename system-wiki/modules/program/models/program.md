---
model: Program
module: Program
table: programs
connection: tenant
primary_source: modules/Program/Models/Program.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Program/Observers/ProgramObserver.php
  - modules/Program/Providers/ProgramServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Accounting/Models/GlAccount.php
  - modules/Product/Models/Product.php
  - modules/Program/Models/ProgramPreferenceCollection.php
traits:
  - HasByUserFields
  - HasMoneyFields
  - LogsActivity
  - HasExternalIds
  - HasIcon
  - HasModelDefinition
  - HasModificationRules
  - Repeatable
related_models: [Cemetery, GlAccount, Product, ProgramPreferenceCollection]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, contract, program]
---

# Program

## Overview

The Program model defines a recurring-service offering that a cemetery can sell to customers — typically a pre-need or at-need service program (e.g., a perpetual care or grounds-maintenance plan). A program is the configuration template: it holds the pricing structure (`payment_amt`, `obligation_price`, `obligation_cost`), scheduling defaults (payment and obligation delay days, `inherit_payment_schedule`, `inherit_obligation_schedule`), obligation metadata (`obligation_name`, `obligation_due_after_days`, `obligation_completed`), and the repeating-record generation configuration (`record_generation`). When a customer enrolls, a [ProgramEnrollment](./program-enrollment.md) is created from this template.

Programs are typed using the `Type` enum (`regular` or `perpetual`), scoped to one or more cemeteries through a many-to-many relationship, and linked to a parent [Product](../../product/models/product.md) for catalog integration. Money columns (`payment_amt`, `obligation_price`, `obligation_cost`, `min_balance`, `max_balance`) are stored as integer cents and transparently converted via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields). Repeating-record schedules are managed via [Repeatable](../../../system/traits/index.md#repeatable), with two named repetition groups (`payment` and `obligation`). General ledger accounts are associated polymorphically via `glAccounts()` (morph-to-many through `GlAccount`), with a convenience method to retrieve the designated liability account.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| type | varchar | No | - | Program type (`regular` or `perpetual`) — cast to `Type` enum |
| product_id | bigint | No | - | FK → products: linked product in the catalog |
| name | varchar | No | - | Display name of the program |
| description | text | Yes | - | Long-form description |
| payment_amt | int | Yes | - | Default payment amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| record_generation | json | Yes | - | Configuration for automated record generation |
| obligation_price | int | Yes | - | Default obligation sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| obligation_cost | int | Yes | - | Default obligation cost in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| min_balance | int | Yes | - | Minimum balance threshold in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| max_balance | int | Yes | - | Maximum balance threshold in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| payment_delay_days | int | Yes | - | Days to delay the first payment after enrollment |
| obligation_delay_days | int | Yes | - | Days to delay the first obligation after enrollment |
| inherit_payment_schedule | tinyint | No | 0 | Whether enrollments inherit the program payment schedule |
| inherit_obligation_schedule | tinyint | No | 0 | Whether enrollments inherit the program obligation schedule |
| obligation_name | varchar | No | - | Display name for obligations created from this program |
| obligation_due_after_days | int | No | - | Days after enrollment that an obligation is due |
| obligation_completed | tinyint | No | 0 | Whether the obligation is considered completed by default |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `product_id` → `products.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `product_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `record_generation` → `array`
- `type` → `Type::class` — cast to `Modules\Program\Enums\Type` enum (`regular` / `perpetual`)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['payment_amt', 'obligation_price', 'obligation_cost', 'min_balance', 'max_balance']` — cents-to-dollars conversion via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

- `getSelectFieldNameAttribute(): ?string` — display label for select/autocomplete fields (delegates to `getModelFullTitle()`)

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backing the `created_by` / `updated_by` / `deleted_by` columns
- [HasExternalIds](../../../system/traits/index.md#hasexternalids) — polymorphic external identifier storage (inherited via BaseModel)
- [HasIcon](../../../system/traits/index.md#hasicon) — Bootstrap Icon class lookup for this model type (inherited via BaseModel)
- [HasModelDefinition](../../../system/traits/index.md#hasmodeldefinition) — resolves the `ModelDefinition` instance for this model (inherited via BaseModel)
- [HasModificationRules](../../../system/traits/index.md#hasmodificationrules) — lifecycle gate: `canBeEdited()`, `canBeDeleted()`, etc. (inherited via BaseModel)
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `payment_amt`, `obligation_price`, `obligation_cost`, `min_balance`, `max_balance`
- [LogsActivity](../../../system/traits/index.md#logsactivity) — auto-logs create/update/delete events via Spatie Activitylog (inherited via BaseModel)
- [Repeatable](../../../system/traits/index.md#repeatable) — recurrence scheduling via polymorphic `Repetition` model; two named groups: `payment` (single repetition) and `obligation` (single repetition)

## Relationships

- `cemeteries()` — belongs-to-many [Cemetery](../../common/models/cemetery.md): the cemeteries that offer this program
- `programPreferenceCollections()` — has many [ProgramPreferenceCollection](./program-preference-collection.md): preference-collection templates defined for this program
- `glAccounts()` — morph-to-many [GlAccount](../../accounting/models/gl-account.md) via `accountable` (pivot `type`): general ledger accounts associated with this program
- `product()` — belongs to [Product](../../product/models/product.md): the catalog product linked to this program

## Scopes

- `forCemetery($query, $cemeteryId)` — filters programs to those associated with the given `cemetery_id` via the `cemeteries` relationship

## Events

_None defined on the model._ Lifecycle events are dispatched by `ProgramObserver` (see Observers).

## Observers

- `ProgramObserver` — registered in `ProgramServiceProvider::registerObservers()` (`Program::observe(ProgramObserver::class)`). Handles:
  - `created` — dispatches `ProgramCreated` event
  - `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs (present but empty)

## Key Methods

- `liabilityAccount()` — retrieves the single GL account associated with this program whose pivot `type = 'liability'`; uses `glAccounts()->withPivot('type')->wherePivot('type', 'liability')->first()`
- `registerRepetitionGroups(): void` — registers the two named repetition groups for this model: `payment` (single repetition) and `obligation` (single repetition), required by the [Repeatable](../../../system/traits/index.md#repeatable) contract

## Common Usage

```php
// Create a perpetual care program
$program = Program::create([
    'type'                      => 'perpetual',
    'product_id'                => $product->id,
    'name'                      => 'Perpetual Care Plan',
    'payment_amt'               => 50000,   // stored as cents
    'obligation_price'          => 20000,
    'obligation_cost'           => 15000,
    'obligation_name'           => 'Annual Grounds Maintenance',
    'obligation_due_after_days' => 365,
]);

// Associate with cemeteries
$program->cemeteries()->sync([$cemetery->id]);

// Retrieve the liability GL account
$liabilityAccount = $program->liabilityAccount();

// Filter programs for a specific cemetery
$cemPrograms = Program::forCemetery($cemetery->id)->get();

// Access preference-collection templates
$collections = $program->programPreferenceCollections;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
