---
model: Customer
module: Customer
table: customers
connection: tenant
primary_source: modules/Customer/Models/Customer.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Customer/Observers/CustomerObserver.php
  - modules/Customer/Providers/CustomerServiceProvider.php
  - modules/Common/Casts/PartialDateCast.php
  - modules/Customer/Pivots/CustomerRelationPivot.php
  - modules/Common/Models/Address.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/OwnerFile.php
  - modules/Certificate/Models/Certificate.php
  - modules/Certificate/Models/CertificateLine.php
  - modules/Event/Models/Event.php
  - modules/Interment/Models/Interment.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Memorial/Models/Memorial.php
  - modules/Memorial/Models/MemorialPerson.php
  - modules/Opportunity/Models/Opportunity.php
  - modules/Order/Models/Order.php
  - modules/Order/Models/OrderLine.php
  - modules/PaymentPlan/Models/PaymentPlan.php
  - modules/Property/Models/PropertyCommitment.php
  - modules/Task/Models/Task.php
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Models/PaymentMethod.php
  - modules/Transaction/Models/PaymentMethodRequest.php
  - modules/Transaction/Models/Transaction.php
  - modules/Autopay/Models/Autopay.php
  - modules/WorkOrder/Models/WorkOrder.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasPartialDateScopes
  - HasSearch
  - HasSyncables
  - SoftDeletes
related_models: [Address, Autopay, Certificate, CertificateLine, Customer, Event, Interment, LiabilityLine, ListOption, Memorial, Note, Opportunity, Order, OrderLine, OwnerFile, Payment, PaymentMethod, PaymentMethodRequest, PaymentPlan, PropertyCommitment, Task, VeteranTag, WorkOrder]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [customer, core, crm]
---

# Customer

## Overview

The Customer model represents individuals and organizations that interact with the cemetery. Customers can be leads or active customers, supporting both individual persons and company entities. It is one of the central entities in the Everspot system, connecting to nearly every other module.

For individuals, the model tracks detailed personal information — names (first/middle/last/nickname/maiden), title and suffix, partial dates of birth (stored as separate year/month/day component columns), and contact details. For organizations, a `company_name` is used instead. Customers can form hierarchies two ways: a simple parent/child link (`parent_id`) and a richer many-to-many `customer_relation` graph that records directional relationship types between two customers.

