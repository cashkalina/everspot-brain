---
model: WorkOrder
module: WorkOrder
table: work_orders
connection: tenant
primary_source: modules/WorkOrder/Models/WorkOrder.php
source_paths:
  - app/Models/BaseModel.php
  - modules/WorkOrder/Observers/WorkOrderObserver.php
  - modules/WorkOrder/Providers/WorkOrderServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/User.php
  - modules/Customer/Models/Customer.php
  - modules/Event/Models/Event.php
  - modules/Interment/Models/Interment.php
  - modules/Memorial/Models/Memorial.php
  - modules/Property/Models/Property.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasExternalApprovals
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasSearch
  - HasTimeEntries
  - Repeatable
  - SoftDeletes
related_models: [Cemetery, Customer, Event, Interment, ListOption, Memorial, Note, Property, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, service, core]
---

# WorkOrder

## Overview

The WorkOrder model represents a work task or maintenance request within the cemetery management system. Work orders capture scheduled or on-demand jobs — from monument repair to grounds maintenance — and are the primary operational record for field and staff work.

Each work order belongs to a cemetery and may be optionally linked to a customer, an interment record, one or more memorials, and one or more properties. This gives work orders the context they need to appear in the right places throughout the UI and in reporting. Work orders are assigned to a single staff user (`assigned_to`) and carry a status (`not-started`, `in-progress`, `completed`, `canceled`) and a priority (`low`, `medium`, `high`), allowing supervisors to triage and track field work.

Work orders support time tracking via the `HasTimeEntries` trait — staff can log individual `TimeEntry` records against a work order, and the total time is aggregated into the `time_spent` column automatically. Work orders also support recurrence scheduling via the `Repeatable` trait, can be templated (`is_template`), and can be shared via a unique `staff_access_key` that allows field staff to view the work order without logging in (exposable as a QR code). The model carries soft deletes, audit user stamps, EAV custom attributes, Spatie media file attachments, model numbering, search indexing, and external-approval flow via traits.

