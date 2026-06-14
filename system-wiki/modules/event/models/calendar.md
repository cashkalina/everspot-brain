---
model: Calendar
module: Event
table: calendars
connection: tenant
primary_source: modules/Event/Models/Calendar.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Models/User.php
  - modules/Event/Models/Event.php
  - modules/Event/Models/CalendarPermission.php
traits:
  - HasColor
  - HasIcon
  - SoftDeletes
related_models: [CalendarPermission, Event, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [scheduling, admin, core]
---

# Calendar

## Overview

The Calendar model is the organizing container for events in the Everspot system. Each calendar has a name, optional description, a hex color for visual distinction in the UI, and a type that classifies it as either personal or shared. Calendars are owned by a single user (`owner_id`) and may be designated as globally viewable or globally editable, controlling whether all users can see or modify their events without explicit per-user grants.

Access control is layered: calendar owners always hold implicit admin-level access, while other users may be granted explicit per-user permissions through the `CalendarPermission` model (with levels `view`, `create`, `edit`, `delete`, and `admin`). System-wide gate permissions (`calendar-view`, `calendar-update`) bypass calendar-level checks entirely. The model exposes a family of `can*` methods for each permission level, making authorization checks easy at the application layer.

Calendars support soft deletes, keeping deleted calendars (and their events) recoverable. The `HasColor` trait supplies hex-color storage with UI helpers for contrast and opacity; its contributed `color` column defaults to `#3788d8` (blue) in the schema.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| name | varchar | No | - | Calendar display name |
| description | text | Yes | - | Optional calendar description |
| color | varchar | No | #3788d8 | Hex color for UI display (via [HasColor](../../../system/traits/index.md#hascolor) — see trait doc) |
| type | enum | No | personal | Calendar type (`personal` or `shared`) |
| global_viewable | tinyint | No | 0 | Whether all users can view this calendar and its events |
| global_editable | tinyint | No | 0 | Whether all users can create/edit/delete events on this calendar |
| owner_id | bigint | No | - | FK → users: the calendar owner |
| is_active | tinyint | No | 1 | Whether the calendar is active |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `owner_id` → `users.id`

**Indexes:** FK-backing index on `owner_id`; primary key on `id`.

## Casts

- `type` → `CalendarType::class` — enum cast; values `personal` and `shared`
- `global_viewable` → `boolean`
- `global_editable` → `boolean`
- `is_active` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['name', 'description', 'color', 'type', 'global_viewable', 'global_editable', 'owner_id', 'is_active']`

**Hidden:** _None._

**Visible:** _None._

**Appends:** _None._

**Defaults (`$attributes`):** _None._ (schema defaults: `color → #3788d8`, `type → personal`, `global_viewable → 0`, `global_editable → 0`, `is_active → 1`)

## Accessors & Mutators

_None._

## Traits

- [HasColor](../../../system/traits/index.md#hascolor) — hex color storage with `getColor()`, `getTextColor()` (contrast), and `getColorWithOpacity()` for calendar UI display
- [HasIcon](../../../system/traits/index.md#hasicon) — Bootstrap Icon class mapping for calendar display in the UI
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — calendars are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `owner()` — belongs to [User](../../common/models/user.md) (`owner_id`): the user who owns this calendar
- `events()` — has many [Event](./event.md): all events on this calendar
- `permissions()` — has many [CalendarPermission](./calendar-permission.md): per-user permission grants for this calendar
- `users()` — belongs-to-many [User](../../common/models/user.md) via `calendar_permissions` (pivot `permission_type`, timestamps): all users granted access to this calendar

## Scopes

- `personal(Builder $query)` — filters to `type = 'personal'`
- `shared(Builder $query)` — filters to `type = 'shared'`
- `globalViewable(Builder $query)` — filters to `global_viewable = true`
- `globalEditable(Builder $query)` — filters to `global_editable = true`
- `active(Builder $query)` — filters to `is_active = true`
- `accessibleByUser(Builder $query, User $user)` — active calendars where the given user is the owner or has an explicit `CalendarPermission` row

## Events

_None defined on the model._

## Observers

_None registered._

## Key Methods

- `canView(User $user): bool` — returns `true` if the user has system-wide `calendar-view` gate, is the owner, the calendar is `global_viewable`, or the user has any explicit `CalendarPermission` row
- `canCreate(User $user): bool` — returns `true` if the user has `calendar-update` gate, is the owner, the calendar is `global_editable`, or the user has a `create`/`edit`/`delete`/`admin` permission
- `canEdit(User $user): bool` — returns `true` if the user has `calendar-update` gate, is the owner, the calendar is `global_editable`, or the user has an `edit`/`delete`/`admin` permission
- `canDelete(User $user): bool` — returns `true` if the user has `calendar-update` gate, is the owner, the calendar is `global_editable`, or the user has a `delete`/`admin` permission
- `canAdmin(User $user): bool` — returns `true` if the user has `calendar-update` gate, is the owner, or the user has an explicit `admin` permission
- `getUserPermission(User $user): ?string` — returns `'admin'` for the owner, or the `permission_type` of the user's `CalendarPermission` row, or `null` if none
- `grantPermission(User $user, string $permissionType): void` — upserts a `CalendarPermission` row for the user with the given permission level
- `revokePermission(User $user): void` — deletes the user's `CalendarPermission` row
- `isOwnedBy(User $user): bool` — checks whether `owner_id` matches the given user
- `isPersonal(): bool` — returns `true` if `type === CalendarType::PERSONAL`
- `isShared(): bool` — returns `true` if `type === CalendarType::SHARED`
- `isGlobalViewable(): bool` — returns `true` if `global_viewable` is set
- `isGlobalEditable(): bool` — returns `true` if `global_editable` is set
- `transferOwnership(User $newOwner): void` — transfers calendar ownership: revokes any existing permission for the new owner, grants the previous owner `admin`, updates `owner_id`
- `canTransferOwnership(User $user): bool` — returns `true` if the user is the owner or has `calendar-update` gate

## Common Usage

```php
// Create a personal calendar
$calendar = Calendar::create([
    'name'     => 'My Schedule',
    'color'    => '#e74c3c',
    'type'     => CalendarType::PERSONAL,
    'owner_id' => $user->id,
    'is_active' => true,
]);

// Create a shared calendar visible to all
$shared = Calendar::create([
    'name'           => 'Company Events',
    'type'           => CalendarType::SHARED,
    'global_viewable' => true,
    'owner_id'       => $adminUser->id,
    'is_active'      => true,
]);

// Grant a user create-level access
$calendar->grantPermission($user, 'create');

// Check permissions before editing
if ($calendar->canEdit($currentUser)) {
    $calendar->update(['name' => 'Updated Name']);
}

// Query calendars accessible to a user
$myCalendars = Calendar::accessibleByUser($user)->active()->get();

// Transfer ownership
$calendar->transferOwnership($newOwner);
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