The model integrates extensively across the system, linking to financial records (payments, payment methods, transactions, payment plans, autopays), cemetery operations (interments in several roles, property commitments, certificates, memorials), sales (orders, opportunities, liability lines), and administrative functions (tasks, work orders, events, notes, addresses). It carries soft deletes, audit user stamps, Spatie media file attachments, EAV custom attributes, model numbering, search indexing, and external-integration sync linkage — all via traits (see [Traits](#traits)).

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| parent_id | bigint | Yes | - | Parent customer for simple family hierarchies (FK → customers) |
| model_no | varchar | Yes | - | User-facing customer number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| status | varchar | No | - | Customer status (`lead`, `customer`) |
| type_id | bigint | Yes | - | FK → list_options: customer type |
| title_id | bigint | Yes | - | FK → list_options: title (Mr., Mrs., etc.) |
| first_name | varchar | Yes | - | Individual's first name |
| middle_name | varchar | Yes | - | Individual's middle name |
| last_name | varchar | Yes | - | Individual's last name |
| nickname | varchar | Yes | - | Preferred nickname |
| maiden_name | varchar | Yes | - | Maiden name |
| dob_year | smallint | Yes | - | Date-of-birth year component (partial date) |
| dob_month | tinyint | Yes | - | Date-of-birth month component (partial date) |
| dob_day | tinyint | Yes | - | Date-of-birth day component (partial date) |
| dob_estimated | tinyint | No | 0 | Whether the date of birth is estimated |
| suffix_id | bigint | Yes | - | FK → list_options: suffix (Jr., Sr., etc.) |
| company_name | varchar | Yes | - | Company name for business customers |
| contact_email | varchar | Yes | - | Primary contact email |
| contact_phone | varchar | Yes | - | Primary contact phone (digits-only; normalized on set) |
| is_active | tinyint | No | 1 | Whether the customer is active |
| meta | json | Yes | - | Additional metadata |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `parent_id` → `customers.id`; `type_id`, `title_id`, `suffix_id` → `list_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** single-column indexes on `company_name`, `contact_email`, `contact_phone`, `first_name`, `middle_name`, `last_name`, `maiden_name`, `nickname`, `model_no`, `status`, `is_active`, `dob_year`; composite index on (`dob_year`, `dob_month`); FK-backing indexes on `parent_id`, `type_id`, `title_id`, `suffix_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `is_active` → `boolean`
- `dob` → `PartialDateCast::class.':dob'` — composes the `dob_year` / `dob_month` / `dob_day` component columns into a single partial-date value (see `modules/Common/Casts/PartialDateCast.php`)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._ (the many accessors below are read on demand, not auto-appended to array/JSON output)
**Defaults (`$attributes`):** _None._ — `status` is defaulted at runtime by the observer (`setting('customer_default_status')` → `Customer::$defaultStatus`, which is `customer`), not via `$attributes`.

**Constants / static config:**
```php
const STATUSES = [
    'lead'     => ['label' => 'Lead',     'color' => 'info'],
    'customer' => ['label' => 'Customer', 'color' => 'success'],
];

public static $defaultStatus = 'customer';
```

## Accessors & Mutators

- `getInitialsAttribute(): ?string` — up to 3 uppercase initials, from `company_name` words or first/middle/last
- `getTypeAttribute(): ?string` — name of the related type [ListOption](../../common/models/list-option.md)
- `getTitleAttribute(): ?string` — name of the related title [ListOption](../../common/models/list-option.md)
- `getSuffixAttribute(): ?string` — name of the related suffix [ListOption](../../common/models/list-option.md)
- `getStatusBadgeAttribute(): ?string` — HTML badge for the customer status (color/label from `STATUSES`, plus inactive styling)
- `getPivotBadgeAttribute(): string` — HTML badge for the pivot `role` (primary/assigned/additional); only meaningful when loaded through a pivot relationship
- `getFullNameAttribute(): ?string` — `company_name`, or first/middle/last joined and suffixed
- `getFullNameMaidenAttribute(): ?string` — full name with `(maiden_name)` appended when present
- `getTitleFullNameAttribute(): ?string` — title prepended to full name
- `getTitleFullNameMaidenAttribute(): ?string` — title prepended to full-name-with-maiden
- `getCertificateNumbersAttribute(): string` — comma-joined `model_no`s of related certificates, or `None`
- `getCalculatedFirstNameAttribute(): ?string` — `first_name`, falling back to `company_name`
- `getSelectFieldNameAttribute(): ?string` — display label for select fields (the full name)
- `getFormattedPhoneNumberAttribute(): ?string` — `contact_phone` run through the `FormatPhoneNumber` action
- `setContactPhoneAttribute($value): void` — **mutator**: strips all non-digits from `contact_phone` on write (null-safe)

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for storing dynamic per-customer fields
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps (backs the `created_by` / `updated_by` / `deleted_by` columns)
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (a custom `CustomerFactory` is wired via `newFactory()`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary attachments (the model implements `HasMedia`) for customer documents and images
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no` (with customer-specific type logic; see `onCustomer()` / `getModelNumberType()`)
- [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) — query scopes over the `dob_year` / `dob_month` / `dob_day` partial-date columns
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; this model's searchable payload is built in `addToSearchData()`
- [HasSyncables](../../../system/traits/index.md#hassyncables) — links the customer to external-integration records (e.g. QuickBooks)
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — customers are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

**Family / customer graph:**
- `parent()` — belongs to [Customer](./customer.md) (`parent_id`): parent in the simple family hierarchy
- `children()` — has many [Customer](./customer.md) (`parent_id`): children in the simple family hierarchy
- `relationsAsPrimary()` — belongs-to-many [Customer](./customer.md) via `customer_relation` (as customer A): directional relationships where this customer is the primary side
- `relationsAsSecondary()` — belongs-to-many [Customer](./customer.md) via `customer_relation` (as customer B): directional relationships where this customer is the secondary side

**Financial:**
- `paymentMethods()` — has many [PaymentMethod](../../transaction/models/payment-method.md): stored payment methods
- `payments()` — has many [Payment](../../transaction/models/payment.md): payment transactions
- `paymentMethodRequests()` — has many [PaymentMethodRequest](../../transaction/models/payment-method-request.md): pending payment-method setups
- `transactions()` — has many [Transaction](../../transaction/models/transaction.md): all transactions
- `autopays()` — has many [Autopay](../../autopay/models/autopay.md): automatic-payment configurations
- `paymentPlans()` — belongs-to-many [PaymentPlan](../../payment-plan/models/payment-plan.md) (pivot `role`): associated payment plans
- `liabilityLines()` — belongs-to-many [LiabilityLine](../../liability/models/liability-line.md) (pivot `role`): financial liability lines

**Cemetery operations:**
- `intermentsAsDeceased()` — has many [Interment](../../interment/models/interment.md) (`deceased_id`): interments where this customer is the deceased
- `intermentAsDeceased()` — has one [Interment](../../interment/models/interment.md) (`deceased_id`): the single interment as deceased
- `intermentsAsNok()` — has many [Interment](../../interment/models/interment.md) (`nok_id`): interments where this customer is next of kin
- `intermentsAsFuneralHome()` — has many [Interment](../../interment/models/interment.md) (`funeral_home_id`): interments where this customer is the funeral home
- `intermentsAsFuneralDirector()` — has many [Interment](../../interment/models/interment.md) (`funeral_director_id`): interments where this customer is the funeral director
- `certificates()` — belongs-to-many [Certificate](../../certificate/models/certificate.md) via `certificate_customers` (pivot `customer_name`): associated certificates
- `certificateLines()` — has-many-through [CertificateLine](../../certificate/models/certificate-line.md) (through Certificate): certificate lines for the customer's certificates
- `propertyCommitments()` — belongs-to-many [PropertyCommitment](../../property/models/property-commitment.md): property ownership commitments
- `ownerFiles()` — belongs-to-many [OwnerFile](../../common/models/owner-file.md) via `customer_owner_file` (pivot `role`, timestamps): owner-file associations (all roles)
- `primaryOwnerFiles()` — belongs-to-many [OwnerFile](../../common/models/owner-file.md): owner files where `role = primary`
- `assignedOwnerFiles()` — belongs-to-many [OwnerFile](../../common/models/owner-file.md): owner files where `role = assigned`
- `memorials()` — has-many-through [Memorial](../../memorial/models/memorial.md) (through MemorialPerson): memorials the customer appears on

**Sales & opportunities:**
- `opportunities()` — has many [Opportunity](../../opportunity/models/opportunity.md): sales opportunities
- `orders()` — belongs-to-many [Order](../../order/models/order.md) via `customer_order` (pivot `role`): sales orders
- `orderLinesAssigned()` — has many [OrderLine](../../order/models/order-line.md) (`assigned_customer_id`): order lines assigned to this customer

**Administrative:**
- `tasks()` — morphMany [Task](../../task/models/task.md) (`taskable`): tasks for the customer
- `workOrders()` — has many [WorkOrder](../../work-order/models/work-order.md): work orders for the customer
- `events()` — morphMany [Event](../../event/models/event.md) (`eventable`): calendar events
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): customer notes
- `addresses()` — morphMany [Address](../../common/models/address.md) (`addressable`): all addresses
- `defaultBillingAddress()` — morphOne [Address](../../common/models/address.md): the default billing address (`billing_default = 1`)
- `defaultShippingAddress()` — morphOne [Address](../../common/models/address.md): the default shipping address (`shipping_default = 1`)
- `otherAddresses()` — morphMany [Address](../../common/models/address.md): addresses that are neither default billing nor default shipping

**Reference data:**
- `typeOption()` — belongs to [ListOption](../../common/models/list-option.md) (`type_id`): customer type
- `titleOption()` — belongs to [ListOption](../../common/models/list-option.md) (`title_id`): title (Mr., Mrs., …)
- `suffixOption()` — belongs to [ListOption](../../common/models/list-option.md) (`suffix_id`): suffix (Jr., Sr., …)
- `veteranTag()` — has one [VeteranTag](./veteran-tag.md): veteran status information

## Scopes

- `active(Builder $query)` — `is_active = true`
- `hasEmail(Builder $query)` — `contact_email` present and non-empty
- `withoutEmail(Builder $query)` — `contact_email` null or empty
- `hasPhone(Builder $query)` — `contact_phone` present and non-empty
- `withoutPhone(Builder $query)` — `contact_phone` null or empty
- `hasAddress(Builder $query)` — has a default billing or shipping address
- `withoutAddress(Builder $query)` — has neither a default billing nor shipping address
- `hasBillingAddress(Builder $query)` — has a default billing address
- `withoutBillingAddress(Builder $query)` — lacks a default billing address
- `hasShippingAddress(Builder $query)` — has a default shipping address
- `withoutShippingAddress(Builder $query)` — lacks a default shipping address
- `isDeceased(Builder $query)` — has at least one interment as deceased
- `isNotDeceased(Builder $query)` — has no interment as deceased

Partial-date query scopes over the DOB component columns are contributed by [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) (see trait doc).

## Events

_None defined on the model._ Lifecycle behavior is handled by `CustomerObserver` (see Observers). On update the observer dispatches the `CustomerUpdated` event with the list of changed fields.

## Observers

- `CustomerObserver` — registered in `CustomerServiceProvider::boot()` (`Customer::observe(CustomerObserver::class)`). Handles:
  - `saving` — trims whitespace on name/contact fields; defaults `status` when unset; prevents `type_id` from being changed once set
  - `created` — fires `analytics()->track('Customer Created')`
  - `updated` — dispatches `CustomerUpdated` with the changed-field list
  - `deleting` — wraps deletion in a transaction: runs `PreDeleteCustomer` checks, then deletes related events and tasks

## Key Methods

- `findRelationBetween($customerId1, $customerId2)` *(static)* — looks up the directional relationship type id between two customers in `customer_relation` (checks both A→B and B→A orderings); returns the relation id or `null`
- `allRelatedInterments(): Builder` — query for all interments referencing this customer in any role (deceased, NOK, funeral home, funeral director), eager-loaded and ordered by date desc
- `getAllPropertyOwned(): Collection` — all property owned by the customer (via `GetCustomerProperties`)
- `getOpenPropertyOwned(): Collection` — only open/active property owned (via `GetCustomerProperties`)
- `onCustomer(): void` — re-generates the `model_no` when the current value no longer matches the configured prefix/suffix template (hooks the numbering trait)
- `addToSearchData(): array` — builds the searchable representation (full name, nickname, email, phone, billing/shipping address previews) for [HasSearch](../../../system/traits/index.md#hassearch)

## Common Usage

```php
// Create an individual customer
$customer = Customer::create([
    'first_name'    => 'John',
    'last_name'     => 'Doe',
    'contact_email' => 'john@example.com',
    'contact_phone' => '555-1234',   // stored as digits only: "5551234"
    'is_active'     => true,
]);

// Create a company customer
$company = Customer::create([
    'company_name'  => 'Acme Corp',
    'contact_email' => 'info@acme.com',
    'is_active'     => true,
]);

// Partial date of birth
$customer->update(['dob_year' => 1950, 'dob_month' => 6, 'dob_day' => 15]);

// Computed display values
echo $customer->full_name;        // "John Doe"
echo $customer->initials;         // "JD"

// Query helpers
$leads = Customer::active()->hasEmail()->get();
$living = Customer::isNotDeceased()->get();

// Interments across all roles
$interments = $customer->allRelatedInterments()->get();

// Relationship type between two customers
$relationId = Customer::findRelationBetween($a->id, $b->id);

// Simple family hierarchy
$child->parent()->associate($parent);
$child->save();
$kids = $parent->children;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
</content>
</invoke>
