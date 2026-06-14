---
model: ProgramObligation
module: Program
table: program_obligations
connection: tenant
primary_source: modules/Program/Models/ProgramObligation.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Program/Observers/ProgramObligationObserver.php
  - modules/Program/Providers/ProgramServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Customer/Models/Customer.php
  - modules/Program/Models/ProgramEnrollment.php
  - modules/Program/Models/ProgramObligationPreferenceCollection.php
traits:
  - HasByUserFields
  - HasDateStatusFields
  - HasMoneyFields
  - HasRecognition
  - HasTrusting
  - LogsActivity
  - HasExternalIds
  - HasIcon
  - HasModelDefinition
  - HasModificationRules
related_models: [Cemetery, Customer, ProgramEnrollment, ProgramObligationPreferenceCollection]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, contract, program]
---

# ProgramObligation

## Overview

The ProgramObligation model represents a single service obligation arising from a [ProgramEnrollment](./program-enrollment.md). Where a ProgramEnrollment is the customer's enrollment in an ongoing program, an obligation is a discrete, scheduled service event that must be fulfilled within that enrollment — for example, an annual grounds-maintenance visit in a perpetual care program. Obligations carry their own dates, pricing (`sale_price`, `cost_price`, `ar_paid_amt`), and fulfillment tracking dates (sale, constructive, delivery, cancellation, certificate issuance, PIF — via [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields)).

Each obligation belongs to a [ProgramEnrollment](./program-enrollment.md) and is scoped to a cemetery. It may have a linked [ProgramObligationPreferenceCollection](./program-obligation-preference-collection.md) that captures the customer's preference selections for how the obligation is to be fulfilled. Money columns are stored as integer cents and transparently converted via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

The model participates in the Recognition and Trust module workflows via [HasRecognition](../../../system/traits/index.md#hasrecognition) and [HasTrusting](../../../system/traits/index.md#hastrusting), with per-obligation configurations stored in `recognition_config` and `trusting_config`. On creation, `ProgramObligationObserver` dispatches `ProgramObligationCreated`, which triggers trust and recognition arrangement creation via the module's `EventServiceProvider`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| program_enrollment_id | bigint | No | - | FK → program_enrollments: the enrollment this obligation belongs to |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery where this obligation is to be fulfilled |
| date | date | No | - | The scheduled service date for this obligation |
| sale_price | int | No | - | Sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| cost_price | int | No | - | Cost price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| due_date | date | No | - | Date by which the obligation must be fulfilled |
| recognition_config | json | Yes | - | Recognition module configuration for this obligation (via [HasRecognition](../../../system/traits/index.md#hasrecognition) — see trait doc) |
| trusting_config | json | Yes | - | Trust module configuration for this obligation (via [HasTrusting](../../../system/traits/index.md#hastrusting) — see trait doc) |
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

**Foreign keys:** `program_enrollment_id` → `program_enrollments.id`; `cemetery_id` → `cemeteries.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `program_obligations_sale_date_index` on `sale_date`; `program_obligations_constructive_date_index` on `constructive_date`; `program_obligations_delivery_date_index` on `delivery_date`; `program_obligations_cancellation_date_index` on `cancellation_date`; `program_obligations_certificate_issuance_date_index` on `certificate_issuance_date`; `program_obligations_pif_date_index` on `pif_date`; FK-backing indexes on `program_enrollment_id`, `cemetery_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `date`
- `due_date` → `date`
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
**Defaults (`$attributes`):** _None._

**Money attributes:** `$moneyAttributes = ['sale_price', 'cost_price', 'ar_paid_amt']` — cents-to-dollars conversion via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backing the `created_by` / `updated_by` / `deleted_by` columns
- [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) — date-driven fulfillment status from the sale/constructive/delivery/cancellation/certificate issuance/PIF date columns; scopes `open()` and `notCanceled()`
- [HasExternalIds](../../../system/traits/index.md#hasexternalids) — polymorphic external identifier storage (inherited via BaseModel)
- [HasIcon](../../../system/traits/index.md#hasicon) — Bootstrap Icon class lookup for this model type (inherited via BaseModel)
- [HasModelDefinition](../../../system/traits/index.md#hasmodeldefinition) — resolves the `ModelDefinition` instance for this model (inherited via BaseModel)
- [HasModificationRules](../../../system/traits/index.md#hasmodificationrules) — lifecycle gate: `canBeEdited()`, `canBeDeleted()`, etc. (inherited via BaseModel)
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `sale_price`, `cost_price`, `ar_paid_amt`
- [HasRecognition](../../../system/traits/index.md#hasrecognition) — Recognition module integration: polymorphic `RecognitionArrangement`/`RecognitionElement` relationships; config stored in `recognition_config`
- [HasTrusting](../../../system/traits/index.md#hastrusting) — Trust module integration: polymorphic `TrustArrangement`/`TrustElement` relationships; config stored in `trusting_config`
- [LogsActivity](../../../system/traits/index.md#logsactivity) — auto-logs create/update/delete events via Spatie Activitylog (inherited via BaseModel)

## Relationships

- `programEnrollment()` — belongs to [ProgramEnrollment](./program-enrollment.md) (`program_enrollment_id`): the enrollment that generated this obligation
- `programObligationPreferenceCollection()` — has one [ProgramObligationPreferenceCollection](./program-obligation-preference-collection.md): the preference-collection instance for this obligation's customer choices

## Scopes

Date-status scopes (`open()`, `notCanceled()`) are contributed by [HasDateStatusFields](../../../system/traits/index.md#hasdatestatusfields) (see trait doc).

## Events

_None defined on the model._ Lifecycle events are dispatched by `ProgramObligationObserver` (see Observers). On `created`, the observer dispatches `ProgramObligationCreated`, which triggers `CreateTrustArrangementForObligation` and `CreateRecArrangementForObligation` via the module's `EventServiceProvider`.

## Observers

- `ProgramObligationObserver` — registered in `ProgramServiceProvider::registerObservers()` (`ProgramObligation::observe(ProgramObligationObserver::class)`). Handles:
  - `created` — dispatches `ProgramObligationCreated` event
  - `updated`, `deleted`, `restored`, `forceDeleted` — no-op stubs (present but empty)

## Key Methods

- `getRecognitionEntity(): Customer` — returns the [Customer](../../customer/models/customer.md) for the Recognition module (required by the [HasRecognition](../../../system/traits/index.md#hasrecognition) contract); traverses `$this->programEnrollment->customer`

## Common Usage

```php
// Access an enrollment's obligations
$obligations = $enrollment->programObligations;

// Filter to open (not cancelled, not delivered) obligations
$openObligations = $enrollment->programObligations()->open()->get();

// Access the preference collection for a specific obligation
$prefCollection = $obligation->programObligationPreferenceCollection;

// Access the parent enrollment and customer
$customer = $obligation->programEnrollment->customer;

// Check fulfillment dates
if ($obligation->delivery_date) {
    echo "Delivered on: {$obligation->delivery_date}";
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
