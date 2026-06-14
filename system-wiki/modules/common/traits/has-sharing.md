---
trait: HasSharing
owning_module: Common
source_paths:
  - modules/Common/Support/Sharing/Traits/HasSharing.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasSharing

**Source:** `modules/Common/Support/Sharing/Traits/HasSharing.php`
**Registry entry:** [system/traits/index.md#hassharing](../../../system/traits/index.md#hassharing)

## Purpose

Adds a fine-grained sharing system to models, backed by the polymorphic `Share` model. Records can be shared with individual users, roles (Spatie Permission), cemeteries, departments (via `ListOption`), or made public. Each share entry has a `permission_level` string (e.g. `view`, `edit`, `admin`) managed through a `SharePermissionRegistry` that defines per-model permission hierarchies.

Permission checking aggregates across all share types for a given user (user + roles + cemetery + department + public), always returning the highest applicable level.

## Contributed Columns

No columns are added to the using model's table. Share records live in the `shares` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `shares()` | `MorphMany` | `Modules\Common\Models\Share` | All share records for this model. |

## Contributed Scopes

| Scope | Signature | Description |
|-------|-----------|-------------|
| `scopeSharedWith()` | `(Builder, User $user): Builder` | Filters to records shared with the user (checks public, direct user, role, cemetery, department). |
| `scopeAccessibleBy()` | `(Builder, User $user): Builder` | Filters to records created by the user OR shared with them. |
| `scopeWithSharesFor()` | `(Builder, User $user): Builder` | Eager-loads the shares relevant to the given user. |

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `shareWithUser()` | `(User $user, ?string $permissionLevel = null): Share` | Creates or updates a user-direct share. |
| `shareWithRole()` | `(Role $role, ?string $permissionLevel = null): Share` | Creates or updates a role share. |
| `shareWithCemetery()` | `(Cemetery $cemetery, ?string $permissionLevel = null): Share` | Creates or updates a cemetery share. |
| `shareWithDepartment()` | `(ListOption $department, ?string $permissionLevel = null): Share` | Creates or updates a department share. |
| `sharePublicly()` | `(?string $permissionLevel = null): Share` | Creates or updates a public share. |
| `unshare()` | `(ShareType $type, ?int $id): void` | Removes a share by type and target ID. |
| `isSharedWith()` | `(User $user): bool` | Returns `true` if the user has any applicable share. |
| `getPermissionLevelFor()` | `(User $user): ?string` | Returns the highest permission level the user has, or `null` if no share applies. |
| `userHasPermission()` | `(User $user, string $requiredLevel): bool` | Checks whether the user's permission level satisfies `$requiredLevel` per the registry's hierarchy. |
| `getDefaultPermissionLevel()` | `(): string` | Returns the default permission level from `SharePermissionRegistry` for this model class. |
| `getHighestPermissionLevel()` | `(array $levels): string` | Returns the highest permission level from an array, ranked by `SharePermissionRegistry` hierarchy. |

## Configuration / Contract

No interface required on the using model. The `Share` model and its `shares` table must exist. `SharePermissionRegistry` must be bound in the service container and configured for the model class with its permission class and hierarchy.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasSharing` across model docs, or `use HasSharing` in Everspot source.
