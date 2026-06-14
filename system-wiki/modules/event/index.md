---
title: Event Module
module: Event
last_updated: 2026-06-14
---

# Event Module

The Event module provides calendar and scheduling functionality for Everspot. It allows any entity in the system to own calendar events via a polymorphic `eventable` relationship, organizes those events into color-coded calendars with hierarchical per-user access control, and integrates with other modules (notably Interment) to sync dates and drive workflow stage transitions automatically.

## Contents

| Directory | Description |
|-----------|-------------|
| [models/](./models/index.md) | Calendar, CalendarPermission, Event — the three module models |
| [traits/](./traits/index.md) | HasColor — hex color storage and UI helpers |

## Key Concepts

- **Calendars** are user-owned containers with optional global visibility/editability; per-user access is delegated via `CalendarPermission` records with five levels (`view` → `admin`).
- **Events** are polymorphic — any module entity can have events attached. The `EventObserver` drives side effects: syncing cemetery IDs, managing interment stage transitions, and keeping `Interment.interment_event_id` consistent as events are created or deleted.
- **Colors** flow from calendar to event — `Event::getColor()` delegates to its calendar's `HasColor`-contributed `getColor()`.
- **Timezones** — start/end times are stored as UTC via `TimezonedDateTime` cast and converted to the active user's timezone by accessors on the Event model.
