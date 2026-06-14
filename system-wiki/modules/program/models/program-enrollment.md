---
model: ProgramEnrollment
module: Program
table: program_enrollments
connection: tenant
primary_source: modules/Program/Models/ProgramEnrollment.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Program/Observers/ProgramEnrollmentObserver.php
  - modules/Program/Providers/ProgramServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Customer/Models/Customer.php
  - modules/Accounting/Models/GlAccount.php
  - modules/Product/Models/Product.php
  - modules/Program/Models/Program.php
  - modules/Program/Models/ProgramObligation.php
traits:
  - HasByUserFields
  - HasDateStatusFields
  - HasMoneyFields
  - HasRecognition
  - HasTrusting
  - Repeatable
related_models: [Cemetery, Customer, GlAccount, Product, Program, ProgramObligation]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, contract, program, customer]
---

# ProgramEnrollment

## Overview

The ProgramEnrollment model records an individual customer's enrollment in a [Program](./program.md). It is the operational instantiation of a program template for a specific customer at a specific cemetery: it captures the enrollment and disenrollment dates, the status (`active` / `inactive`), all financial figures (sale price, obligation price/cost, balance tracking, AR paid amount), and scheduling/fulfillment dates contributed by the [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) trait (sale, constructive, delivery, cancellation, certificate issuance, and PIF dates).

Each enrollment has a parent program (its configuration template) and belongs to a customer and a cemetery. Obligations are generated from the enrollment as [ProgramObligation](./program-obligation.md) records — one or more per enrollment depending on the recurrence schedule. The enrollment is linked to a catalog product, and its GL accounts are managed polymorphically via the `glAccounts()` morph-to-many relationship (the liability account is attached automatically by `ProgramEnrollmentObserver` on `created`).

