---
model: CertificateLine
module: Certificate
table: certificate_lines
connection: tenant
primary_source: modules/Certificate/Models/CertificateLine.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Certificate/Observers/CertificateLineObserver.php
  - modules/Certificate/Providers/CertificateServiceProvider.php
  - modules/Certificate/Models/Certificate.php
  - modules/Liability/Models/LiabilityLine.php
  - modules/Product/Models/Product.php
  - modules/Property/Models/Property.php
  - modules/Property/Models/PropertyGroup.php
  - modules/Property/Models/PropertyType.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasMoneyFields
  - SoftDeletes
related_models: [Certificate, LiabilityLine, Product, Property, PropertyGroup, PropertyType]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, contract, financial]
---

# CertificateLine

## Overview

`CertificateLine` represents a single line item on a [Certificate](./certificate.md). Each line records either a product-based entry (linked to an actual `LiabilityLine` from the financial module) or a manual entry (where product details are supplied directly). Lines can also carry a property reference (`property_id`, `property_type_id`, `property_group_id`) to describe the specific cemetery property rights being certified.

When a `liability_line_id` is present, the `CertificateLineObserver` auto-populates the snapshot columns (`product_id`, `order_reference`, `product_sku`, `product_name`, `product_description`, `sale_price`, `sale_date`) from the linked `LiabilityLine` on `creating` and on `updating` if the FK changes. This ensures that printed certificates reflect the liability data at the time of generation, even if the liability later changes.

For property lines, the `property_description` column is computed from EAV attribute values (via `HasAttributes`) using `generatePropertyDescription()`, which reads attribute values for the `location-certificate-line` area code. Rich grouping helpers live on the parent `Certificate` model (via `GroupCertificateLinesByLocation`), not here.

