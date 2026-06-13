---
model: Customer
module: Customer
table: customers
connection: tenant
source_paths:
  - modules/Customer/Models/Customer.php
  - app/Models/BaseModel.php
  - modules/Common/Traits/HasByUserFields.php
  - modules/Common/Traits/HasFiles.php
  - modules/Common/Traits/HasModelNumbering.php
  - modules/Common/Traits/HasPartialDateScopes.php
  - modules/Common/Traits/HasSearch.php
  - modules/Common/Traits/HasSyncables.php
  - modules/Attribute/Traits/HasAttributes.php
related: [Order, PaymentMethod, Payment, Transaction, Address, Certificate, Opportunity, Interment, PropertyCommitment, PaymentPlan, Task, WorkOrder]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-13
completeness: complete
deprecated: false
tags: [customer, core, crm]
---

# Customer

**Primary source:** `modules/Customer/Models/Customer.php`

## Overview

The Customer model represents individuals and organizations that interact with the cemetery. Customers can be leads, active customers, or have historical relationships with the organization. This is one of the central entities in the Everspot system, connecting to nearly every other module.

Customers support both individual persons and company entities. For individuals, the model tracks detailed personal information including names, dates of birth (with partial date support), contact information, and veteran status. Customers can have hierarchical relationships (parent/child) for family structures.

The model integrates extensively across the system, linking to financial records (payments, payment methods, transactions), cemetery operations (interments, property commitments, certificates), sales (orders, opportunities), and administrative functions (tasks, work orders, events). It implements soft deletes, file attachments, custom attributes, model numbering, and comprehensive audit tracking.

## Connection & Table

Tenant · `customers`

## Schema

<!-- Rendered from schema/tenant.json -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| parent_id | bigint | Yes | - | Parent customer for family hierarchies |
| model_no | varchar | Yes | - | User-facing customer number |
| status | varchar | No | - | Customer status (lead, customer) |
| type_id | bigint | Yes | - | Foreign key to customer type list option |
| title_id | bigint | Yes | - | Foreign key to title list option (Mr., Mrs., etc.) |
| first_name | varchar | Yes | - | Individual's first name |
| middle_name | varchar | Yes | - | Individual's middle name |
| last_name | varchar | Yes | - | Individual's last name |
| nickname | varchar | Yes | - | Preferred nickname |
| maiden_name | varchar | Yes | - | Maiden name |
| dob_year | smallint | Yes | - | Date of birth year component |
| dob_month | tinyint | Yes | - | Date of birth month component |
| dob_day | tinyint | Yes | - | Date of birth day component |
| dob_estimated | tinyint | No | 0 | Whether date of birth is estimated |
| suffix_id | bigint | Yes | - | Foreign key to suffix list option (Jr., Sr., etc.) |
| company_name | varchar | Yes | - | Company name for business customers |
| contact_email | varchar | Yes | - | Primary contact email |
| contact_phone | varchar | Yes | - | Primary contact phone |
| is_active | tinyint | No | 1 | Whether customer is active |
| meta | json | Yes | - | Additional metadata |
| created_by | bigint | Yes | - | User who created the customer |
| updated_by | bigint | Yes | - | User who last updated the customer |
| deleted_by | bigint | Yes | - | User who soft-deleted the customer |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft delete timestamp |

## Properties / Casts

**Constants:**
```php
const STATUSES = [
    'lead' => ['label' => 'Lead', 'color' => 'info'],
    'customer' => ['label' => 'Customer', 'color' => 'success'],
];

public static $defaultStatus = 'customer';
```

**Casts:**
- `is_active` → `boolean`
- `dob` → `PartialDateCast::class.':dob'` — Handles partial dates (year/month/day components)

**Guarded:**
- `[]` — All fields are mass-assignable

## Relationships

**Family Structure:**
- `parent()` — BelongsTo Customer: Parent customer in family hierarchy
- `children()` — HasMany Customer: Child customers in family hierarchy
- `relationsAsPrimary()` — BelongsToMany Customer: Customer relationships where this is primary
- `relationsAsSecondary()` — BelongsToMany Customer: Customer relationships where this is secondary

**Financial:**
- `paymentMethods()` — HasMany [PaymentMethod](../../transaction/models/payment-method.md): Stored payment methods
- `payments()` — HasMany [Payment](../../transaction/models/payment.md): Payment transactions
- `paymentMethodRequests()` — HasMany PaymentMethodRequest: Pending payment method setups
- `transactions()` — HasMany [Transaction](../../transaction/models/transaction.md): All transactions
- `autopays()` — HasMany Autopay: Automatic payment configurations
- `paymentPlans()` — BelongsToMany PaymentPlan: Active payment plans

