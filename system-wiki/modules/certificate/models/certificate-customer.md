---
model: CertificateCustomer
module: Certificate
table: certificate_customers
connection: tenant
primary_source: modules/Certificate/Models/CertificateCustomer.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Certificate/Models/Certificate.php
  - modules/Customer/Models/Customer.php
  - modules/Common/Models/Address.php
traits: []
related_models: [Address, Certificate, Customer]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, customer, contract]
---

# CertificateCustomer

## Overview

`CertificateCustomer` is a pivot-with-extras model connecting a [Certificate](./certificate.md) to a [Customer](../../customer/models/customer.md). It records the customer's name at the time the certificate was generated (`customer_name`), providing a snapshot so the certificate retains the correct display name even if the customer record is later updated.

Beyond the relationship keys, the model carries a `customer_name` snapshot column and supports a polymorphic `address()` relationship (`addressable` morphOne), allowing a per-customer delivery or mailing address to be stored directly on the pivot row when needed.

The model extends `BaseModel` but declares no traits beyond those inherited from `BaseModel` itself.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| certificate_id | bigint | No | - | FK → certificates: the parent certificate |
| customer_id | bigint | No | - | FK → customers: the associated customer |
| customer_name | varchar | No | - | Snapshot of the customer's display name at time of creation |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `certificate_id` → `certificates.id`; `customer_id` → `customers.id`

**Indexes:** single-column indexes on `certificate_id`, `customer_id`

## Casts

_None._

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

- `certificate()` — belongs to [Certificate](./certificate.md): the parent certificate
- `customer()` — belongs to [Customer](../../customer/models/customer.md): the associated customer
- `address()` — morphOne [Address](../../common/models/address.md) (`addressable`): an optional address record for this customer on this certificate

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._

## Common Usage

```php
// CertificateCustomer is typically created via the certificate's customers() hasMany:
$certCustomer = $certificate->customers()->create([
    'customer_id'   => $customer->id,
    'customer_name' => $customer->full_name,
]);

// Access the related certificate and customer
$certCustomer->certificate;
$certCustomer->customer;

// Store an address for this customer on the certificate
$certCustomer->address()->create([
    'address_line_1' => '123 Main St',
    'city'           => 'Springfield',
    // ...
]);

// Load all certificate-customer links for a certificate
$certificate->customers()->with('customer')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