**Constants / static config:**
```php
const STATUSES = [
    'not-started' => ['label' => 'Not Started', 'color' => 'warning'],
    'in-progress'  => ['label' => 'In Progress',  'color' => 'info'],
    'completed'    => ['label' => 'Completed',     'color' => 'success'],
    'canceled'     => ['label' => 'Canceled',      'color' => 'danger'],
];

const PRIORITIES = [
    'low'    => ['label' => 'Low',    'color' => 'info'],
    'medium' => ['label' => 'Medium', 'color' => 'warning'],
    'high'   => ['label' => 'High',   'color' => 'danger'],
];
```

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| cemetery_id | bigint | Yes | - | FK → cemeteries: the cemetery this work order belongs to |
| work_order_category_id | bigint | Yes | - | FK → list_options (type=work_order_category): the work order category |
| customer_id | bigint | Yes | - | FK → customers: optional linked customer |
| interment_id | bigint | Yes | - | FK → interments: optional linked interment |
| date | date | Yes | - | Scheduled date of the work order |
| model_no | varchar | Yes | - | User-facing work order number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| status | varchar | No | - | Current status: `not-started`, `in-progress`, `completed`, `canceled` |
| priority | varchar | Yes | - | Priority level: `low`, `medium`, `high` |
| title | varchar | Yes | - | Short title / subject of the work order |
| description | text | Yes | - | Detailed description of the work to be performed |
| assigned_to | bigint | Yes | - | FK → users: the staff member assigned to this work order |
| due_date | date | Yes | - | Target completion date |
| time_spent | decimal | No | 0.0000 | Total time logged (hours); aggregated from TimeEntry records (via [HasTimeEntries](../../../system/traits/index.md#hastimeentries) — see trait doc) |
| is_template | tinyint | No | 0 | Whether this work order is a reusable template |
| template_name | varchar | Yes | - | Display name for the template (when `is_template = 1`) |
| is_recurring | tinyint | No | 0 | Whether this work order recurs (via [Repeatable](../../../system/traits/index.md#repeatable) — see trait doc) |
| staff_access_key | varchar | Yes | - | Unique key for unauthenticated staff access (used to generate QR codes) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `model_no`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `customer_id` → `customers.id`; `interment_id` → `interments.id`; `assigned_to`, `created_by`, `updated_by`, `deleted_by` → `users.id`. Note: `work_order_category_id` has no DB-level FK constraint in the snapshot (application-level FK to `list_options`).

**Indexes:** single-column indexes on `cemetery_id`, `customer_id`, `interment_id`, `date`, `status`, `title`, `staff_access_key`, `work_order_category_id`; FK-backing indexes on `assigned_to`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `date` → `date` — scheduled work order date
- `due_date` → `date` — target completion date

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getPriorityBadgeAttribute(): ?string` — HTML badge for the work order priority (color/label from `PRIORITIES`); returns `null` if priority is not a known key
- `getFormattedPriorityAttribute(): string` — human-readable priority label (`Low`, `Medium`, `High`); returns `N/A` if unknown
- `getAgeAttribute(): string` — human-readable age of the work order since creation (e.g. `"3 days old"`); returns `"Just created"` if `created_at` is in the future

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for storing dynamic per-work-order fields
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [HasExternalApprovals](../../../system/traits/index.md#hasexternalapprovals) — external approval workflow for work orders requiring sign-off outside the system
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (a custom `WorkOrderFactory` is wired via `newFactory()`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary attachments (the model implements `HasMedia`) for work order photos and documents
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` for work orders
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing for work orders
- [HasTimeEntries](../../../system/traits/index.md#hastimeentries) — polymorphic `timeEntries()` relationship and `calculateTotalTime()` to aggregate `time_spent` from TimeEntry records
- [Repeatable](../../../system/traits/index.md#repeatable) — recurrence scheduling; backs the `is_recurring` column
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — work orders are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md) (`cemetery_id`): the cemetery this work order belongs to
- `workOrderCategory()` — belongs to [ListOption](../../common/models/list-option.md) (`work_order_category_id`, filtered `type=work_order_category`): the work order category
- `category()` — alias for `workOrderCategory()` — belongs to [ListOption](../../common/models/list-option.md): convenience alias for the category relationship
- `customer()` — belongs to [Customer](../../customer/models/customer.md) (`customer_id`): the optional linked customer
- `interment()` — belongs to [Interment](../../interment/models/interment.md) (`interment_id`): the optional linked interment record
- `memorials()` — belongs-to-many [Memorial](../../memorial/models/memorial.md) via `memorial_work_orders`: memorials associated with this work order
- `properties()` — belongs-to-many [Property](../../property/models/property.md) via `property_work_orders`: properties associated with this work order
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): notes attached to the work order
- `events()` — morphMany [Event](../../event/models/event.md) (`eventable`): calendar events linked to the work order
- `assignedTo()` — belongs to [User](../../common/models/user.md) (`assigned_to`): the staff member assigned to this work order

## Scopes

- `open(Builder $query)` — filters to work orders where status is not `completed` or `canceled`, ordered by status
- `templates(Builder $query)` — filters to work orders where `is_template = true`

## Events

- `onCompleted(): void` — dispatches `WorkOrderCompleted` event when called (must be triggered explicitly by calling code, not an Eloquent lifecycle hook)

## Observers

- `WorkOrderObserver` — registered in `WorkOrderServiceProvider::registerObservers()` (`WorkOrder::observe(WorkOrderObserver::class)`). Handles:
  - `saved` — dispatches `WorkOrderAssigned` or `WorkOrderUnassigned` events when the `assigned_to` field changes (via `DispatchEventForAssignmentChanges`); also syncs `cemetery_id` to all linked events
  - `created` — fires `analytics()->track('Work Order Created')`
  - `deleting` — wraps deletion in a DB transaction and runs `PreDeleteWorkOrder` checks

## Key Methods

- `getModelInferredName(): ?string` — returns `$this->title`; used by the model-numbering and definition systems to infer a display name
- `isOpen(): bool` — returns `true` if status is `not-started` or `in-progress`
- `onCompleted(): void` — dispatches the `WorkOrderCompleted` event; call this explicitly when marking a work order complete
- `getQrCodeDataUri(): ?string` — generates a PNG QR code (via `endroid/qr-code`) pointing to the staff access URL for this work order; returns `null` if the work order has no id or `staff_access_key`, or if QR generation fails

## Common Usage

```php
// Create a work order
$workOrder = WorkOrder::create([
    'cemetery_id'  => $cemetery->id,
    'customer_id'  => $customer->id,
    'title'        => 'Replace headstone base',
    'status'       => 'not-started',
    'priority'     => 'high',
    'date'         => now()->toDateString(),
    'due_date'     => now()->addDays(7)->toDateString(),
    'assigned_to'  => $staffUser->id,
]);

// Query open work orders for a cemetery
$open = WorkOrder::open()->where('cemetery_id', $cemetery->id)->get();

// Query templates
$templates = WorkOrder::templates()->get();

// Log time against a work order (via HasTimeEntries)
$workOrder->timeEntries()->create([
    'date'         => today(),
    'amount'       => 2.5,   // hours
    'performed_by' => $user->id,
    'description'  => 'Removed old base',
]);

// Mark complete and dispatch event
$workOrder->update(['status' => 'completed']);
$workOrder->onCompleted();

// Generate QR code for field access
$qr = $workOrder->getQrCodeDataUri();

// Display helpers
echo $workOrder->priority_badge;      // HTML badge
echo $workOrder->formatted_priority;  // "High"
echo $workOrder->age;                 // "3 days old"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
