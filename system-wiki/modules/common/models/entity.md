---
model: Entity
module: Common
table: entities
connection: tenant
primary_source: modules/Common/Models/Entity.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Providers/CommonServiceProvider.php
  - modules/Common/Observers/EntityObserver.php
  - modules/Common/Database/Factories/EntityFactory.php
  - modules/Common/Models/Address.php
  - modules/Common/Models/EntityTypePivot.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Memorial/Models/Memorial.php
traits:
  - HasAttributes
  - HasByUserFields
  - HasFactory
  - HasFiles
  - HasModelNumbering
  - HasSearch
  - SoftDeletes
related_models: [Address, EntityTypePivot, ListOption, Memorial, Note]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [core, admin]
---

# Entity

## Overview

The Entity model represents an external company or individual that interacts with the cemetery in a non-customer capacity — primarily as a manufacturer, installer, or dealer of memorials. Unlike [Customer](../../customer/models/customer.md), which represents buyers and deceased individuals, Entity captures the supplier/service-provider side of the memorial ecosystem.

Entities can be individuals (first/last name) or companies (`company_name`), optionally with title and suffix. One entity can have multiple types simultaneously, tracked via [EntityTypePivot](./entity-type-pivot.md) rows in the `entity_types` table. The three supported types — `MANUFACTURER`, `INSTALLER`, `DEALER` — are defined in the `EntityType` enum.

The model carries soft deletes, audit user stamps, EAV custom attributes, Spatie file attachments, model numbering, and search indexing via traits. Lifecycle events are handled by `EntityObserver`, registered in `CommonServiceProvider`.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_no | varchar | Yes | - | User-facing entity number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc) |
| title_id | bigint | Yes | - | FK → list_options: name title |
| first_name | varchar | Yes | - | First name (for individual entities) |
| middle_name | varchar | Yes | - | Middle name |
| last_name | varchar | Yes | - | Last name |
| suffix_id | bigint | Yes | - | FK → list_options: name suffix |
| company_name | varchar | Yes | - | Company name (for business entities) |
| contact_email | varchar | Yes | - | Primary contact email |
| contact_phone | varchar | Yes | - | Primary contact phone |
| website | varchar | Yes | - | Website URL |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `title_id`, `suffix_id` → `list_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `title_id`, `suffix_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

_None declared on the model._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

- `getFullNameAttribute(): string` — builds full name from title label, first/middle/last name, and suffix label (filtered nulls, space-joined)
- `getDisplayNameAttribute(): string` — returns `company_name` if set, otherwise `full_name`, falling back to `'Unknown Entity'`
- `getIsCompanyAttribute(): bool` — `true` when `company_name` is non-empty
- `getIsIndividualAttribute(): bool` — `true` when `first_name` or `last_name` is non-empty
- `getTypesAttribute()` — collection of `EntityType` enum values from `entityTypes` relationship

## Traits

- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for dynamic per-entity fields
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook (wired to `EntityFactory`)
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary file attachments (implements `HasMedia`)
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing for entity records
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — entities are soft-deleted, never hard-deleted

## Relationships

- `titleOption()` — belongs to [ListOption](./list-option.md) (`title_id`): name title lookup
- `suffixOption()` — belongs to [ListOption](./list-option.md) (`suffix_id`): name suffix lookup
- `addresses()` — morphMany [Address](./address.md) (`addressable`): all addresses
- `defaultShippingAddress()` — morphOne [Address](./address.md): the address with `shipping_default = 1`
- `defaultBillingAddress()` — morphOne [Address](./address.md): the address with `billing_default = 1`
- `otherAddresses()` — morphMany [Address](./address.md): addresses that are neither default billing nor default shipping
- `entityTypes()` — has many [EntityTypePivot](./entity-type-pivot.md) (`entity_id`): type assignments for this entity
- `memorialsAsManufacturer()` — has many [Memorial](../../memorial/models/memorial.md) (`manufacturer_id`): memorials where this entity is the manufacturer
- `memorialsAsInstaller()` — has many [Memorial](../../memorial/models/memorial.md) (`installer_id`): memorials where this entity is the installer
- `memorialsAsDealer()` — has many [Memorial](../../memorial/models/memorial.md) (`dealer_id`): memorials where this entity is the dealer
- `notes()` — morphMany [Note](./note.md) (`notable`): notes for this entity

## Scopes

- `ofType(Builder $query, EntityType|string $type): Builder` — filters to entities with a specific type via `entityTypes` whereHas
- `manufacturers(Builder $query): Builder` — filters to `EntityType::MANUFACTURER`
- `installers(Builder $query): Builder` — filters to `EntityType::INSTALLER`
- `dealers(Builder $query): Builder` — filters to `EntityType::DEALER`

## Events

_None._

## Observers

- `EntityObserver` — registered in `CommonServiceProvider::registerObservers()` (`Entity::observe(EntityObserver::class)`). Handles:
  - `saving` — normalizes/validates entity data
  - `created` — post-creation side effects
  - `deleting` — pre-deletion checks and cascades

## Key Methods

- `hasType(EntityType|string $type): bool` — returns `true` if the entity has a given type via `entityTypes()` query
- `isManufacturer(): bool` — shorthand for `hasType(EntityType::MANUFACTURER)`
- `isInstaller(): bool` — shorthand for `hasType(EntityType::INSTALLER)`
- `isDealer(): bool` — shorthand for `hasType(EntityType::DEALER)`

## Common Usage

```php
// Create a manufacturer entity
$entity = Entity::create([
    'company_name' => 'Rock of Ages',
    'contact_email' => 'info@rockofages.com',
]);
$entity->entityTypes()->create(['type' => EntityType::MANUFACTURER]);

// Query by type
$manufacturers = Entity::manufacturers()->get();

// Check type
if ($entity->isDealer()) {
    // handle dealer logic
}

// Display name
echo $entity->display_name;   // "Rock of Ages" (or full_name for individuals)
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
