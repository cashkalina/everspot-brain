---
model: Opportunity
module: Opportunity
table: opportunities
connection: tenant
primary_source: modules/Opportunity/Models/Opportunity.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Opportunity/Observers/OpportunityObserver.php
  - modules/Opportunity/Providers/OpportunityServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/User.php
  - modules/Customer/Models/Customer.php
traits:
  - HasByUserFields
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasMoneyFields
  - HasSearch
  - SoftDeletes
related_models: [Cemetery, Customer, ListOption, Note, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [customer, admin]
---

# Opportunity

## Overview

The Opportunity model represents a sales lead or potential deal in the Everspot CRM. It connects a cemetery, a customer, and a structured pipeline with stage, type, source, and order-type classifications — all driven by `ListOption` reference data. Each opportunity has a title, description, amount (`amt`), probability percentage, and auto-computed `expected_revenue` (probability × amount, kept in sync by the observer).

Opportunities carry a lifecycle status (`open`, `on-hold`, `closed`) that the observer derives automatically from the stage: if the stage name contains "Closed" the status becomes `closed`; "On Hold" → `on-hold`; otherwise `open`. The `date` column marks the opportunity creation date; `closing_date` records the target or actual close date.

Money columns (`amt`, `expected_revenue`) are stored in cents and handled transparently by the `HasMoneyFields` trait. The model also participates in Spatie MediaLibrary file attachments (via `HasFiles`), search indexing (`HasSearch`), user-facing record numbering (`HasModelNumbering`), audit user stamps (`HasByUserFields`), a model factory (`HasFactory`), and soft deletes (`SoftDeletes`).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| cemetery_id | bigint | No | - | FK → cemeteries: the cemetery this opportunity belongs to |
| order_type_id | bigint | Yes | - | FK → list_options: order type classification |
| customer_id | bigint | No | - | FK → customers: the associated customer |
| type_id | bigint | No | - | FK → list_options: opportunity type |
| source_id | bigint | No | - | FK → list_options: lead source |
| stage_id | bigint | No | - | FK → list_options: pipeline stage (drives status via observer) |
| model_no | varchar | Yes | - | User-facing opportunity number (unique; via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| date | date | No | - | Opportunity creation/entry date |
| status | varchar | No | - | Lifecycle status (`open`, `on-hold`, `closed`; managed by observer from stage) |
| title | varchar | No | - | Opportunity title |
| description | text | Yes | - | Optional longer description |
| amt | int | No | - | Deal amount in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — see trait doc) |
| probability | decimal | No | - | Close probability (0–100 percentage) |
| expected_revenue | int | No | - | Computed: `probability × amt` in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — kept in sync by observer) |
| next_step | varchar | Yes | - | Free-text next action |
| closing_date | date | Yes | - | Target or actual close date |
| owner_id | bigint | No | - | FK → users: the user who owns this opportunity |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `customer_id` → `customers.id`; `order_type_id`, `type_id`, `source_id`, `stage_id` → `list_options.id`; `owner_id`, `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `cemetery_id`, `customer_id`, `order_type_id`, `source_id`, `stage_id`, `status`, `title`, `type_id` (single-column); `model_no` (unique); FK-backing indexes on `owner_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `date`
- `closing_date` → `date`

<!-- trait-contributed casts (money attribute conversion) are documented in HasMoneyFields trait doc -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ — `status` defaults to `open` at runtime via `BaseModel::handleDefaultStatus()` on creating (`protected static $defaultStatus = 'open'`).

**Money attributes** (via `HasMoneyFields`):
```php
public $moneyAttributes = ['amt', 'expected_revenue'];
```

**Constants / static config:**
```php
const STATUSES = [
    'open'    => ['label' => 'Open',    'color' => 'success'],
    'on-hold' => ['label' => 'On Hold', 'color' => 'warning'],
    'closed'  => ['label' => 'Closed',  'color' => 'secondary'],
];

protected static $defaultStatus = 'open';
```