The enrollment participates in the Recognition and Trust module workflows via [HasRecognition](../../../system/traits/index.md#hasrecognition) and [HasTrusting](../../../system/traits/index.md#hastrusting), with their per-enrollment configurations stored in the `recognition_config` and `trusting_config` JSON columns. Repeating-record schedules (payment and obligation groups) are managed via [Repeatable](../../../system/traits/index.md#repeatable). Money columns are stored as integer cents and transparently converted via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| program_id | bigint | No | - | FK → programs: the program template this enrollment is based on |
| customer_id | bigint | No | - | FK → customers: the enrolled customer |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery administering this enrollment |
| product_id | bigint | No | - | FK → products: the catalog product for this enrollment |
| status | varchar | No | - | Enrollment status (`active` or `inactive`) |
| payment_amt | int | No | - | Payment amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| sale_price | int | No | - | Total sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| cost_price | int | Yes | - | Cost price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| record_generation | json | Yes | - | Configuration for automated record generation |
| obligation_name | varchar | No | - | Display name for obligations created from this enrollment |
| obligation_due_after_days | int | No | - | Days after enrollment that obligations are due |
| obligation_completed | tinyint | No | 0 | Whether obligations are considered completed by default |
| obligation_special_notes | text | Yes | - | Special notes for obligations |
| obligation_price | int | No | - | Obligation sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| obligation_cost | int | No | - | Obligation cost in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| min_balance | int | Yes | - | Minimum balance threshold in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| max_balance | int | Yes | - | Maximum balance threshold in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| payments_total | int | Yes | - | Running total of payments received in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| obligations_total | int | Yes | - | Running total of obligation amounts in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| balance | int | Yes | - | Current balance in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| enrollment_date | date | No | - | Date the customer enrolled (set automatically to `now()` on creating by observer) |
| disenrollment_date | date | Yes | - | Date the customer disenrolled |
| recognition_config | json | Yes | - | Recognition module configuration for this enrollment (via [HasRecognition](../../../system/traits/index.md#hasrecognition) — see trait doc) |
| trusting_config | json | Yes | - | Trust module configuration for this enrollment (via [HasTrusting](../../../system/traits/index.md#hastrusting) — see trait doc) |
| sale_date | date | Yes | - | Sale date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| constructive_date | date | Yes | - | Constructive delivery date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| delivery_date | date | Yes | - | Delivery date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| cancellation_date | date | Yes | - | Cancellation date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| certificate_issuance_date | date | Yes | - | Certificate issuance date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| pif_date | date | Yes | - | Paid-in-full date (via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — see trait doc) |
| ar_paid_amt | int | No | 0 | AR paid amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `program_id` → `programs.id`; `customer_id` → `customers.id`; `cemetery_id` → `cemeteries.id`; `product_id` → `products.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `program_enrollments_status_index` on `status`; `program_enrollments_sale_date_index` on `sale_date`; `program_enrollments_constructive_date_index` on `constructive_date`; `program_enrollments_delivery_date_index` on `delivery_date`; `program_enrollments_cancellation_date_index` on `cancellation_date`; `program_enrollments_certificate_issuance_date_index` on `certificate_issuance_date`; `program_enrollments_pif_date_index` on `pif_date`; FK-backing indexes on `program_id`, `customer_id`, `cemetery_id`, `product_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `enrollment_date` → `date`
- `disenrollment_date` → `date`
- `record_generation` → `array`
- `recognition_config` → `array`
- `trusting_config` → `array`
- `sale_date` → `date`
- `constructive_date` → `date`
- `delivery_date` → `date`
- `cancellation_date` → `date`
- `certificate_issuance_date` → `date`
- `pif_date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ — `status` defaults to `'active'` via `protected static $defaultStatus = 'active'`.

**Constants / static config:**
```php
const STATUSES = [
    'active'   => ['label' => 'Active',   'color' => 'success'],
    'inactive' => ['label' => 'Inactive', 'color' => 'secondary'],
];

protected static $defaultStatus = 'active';
```

**Money attributes:** `$moneyAttributes = ['payment_amt', 'sale_price', 'obligation_price', 'obligation_cost', 'min_balance', 'max_balance', 'payments_total', 'obligations_total', 'balance', 'ar_paid_amt']` — cents-to-dollars conversion via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backing the `created_by` / `updated_by` / `deleted_by` columns
- [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — date-driven fulfillment status from the sale/constructive/delivery/cancellation/certificate issuance/PIF date columns; scopes `open()` and `notCanceled()`
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for all money columns
- [HasRecognition](../../../system/traits/index.md#hasrecognition) — Recognition module integration: polymorphic `RecognitionArrangement`/`RecognitionElement` relationships; config stored in `recognition_config`
- [HasTrusting](../../../system/traits/index.md#hastrusting) — Trust module integration: polymorphic `TrustArrangement`/`TrustElement` relationships; config stored in `trusting_config`
- [Repeatable](../../../system/traits/index.md#repeatable) — recurrence scheduling via polymorphic `Repetition` model; two named groups: `payment` (single repetition) and `obligation` (single repetition)

## Relationships

- `program()` — belongs to [Program](./program.md) (`program_id`): the program template this enrollment is based on
- `customer()` — belongs to [Customer](../../customer/models/customer.md) (`customer_id`): the enrolled customer
- `product()` — belongs to [Product](../../product/models/product.md) (`product_id`): the catalog product for this enrollment
- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery administering this enrollment
- `programObligations()` — has many [ProgramObligation](./program-obligation.md): obligations generated for this enrollment
- `glAccounts()` — morph-to-many [GlAccount](../../accounting/models/gl-account.md) via `accountable` (pivot `type`): general ledger accounts associated with this enrollment

## Scopes

Date-status scopes (`open()`, `notCanceled()`) are contributed by [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) (see trait doc).

## Events

_None defined on the model._ Lifecycle events are dispatched by `ProgramEnrollmentObserver` (see Observers). On `created`, the observer dispatches `ProgramEnrollmentCreated`, which triggers `CreateTrustArrangementForEnrollment` via the module's `EventServiceProvider`.

## Observers

- `ProgramEnrollmentObserver` — registered in `ProgramServiceProvider::registerObservers()` (`ProgramEnrollment::observe(ProgramEnrollmentObserver::class)`). Handles:
  - `creating` — sets `enrollment_date` to `now()` and copies `payment_amt` to `sale_price`
  - `created` — dispatches `ProgramEnrollmentCreated` event; attaches the program's liability GL account to the enrollment via `glAccounts()->attach()`
  - `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs (present but empty)

## Key Methods

- `liabilityAccount()` — retrieves the single GL account associated with this enrollment whose pivot `type = 'liability'`; uses `glAccounts()->withPivot('type')->wherePivot('type', 'liability')->first()`
- `registerRepetitionGroups(): void` — registers the two named repetition groups: `payment` (single repetition) and `obligation` (single repetition), required by the [Repeatable](../../../system/traits/index.md#repeatable) contract
- `getRecognitionEntity(): Customer` — returns the [Customer](../../customer/models/customer.md) for the Recognition module (required by the [HasRecognition](../../../system/traits/index.md#hasrecognition) contract)

## Common Usage

```php
// Enroll a customer in a program
$enrollment = ProgramEnrollment::create([
    'program_id'               => $program->id,
    'customer_id'              => $customer->id,
    'cemetery_id'              => $cemetery->id,
    'product_id'               => $product->id,
    'payment_amt'              => 50000,   // cents
    'obligation_price'         => 20000,
    'obligation_cost'          => 15000,
    'obligation_name'          => 'Annual Service',
    'obligation_due_after_days'=> 365,
]);
// Observer sets enrollment_date = now(), sale_price = payment_amt, attaches liability GL account

// Check status
$active = ProgramEnrollment::where('status', 'active')->get();

// Access obligations
$obligations = $enrollment->programObligations;

// Access the enrolled customer
$customer = $enrollment->customer;

// Access the liability GL account
$liabilityAccount = $enrollment->liabilityAccount();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