**Cemetery Operations:**
- `intermentsAsDeceased()` — HasMany Interment: Interments where customer is deceased
- `intermentAsDeceased()` — HasOne Interment: Primary interment as deceased
- `intermentsAsNok()` — HasMany Interment: Interments where customer is next of kin
- `intermentsAsFuneralHome()` — HasMany Interment: Interments where customer is funeral home
- `intermentsAsFuneralDirector()` — HasMany Interment: Interments where customer is funeral director
- `certificates()` — BelongsToMany Certificate: Associated certificates
- `certificateLines()` — HasManyThrough CertificateLine: Certificate lines through certificates
- `propertyCommitments()` — BelongsToMany PropertyCommitment: Property ownership commitments
- `ownerFiles()` — BelongsToMany OwnerFile: Owner file associations (all types)
- `primaryOwnerFiles()` — BelongsToMany OwnerFile: Owner files where customer is primary
- `assignedOwnerFiles()` — BelongsToMany OwnerFile: Owner files assigned to customer
- `memorials()` — HasManyThrough Memorial: Memorial records

**Sales & Opportunities:**
- `opportunities()` — HasMany Opportunity: Sales opportunities
- `orders()` — BelongsToMany Order: Sales orders
- `orderLinesAssigned()` — HasMany OrderLine: Order lines assigned to this customer
- `liabilityLines()` — BelongsToMany LiabilityLine: Financial liability lines

**Administrative:**
- `tasks()` — MorphMany Task: Tasks associated with customer
- `workOrders()` — HasMany WorkOrder: Work orders for customer
- `events()` — MorphMany Event: Calendar events
- `notes()` — MorphMany Note: Customer notes
- `addresses()` — MorphMany Address: All addresses
- `defaultBillingAddress()` — MorphOne Address: Primary billing address
- `defaultShippingAddress()` — MorphOne Address: Primary shipping address
- `otherAddresses()` — MorphMany Address: Non-default addresses

**Reference Data:**
- `typeOption()` — BelongsTo ListOption: Customer type configuration
- `titleOption()` — BelongsTo ListOption: Title (Mr., Mrs., etc.)
- `suffixOption()` — BelongsTo ListOption: Suffix (Jr., Sr., etc.)
- `veteranTag()` — HasOne VeteranTag: Veteran status information

## Key Methods

- `allRelatedInterments(): Builder` — Returns query for all interments related to this customer in any capacity
- `findRelationBetween($customerId1, $customerId2)` — Static method to find relationship type between two customers
- `getFullNameAttribute(): string` — Computed full name from first, middle, last names
- `getFormattedPhoneAttribute(): string` — Returns formatted phone number
- `hasEmail(): bool` — Checks if customer has contact email

## Scopes / Events / Observers

**Query Scopes:**
- `active(Builder $query)` — Filters to active customers (`is_active = 1`)
- `hasEmail(Builder $query)` — Filters to customers with email addresses
- Partial date scopes via `HasPartialDateScopes` trait for DOB queries

**Soft Deletes:**
- Model uses `SoftDeletes` trait
- Deleted customers remain in database with `deleted_at` timestamp
- `deleted_by` tracks which user performed the deletion

**Media/Files:**
- Implements `HasMedia` interface via `HasFiles` trait
- Supports file attachments for documents, images, etc.

## Common Usage

```php
// Create a customer
$customer = Customer::create([
    'status' => 'customer',
    'first_name' => 'John',
    'last_name' => 'Doe',
    'contact_email' => 'john@example.com',
    'contact_phone' => '555-1234',
    'is_active' => true,
]);

// Create a company customer
$company = Customer::create([
    'status' => 'customer',
    'company_name' => 'Acme Corp',
    'contact_email' => 'info@acme.com',
    'is_active' => true,
]);

// Set partial date of birth
$customer->update([
    'dob_year' => 1950,
    'dob_month' => 6,
    'dob_day' => 15,
]);

// Access computed full name
echo $customer->full_name; // "John Doe"

// Query active customers with email
$activeWithEmail = Customer::active()->hasEmail()->get();

// Get all interments for a customer (any role)
$interments = $customer->allRelatedInterments()->get();

// Find relationship between two customers
$relationshipId = Customer::findRelationBetween($customer1->id, $customer2->id);

// Access financial records
$payments = $customer->payments;
$paymentMethods = $customer->paymentMethods;

// Create family hierarchy
$child = Customer::create([...]);
$child->parent()->associate($parentCustomer);
$child->save();

// Access children
$children = $parentCustomer->children;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
