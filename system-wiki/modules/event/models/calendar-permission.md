---
model: CalendarPermission
module: Event
table: calendar_permissions
connection: tenant
primary_source: modules/Event/Models/CalendarPermission.php
source_paths:
  - modules/Event/Models/Calendar.php
  - modules/Common/Models/User.php
traits:
  - HasFactory
related_models: [Calendar, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [scheduling, admin]
---

# CalendarPermission

## Overview

`CalendarPermission` is the per-user access-control record for a calendar. Each row grants a single user a specific permission level on a specific calendar. The five permission levels form a strict hierarchy from lowest to highest: `view`, `create`, `edit`, `delete`, `admin`. Higher levels imply all lower capabilities — a user with `edit` can also view and create, for example.

This model is the join record backing `Calendar::users()` and `Calendar::permissions()`. It carries `permission_type` as the pivot attribute. The `calendar_permissions` table has a unique constraint on `(calendar_id, user_id)`, so each user can hold at most one explicit permission per calendar at any time; granting a different level replaces the existing row.

Calendar owners are never stored here — owner-level access is determined by `calendars.owner_id` directly. `CalendarPermission` rows represent delegated access only.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| calendar_id | bigint | No | - | FK → calendars: the calendar this permission applies to |
| user_id | bigint | No | - | FK → users: the user receiving the permission |
| permission_type | enum | No | view | Permission level (`view`, `create`, `edit`, `delete`, `admin`) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `calendar_id` → `calendars.id` (cascade delete); `user_id` → `users.id` (cascade delete)

**Indexes:** unique index on `(calendar_id, user_id)`; FK-backing index on `user_id`; primary key on `id`.

## Casts

_None._

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['calendar_id', 'user_id', 'permission_type']`

**Hidden:** _None._

**Visible:** _None._

**Appends:** _None._

**Defaults (`$attributes`):** _None._ (schema default: `permission_type → view`)

## Accessors & Mutators

_None._

## Traits

- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for generating test `CalendarPermission` records

## Relationships

- `calendar()` — belongs to [Calendar](./calendar.md): the calendar this permission grants access to
- `user()` — belongs to [User](../../common/models/user.md): the user who holds this permission

## Scopes

- `forUser(Builder $query, User $user)` — filters to permissions belonging to the given user
- `forCalendar(Builder $query, Calendar $calendar)` — filters to permissions for the given calendar
- `withPermission(Builder $query, string $permission)` — filters to rows where `permission_type` matches the given value

## Events

_None defined on the model._

## Observers

_None registered._

## Key Methods

- `isView(): bool` — returns `true` if `permission_type === 'view'`
- `isCreate(): bool` — returns `true` if `permission_type === 'create'`
- `isEdit(): bool` — returns `true` if `permission_type === 'edit'`
- `isDelete(): bool` — returns `true` if `permission_type === 'delete'`
- `isAdmin(): bool` — returns `true` if `permission_type === 'admin'`
- `canView(): bool` — returns `true` for any permission level (all levels imply view)
- `canCreate(): bool` — returns `true` for `create`, `edit`, `delete`, or `admin`
- `canEdit(): bool` — returns `true` for `edit`, `delete`, or `admin`
- `canDelete(): bool` — returns `true` for `delete` or `admin`
- `canAdmin(): bool` — returns `true` only for `admin`

## Common Usage

```php
// Grant a user 'edit' access to a calendar
CalendarPermission::create([
    'calendar_id'     => $calendar->id,
    'user_id'         => $user->id,
    'permission_type' => 'edit',
]);

// Preferred: use Calendar::grantPermission() which upserts
$calendar->grantPermission($user, 'admin');

// Query all permissions for a specific user
$perms = CalendarPermission::forUser($user)->get();

// Check what a user can do from the permission record
$perm = CalendarPermission::forCalendar($calendar)->forUser($user)->first();
if ($perm?->canEdit()) {
    // allow editing
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