## Accessors & Mutators

- `getOrderTypeAttribute(): ?string` — name of the related `orderTypeOption` [ListOption](../../common/models/list-option.md) (the order type label)
- `getTypeAttribute(): ?string` — name of the related `typeOption` [ListOption](../../common/models/list-option.md) (the opportunity type label)
- `getSourceAttribute(): ?string` — name of the related `sourceOption` [ListOption](../../common/models/list-option.md) (the lead source label)
- `getStageAttribute(): ?string` — name of the related `stageOption` [ListOption](../../common/models/list-option.md) (the pipeline stage label; used by the observer to derive status)

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backed by the `created_by` / `updated_by` / `deleted_by` columns
- [HasFactory](../../../system/traits/index.md#hasfactory) — wires the custom `OpportunityFactory` via `newFactory()` for model factories
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments (the model implements `HasMedia`) for opportunity documents and attachments
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` for each opportunity
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `amt` and `expected_revenue`; `formatMoney()`, `fromCents()`, `toCents()` helpers
- [HasSearch](../../../system/traits/index.md#hassearch) — Laravel Scout search indexing for opportunities
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — opportunities are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery this opportunity is associated with
- `customer()` — belongs to [Customer](../../customer/models/customer.md) (`customer_id`): the customer prospect
- `owner()` — belongs to [User](../../common/models/user.md) (`owner_id`): the user responsible for this opportunity
- `orderTypeOption()` — belongs to [ListOption](../../common/models/list-option.md) (`order_type_id`): the order type classification
- `typeOption()` — belongs to [ListOption](../../common/models/list-option.md) (`type_id`): the opportunity type
- `sourceOption()` — belongs to [ListOption](../../common/models/list-option.md) (`source_id`): the lead source
- `stageOption()` — belongs to [ListOption](../../common/models/list-option.md) (`stage_id`): the pipeline stage
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): notes attached to this opportunity

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle behaviour is handled by `OpportunityObserver` (see Observers).

## Observers

- `OpportunityObserver` — registered in `OpportunityServiceProvider::registerObservers()` (`Opportunity::observe(OpportunityObserver::class)`). Handles:
  - `saving` — (1) if `stage_id` has changed, derives `status` from the stage name (contains "Closed" → `closed`; contains "On Hold" → `on-hold`; otherwise `open`); (2) if both `probability` and `amt` are numeric, recomputes `expected_revenue = probability × amt`
  - `created` — fires `analytics()->track('Opportunity Created')`
  - `deleting` — wraps deletion in a DB transaction, runs `PreDeleteOpportunity` action

## Key Methods

- `getModelInferredName(): ?string` — returns `$this->title`; used by `BaseModel` to generate human-readable titles for UI display and logging

## Common Usage

```php
// Create an opportunity
$opportunity = Opportunity::create([
    'cemetery_id'  => $cemetery->id,
    'customer_id'  => $customer->id,
    'owner_id'     => $user->id,
    'type_id'      => $typeOption->id,
    'source_id'    => $sourceOption->id,
    'stage_id'     => $stageOption->id,
    'title'        => 'Pre-need Mausoleum Interest',
    'date'         => today(),
    'amt'          => 500000, // $5,000.00 in cents
    'probability'  => 40,
    // expected_revenue computed by observer: 40 × 500000 = 200000
]);

// Move to a new stage — observer updates status automatically
$opportunity->update(['stage_id' => $closedStageOption->id]);
echo $opportunity->fresh()->status; // 'closed'

// Query open opportunities for a customer
$open = Opportunity::where('customer_id', $customer->id)
    ->where('status', 'open')
    ->get();

// Access money in dollars (via HasMoneyFields)
echo $opportunity->amt;              // 5000.00
echo $opportunity->expected_revenue; // 2000.00

// Attach a note
$opportunity->notes()->create(['content' => 'Spoke with customer about pricing.']);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
