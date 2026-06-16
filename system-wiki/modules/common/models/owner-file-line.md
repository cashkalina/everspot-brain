---
model: OwnerFileLine
module: Common
table: owner_file_lines
connection: tenant
primary_source: modules/Common/Models/OwnerFileLine.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/OwnerFile.php
  - modules/Property/Models/PropertyCommitment.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [OwnerFile]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, core]
---

# OwnerFileLine

## Overview

The OwnerFileLine model represents a single line item within an [OwnerFile](./owner-file.md). Each line points to an `ownable` entity (via morphTo) — typically a [PropertyCommitment](../../property/models/property-commitment.md) — and carries its own status and configuration data.

The status column is cast to the `OwnerFileLineStatus` enum. Two `BaseModel` methods (`reactToStatusChanges()` and `handleDefaultStatus()`) are overridden as no-ops because OwnerFileLine uses an enum for status rather than the string-based status system in `BaseModel`.

The `getPropertyInformationAttribute()` accessor provides a human-readable description of the linked property or property group, for display in owner-file UI contexts.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| owner_file_id | bigint | No | - | FK → owner_files: the parent owner file |
| ownable_type | varchar | No | - | Morph type — the class of the owned item |
| ownable_id | bigint | No | - | Morph ID — the owned item's primary key |
| status | varchar | Yes | - | Line status (cast to `OwnerFileLineStatus` enum) |
| config_data | json | Yes | - | Line-specific configuration (value object: `OwnerFileConfigData`) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `owner_file_id` → `owner_files.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `owner_file_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `config_data` → `OwnerFileConfigData::class` (value object)
- `status` → `OwnerFileLineStatus::class` (enum)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

- `getPropertyInformationAttribute(): ?string` — when `ownable_type` is `PropertyCommitment` and the commitment has a `property`, returns `$property->description`; when it has a `propertyGroup`, returns `'Any Property in {group_full_name}'`; otherwise `null`

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — owner file lines are soft-deleted, never hard-deleted

## Relationships

- `ownerFile()` — belongs to [OwnerFile](./owner-file.md) (`owner_file_id`): the parent owner file
- `ownable()` — morphTo: the owned item (typically a PropertyCommitment)

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `reactToStatusChanges(): void` — no-op override (OwnerFileLine uses enum status, not BaseModel's string-based status system)
- `handleDefaultStatus(): void` — no-op override (no default status needed for enum-typed status)

## Common Usage

```php
// Add a property commitment to an owner file
$line = $ownerFile->lines()->create([
    'ownable_type' => PropertyCommitment::class,
    'ownable_id'   => $commitment->id,
    'status'       => OwnerFileLineStatus::ACTIVE,
]);

// Get the property description for display
echo $line->property_information;   // "Lot 12, Section A, Block 3"

// Access the owned item
$commitment = $line->ownable;
```

## Imports

This model can be created/updated via spreadsheet import. See **[owner-file-line](../imports/owner-file-line.md)** for the column reference (valid headers, required fields, types, and conditional rules).

The import mechanism (upload → queued job → Excel) is documented in the [import subsystem](../../../system/imports.md).

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
