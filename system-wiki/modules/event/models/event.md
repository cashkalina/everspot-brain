---
model: Event
module: Event
table: events
connection: tenant
primary_source: modules/Event/Models/Event.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Event/Observers/EventObserver.php
  - modules/Event/Providers/EventServiceProvider.php
  - modules/Common/Models/User.php
  - modules/Event/Models/Calendar.php
traits:
  - HasByUserFields
  - SoftDeletes
related_models: [Calendar, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [scheduling, core]
---

# Event

## Overview

The Event model represents a calendar event — a scheduled occurrence with a title, type, date range, optional time range, status, and description. Events are polymorphic via `eventable_type`/`eventable_id`, allowing any module entity (Customer, Interment, Opportunity, etc.) to own events. An event may optionally belong to a [Calendar](./calendar.md), which provides grouping, color, and access-control context.

Events support five types (`interment`, `phone-call`, `meeting`, `service-task`, `general`) and two statuses (`active`, `canceled`). Dates are stored as `date` columns; times are stored as `time` columns and cast through `TimezonedDateTime` for automatic timezone conversion between storage and display. The model exposes a rich set of date/time accessors that compose these columns into human-readable strings and `Carbon` instances adjusted to the active user's timezone.

The `EventObserver` handles important side-effects: after save it syncs date/time changes back to the owning `eventable` (e.g. updates an `Interment`'s dates), dispatches `EventSaved`; on create it copies `cemetery_id` from the eventable and — for interment events — sets the `interment_event_id` on the `Interment` if none is set yet; on delete or restore it reassigns or clears `interment_event_id` and syncs the eventable dates again.

The `cemetery_id` and `config_data` columns exist in the schema but are not in `$fillable`; they are set programmatically by the observer and internal processes respectively.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| eventable_type | varchar | Yes | - | Morph type of the owning entity |
| eventable_id | varchar | Yes | - | Morph ID of the owning entity |
| cemetery_id | bigint | Yes | - | FK → cemeteries: set by observer from the eventable; not mass-assignable |
| type | varchar | No | - | Event type (`interment`, `phone-call`, `meeting`, `service-task`, `general`) |
| title | varchar | No | - | Event title |
| description | text | Yes | - | Optional event description |
| status | varchar | No | - | Event status (`active`, `canceled`) |
| start_date | date | No | - | Start date |
| start_time | time | Yes | - | Start time (stored in UTC, cast via TimezonedDateTime) |
| end_date | date | Yes | - | End date (null means single-day event) |
| end_time | time | Yes | - | End time (stored in UTC, cast via TimezonedDateTime) |
| config_data | json | Yes | - | Arbitrary JSON configuration; not mass-assignable |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |
| calendar_id | bigint | Yes | - | FK → calendars: the calendar this event belongs to |

**Primary key:** `id`

**Foreign keys:** `calendar_id` → `calendars.id` (set null on calendar delete); `cemetery_id` → `cemeteries.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** composite index on `(eventable_type, eventable_id)`; single-column indexes on `start_date`, `status`, `title`, `type`; FK-backing indexes on `calendar_id`, `created_by`, `updated_by`, `deleted_by`; regular index on `cemetery_id`.

## Casts

- `start_date` → `date`
- `end_date` → `date`
- `start_time` → `TimezonedDateTime::class` — automatic UTC ↔ user-timezone conversion for time-of-day storage
- `end_time` → `TimezonedDateTime::class` — automatic UTC ↔ user-timezone conversion for time-of-day storage

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['eventable_type', 'eventable_id', 'calendar_id', 'type', 'title', 'description', 'status', 'start_date', 'end_date', 'start_time', 'end_time']`

**Hidden:** _None._

**Visible:** _None._

**Appends:** _None._ (all accessors are on-demand; none are auto-appended)

**Defaults (`$attributes`):** _None._ (status is defaulted by convention to `'active'` via `$defaultStatus` on `BaseModel`)

**Constants / static config:**
```php
const TYPES = [
    'interment'    => 'Interment Event',
    'phone-call'   => 'Phone Call',
    'meeting'      => 'Meeting',
    'service-task' => 'Service Task',
    'general'      => 'Event',
];

const STATUSES = [
    'active'   => ['label' => 'Active',   'color' => 'success'],
    'canceled' => ['label' => 'Canceled', 'color' => 'danger'],
];

protected static $defaultStatus = 'active';
```

## Accessors & Mutators

- `getFormattedStartDateAttribute(): ?string` — `start_date` formatted as `F j, Y` (e.g. "June 14, 2026")
- `getFormattedEndDateAttribute(): ?string` — `end_date` formatted as `F j, Y`
- `getFormattedStartTimeAttribute(): ?string` — `start_time` formatted as `g:i A` (e.g. "2:30 PM")
- `getFormattedEndTimeAttribute(): ?string` — `end_time` formatted as `g:i A`
- `getFormattedStartDateTimeAttribute(): string` — concatenation of formatted start date and time (space-separated)
- `getFormattedEndDateTimeAttribute(): string` — concatenation of formatted end date and time
- `getFormattedDateDurationAttribute(): string` — start date, with ` - end date` appended only when end differs from start
- `getFormattedTimeDurationAttribute(): string` — start time with ` - end time` appended when end time is present
- `getFormattedStartShortAttribute(): string` — short smart date string; includes day-of-week prefix when start is within the last month
- `getStartDateTimeShortAttribute(): ?string` — compact datetime string adapting format based on how far the date is from now (uses year when far out, ordinal when close); includes time when `start_time` is set
- `getConditionalEndDateAttribute(): ?Carbon` — returns `end_date` only when it differs from `start_date`; null otherwise
- `getStartTimeMeridiemAttribute(): ?string` — `a`-format meridiem of `start_time` (`am`/`pm`)
- `getEndTimeMeridiemAttribute(): ?string` — `a`-format meridiem of `end_time`
- `getConditionalStartTimeMeridiemAttribute(): ?string` — returns start meridiem only when it differs from end meridiem (avoids "2:00 PM - 3:00 PM" redundancy)
- `getFormattedTypeAttribute(): string` — human label from `TYPES` for the event's `type`
- `getStartAttribute(): string` — ISO datetime string combining `start_date` and `start_time` (date only when no time)
- `getEndAttribute(): ?string` — ISO datetime string combining `end_date` and `end_time`; adds one day to a date-only end (FullCalendar exclusive-end convention); null when no end date
- `getStartDateTimeAttribute(): Carbon` — `Carbon` instance from `start_date` + `start_time`, adjusted to the active user's timezone (start of day when no time)
- `getEndDateTimeAttribute(): Carbon` — `Carbon` instance from `end_date` + `end_time`, adjusted to the active user's timezone (end of day when no time; falls back to `start_date` when no end date)

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backing the `created_by` / `updated_by` / `deleted_by` columns
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — events are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `eventable()` — morphTo: the owning entity (may be Customer, Interment, Opportunity, Order, or other eventable models)
- `calendar()` — belongs to [Calendar](./calendar.md): the calendar this event is placed on (nullable)

## Scopes

- `past(Builder $query)` — events whose `start_date` (or `start_time` on the same day) is before now
- `future(Builder $query)` — events whose `start_date` (or `start_time` on the same day) is after now
- `forType(Builder $query, $type)` — filters to the given `type` value; no-op when `$type` is falsy
- `forCalendar(Builder $query, $calendarId)` — filters to the given `calendar_id`; no-op when `$calendarId` is falsy
- `forCalendars(Builder $query, array $calendarIds)` — filters to events in any of the given calendar IDs; no-op when array is empty

## Events

_None defined on the model._ Observer `EventObserver` dispatches application events (see Observers).

## Observers

- `EventObserver` — registered in `Modules\Event\Providers\EventServiceProvider::registerObservers()` (`Event::observe(EventObserver::class)`). Handles:
  - `saved` — calls `updateEventableDateTimes()` (syncs dates back to the owning `Interment` via `updateDateTimes()`), calls `manageIntermentStagesAutomatically()`, dispatches `EventSaved`
  - `created` — copies `cemetery_id` from the eventable when present and saves it; for Interment eventables, sets `interment_event_id` on the `Interment` if none is set yet; dispatches `EventCreated`
  - `deleted` — calls `handleIntermentEventDeletion()` (reassigns or clears `interment_event_id` on the parent `Interment`), calls `updateEventableDateTimes()`
  - `restored` — calls `updateEventableDateTimes()` to re-sync the eventable's dates
  - `forceDeleted` — calls `handleIntermentEventDeletion()` and `updateEventableDateTimes()`

## Key Methods

- `manageIntermentStagesAutomatically(): void` — delegates to `$this->eventable->manageStagesAutomatically()` when the eventable is an `Interment`; invoked by the observer after save
- `getColor(): string` — returns the owning calendar's color (via `Calendar::getColor()`), or `#3788d8` when no calendar is set; used by calendar UI renderers
- `getTextColor()` — returns the owning calendar's text color (via `Calendar::getTextColor()`) for contrast rendering
- `getModelInferredName(): ?string` — returns `$this->title`; satisfies the `BaseModel` interface for display purposes
- `isOnSharedCalendar(): bool` — returns `true` when the event belongs to a calendar and that calendar's `type` is `shared`
- `getCalendarPermissions(User $user): ?string` — delegates to `Calendar::getUserPermission($user)` and returns the user's permission level on the calendar (null when no calendar)

## Common Usage

```php
// Create a general event for a customer
$event = Event::create([
    'eventable_type' => Customer::class,
    'eventable_id'   => $customer->id,
    'calendar_id'    => $calendar->id,
    'type'           => 'meeting',
    'title'          => 'Initial consultation',
    'status'         => 'active',
    'start_date'     => '2026-07-01',
    'start_time'     => '10:00:00',
    'end_date'       => '2026-07-01',
    'end_time'       => '11:00:00',
]);

// Query upcoming events on a calendar
$upcoming = Event::forCalendar($calendar->id)->future()->get();

// Query past events of a specific type
$pastCalls = Event::past()->forType('phone-call')->get();

// Display formatted date/time
echo $event->formatted_start_date_time;  // "July 1, 2026 10:00 AM"
echo $event->formatted_date_duration;   // "July 1, 2026"

// Get timezone-adjusted Carbon for UI
$startCarbon = $event->start_date_time;  // Carbon in user's timezone

// Check calendar access for a user
$permission = $event->getCalendarPermissions($user); // 'admin', 'edit', etc.
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
