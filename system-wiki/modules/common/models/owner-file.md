---
model: OwnerFile
module: Common
table: owner_files
connection: tenant
primary_source: modules/Common/Models/OwnerFile.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/OwnerFileObserver.php
  - modules/Common/Models/OwnerFileLine.php
  - modules/Common/Models/Note.php
  - modules/Customer/Models/Customer.php
  - modules/Property/Models/PropertyCommitment.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasFiles
  - HasModelNumbering
  - HasSearch
  - SoftDeletes
related_models: [Customer, Note, OwnerFileLine, PropertyCommitment]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, core]
---

# OwnerFile

## Overview

The OwnerFile model is the central record linking customers to the properties they own. It bundles together a display name (auto-generated from the primary customers or manually overridden), a status, configuration data, and the set of [OwnerFileLine](./owner-file-line.md) records that each point to a specific [PropertyCommitment](../../property/models/property-commitment.md).

Customers are associated to an OwnerFile in two roles via the `customer_owner_file` pivot: `primary` (the actual owner) and `assigned` (an alternative contact or joint holder). The `display_name` is computed from primary customers' full names, joined with `' & '`, unless `manual_name = true` in which case it is preserved as-is.

The model carries soft deletes, audit user stamps, EAV custom attributes, search indexing, file attachments, and model numbering via traits. Lifecycle events (including `display_name` regeneration) are handled by `OwnerFileObserver`, registered in `CommonServiceProvider`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_no | varchar | Yes | - | User-facing owner file number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| display_name | varchar | Yes | - | Auto-generated or manually overridden display name |
| manual_name | tinyint | No | 0 | When true, `display_name` is user-set and not regenerated |
| status | varchar | No | active | Owner file status |
| config_data | json | Yes | - | Owner file configuration (value object: `OwnerFileConfigData`) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `config_data` → `OwnerFileConfigData::class` (value object — see `modules/Common/ValueObjects/OwnerFileConfigData.php`)
- `manual_name` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

**Searchable columns:** `['model_no', 'display_name']`

## Accessors & Mutators

- `getPrimaryCustomerNamesAttribute(): string` — comma-joined full names of primary customers, or `'None'`
- `getAssignedCustomerNamesAttribute(): string` — comma-joined full names of assigned customers, or `'None'`
- `getModelInferredName(): ?string` — returns `display_name`

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for dynamic per-owner-file fields
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary attachments (implements `HasMedia`)
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing on `model_no` and `display_name`
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — owner files are soft-deleted, never hard-deleted

## Relationships

- `lines()` — has many [OwnerFileLine](./owner-file-line.md): the property lines in this owner file
- `allCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) via `customer_owner_file` (pivot `role`, timestamps): all associated customers
- `primaryCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) via `customer_owner_file` where `role = primary`: primary owner customers
- `assignedCustomers()` — belongs-to-many [Customer](../../customer/models/customer.md) via `customer_owner_file` where `role = assigned`: assigned customers
- `notes()` — morphMany [Note](./note.md) (`notable`): notes on this owner file
- `propertyCommitments()` — has-many-through [PropertyCommitment](../../property/models/property-commitment.md) (through OwnerFileLine, matching `ownable_type = PropertyCommitment::class`)

## Scopes

_None._

## Events

_None._

## Observers

- `OwnerFileObserver` — registered in `CommonServiceProvider::registerObservers()` (`OwnerFile::observe(OwnerFileObserver::class)`). Handles:
  - `created`, `updated` — regenerates `display_name` from primary customers when `manual_name = false`
  - `deleting`, `deleted`, `restored`, `forceDeleted` — cascade and cleanup hooks

## Key Methods

- `generateDisplayName($primaryCustomers): string` *(static)* — builds the auto-generated display name from a collection of primary customers (full names joined with `' & '`; returns `'**Add Owner to Update**'` for empty collections)
- `getCustomerSignature(array $customerIds): string` *(static)* — returns a sorted, comma-joined string of customer IDs for deduplication checks

## Common Usage

```php
// Create an owner file and attach a primary customer
$ownerFile = OwnerFile::create(['status' => 'active']);
$ownerFile->primaryCustomers()->attach($customer->id, ['role' => 'primary']);

// Get auto-generated display name
echo $ownerFile->display_name;   // "John Doe & Jane Doe"

// Manually override display name
$ownerFile->update(['display_name' => 'Doe Family Trust', 'manual_name' => true]);

// Get all property commitments through lines
$properties = $ownerFile->propertyCommitments;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