Soft deletes are enabled; the observer's `saved`/`deleted` hooks call `SyncIssuedCertificateLineChanges` to keep liability certificate-date records in sync when the certificate is already issued.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| certificate_id | bigint | No | - | FK → certificates: the parent certificate |
| liability_line_id | bigint | Yes | - | FK → liability_lines: linked liability line (null for manual entries) |
| product_id | bigint | Yes | - | FK → products: snapshot of the product (auto-populated from liability line) |
| order_reference | varchar | Yes | - | Snapshot of order reference (auto-populated from liability line) |
| product_sku | varchar | Yes | - | Snapshot of product SKU (auto-populated from liability line) |
| product_name | varchar | No | - | Snapshot of product name (required; auto-populated or supplied manually) |
| product_description | text | Yes | - | Snapshot of product description (auto-populated from liability line) |
| sale_price | int | Yes | - | Sale price in cents (via [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents/dollars conversion) |
| sale_date | date | Yes | - | Sale date (snapshot from liability line or manual) |
| property_id | bigint | Yes | - | FK → properties: the specific property being certified (if applicable) |
| property_type_id | bigint | Yes | - | FK → property_types: property type (for manual property entries) |
| property_group_id | bigint | Yes | - | FK → property_groups: property group (for grouped property entries) |
| property_description | text | Yes | - | Computed description from EAV location attributes (see `generatePropertyDescription()`) |
| internal_notes | text | Yes | - | Notes visible only to staff |
| external_notes | text | Yes | - | Notes printed on the certificate |
| is_transferable | tinyint | No | 0 | Whether the rights on this line can be transferred |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `certificate_id` → `certificates.id`; `liability_line_id` → `liability_lines.id`; `product_id` → `products.id`; `property_id` → `properties.id`; `property_type_id` → `property_types.id`; `property_group_id` → `property_groups.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** single-column indexes on `certificate_id`, `liability_line_id`, `product_id`, `property_id`, `property_type_id`, `property_group_id`, `created_by`, `updated_by`, `deleted_by`

## Casts

- `is_transferable` → `boolean`
- `sale_date` → `date`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->
<!-- HasMoneyFields handles cents/dollars conversion for sale_price via $moneyAttributes -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `is_transferable` defaults to `0` at the database level

**Money attributes:**
```php
public $moneyAttributes = ['sale_price'];
```
`sale_price` is stored in cents and transparently converted to dollars by [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields).

## Accessors & Mutators

_None._

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes; provides `attributeValues()` used by `generatePropertyDescription()` to build property descriptions from location attribute values
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasMoneyFields](../../../system/traits/index.md#hasmoneyfields) — transparent cents-to-dollars conversion for `sale_price`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — certificate lines are soft-deleted, never hard-deleted

## Relationships

- `certificate()` — belongs to [Certificate](./certificate.md): the parent certificate
- `liabilityLine()` — belongs to [LiabilityLine](../../liability/models/liability-line.md): the financial liability line this entry snapshots (null for manual entries)
- `property()` — belongs to [Property](../../property/models/property.md): the specific cemetery property being certified
- `propertyType()` — belongs to [PropertyType](../../property/models/property-type.md): the property type for manual property entries
- `propertyGroup()` — belongs to [PropertyGroup](../../property/models/property-group.md): the property group this line belongs to
- `product()` — belongs to [Product](../../product/models/product.md): the product record (FK snapshot; prefer `product_name` for display)

## Scopes

- `issued(Builder $query)` — filters to lines whose parent certificate has `status = 'issued'` (via `whereHas('certificate', ...)`)

## Events

_None._

## Observers

- `CertificateLineObserver` — registered in `CertificateServiceProvider::registerObservers()` (`CertificateLine::observe(CertificateLineObserver::class)`). Handles:
  - `creating` — calls `populateSnapshotFields()`: if `liability_line_id` is set, auto-populates `product_id`, `order_reference`, `product_sku`, `product_name`, `product_description`, `sale_price`, `sale_date` from the linked `LiabilityLine`
  - `updating` — re-runs `populateSnapshotFields()` only when `liability_line_id` has changed
  - `saved` — runs `SyncIssuedCertificateLineChanges::onSaved()` to propagate liability certificate-date changes when the certificate is issued
  - `deleted` — runs `SyncIssuedCertificateLineChanges::onDeleted()` to clean up liability certificate-date records

## Key Methods

- `isProperty(): bool` — `true` if any of `property_id`, `property_type_id`, or `property_group_id` is set
- `isManualProperty(): bool` — `true` if `property_type_id` is set but `property_id` is not (a manual, non-linked property entry)
- `generatePropertyDescription(): void` — reads EAV attribute values for the `location-certificate-line` area code, builds a `Label: Value | …` string, and saves it into `property_description` if changed
- `isPropertyAvailable(): bool` — checks whether the linked property is available; delegates to `Property::isAvailableExcept()` (when a liability line is also present) or `Property::isAvailable()`; returns `true` for manual entries with no linked property
- `hasLiabilityLine(): bool` — `true` if `liability_line_id` is non-null
- `isManual(): bool` — `true` if `liability_line_id` is null (manually entered line, no financial link)

## Factory & Seeders

- Factory: `modules/Certificate/Database/Factories/CertificateLineFactory.php`

## Common Usage

```php
// Add a liability-linked line (snapshot fields auto-populated by observer)
$line = $certificate->lines()->create([
    'liability_line_id' => $liabilityLine->id,
    'product_name'      => $liabilityLine->product_name,   // set explicitly or let observer populate
]);

// Add a manual property line
$line = $certificate->lines()->create([
    'product_name'     => 'Right of Interment',
    'property_type_id' => $propertyType->id,
    'is_transferable'  => false,
]);

// Generate the property description from EAV attributes after saving attribute values
$line->generatePropertyDescription();

// Check availability before issuing
if (! $line->isPropertyAvailable()) {
    // handle conflict
}

// Query only issued certificate lines
$issuedLines = CertificateLine::issued()->with('certificate')->get();

// Distinguish manual vs. liability-linked
if ($line->isManual()) {
    // no financial record linked
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
