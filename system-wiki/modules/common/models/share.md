---
model: Share
module: Common
table: shares
connection: tenant
primary_source: modules/Common/Models/Share.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/User.php
traits:
  - HasByUserFields
related_models: [User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# Share

## Overview

The Share model is the backing record for the [HasSharing](../../../system/traits/index.md#hassharing) trait. It represents a sharing grant — a specific `shareable` entity (e.g. an Owner File or Report) shared with a specific `share_type` target (user, role, cemetery, department, or public), at a specific `permission_level`.

Permission levels are validated against the `SharePermissionRegistry` on `creating` and `updating` via lifecycle hooks in `booted()`. The registry resolves the valid permission classes for each shareable type; unknown types are silently skipped rather than blocking.

The `user()` relationship (keyed on `share_id`) resolves when `share_type` is `ShareType::USER`. For other share types (roles, cemeteries, public), `share_id` holds the relevant entity's ID or is null.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| shareable_type | varchar | No | - | Morph type — the class of the shared model |
| shareable_id | bigint | No | - | Morph ID — the shared model's primary key |
| share_type | enum | No | - | Who this is shared with (`user`, `role`, `cemetery`, `department`, `public`) |
| share_id | bigint | Yes | - | ID of the user/role/cemetery/department (null for `public`) |
| permission_level | varchar | No | - | Permission level string (validated by `SharePermissionRegistry`) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `created_by`, `updated_by` → `users.id`

**Indexes:** FK-backing indexes on `created_by`, `updated_by`; composite index on (`shareable_type`, `shareable_id`).

## Casts

- `share_type` → `ShareType::class` (enum)

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` audit stamps

## Relationships

- `shareable()` — morphTo: the shared entity (any model using [HasSharing](../../../system/traits/index.md#hassharing))
- `user()` — belongs to [User](./user.md) (`share_id`): the user this is shared with (only valid when `share_type = ShareType::USER`)

## Scopes

- `forUser($query, User $user)` — filters to `share_type = USER` and `share_id = $user->id`
- `forShareType($query, ShareType $type)` — filters by `share_type`

## Events

- `booted()` — `creating` and `updating` hooks: calls `validatePermissionLevel()` to assert the `permission_level` is valid for the `shareable_type` via `SharePermissionRegistry`

## Observers

_None registered._

## Key Methods

- `hasPermission(string $requiredLevel): bool` — checks whether this share's `permission_level` satisfies the `$requiredLevel` using `SharePermissionRegistry::hasPermission()`
- `validatePermissionLevel(): void` *(protected)* — throws `InvalidArgumentException` if `permission_level` is not valid for the `shareable_type` (silently skips if type is not registered)

## Common Usage

```php
// Share an owner file with a user at 'view' permission
Share::create([
    'shareable_type' => OwnerFile::class,
    'shareable_id'   => $ownerFile->id,
    'share_type'     => ShareType::USER,
    'share_id'       => $user->id,
    'permission_level' => 'view',
]);

// Get all shares for a user
$userShares = Share::forUser($user)->get();

// Check permission level
if ($share->hasPermission('edit')) {
    // allow editing
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
