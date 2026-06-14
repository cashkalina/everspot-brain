---
title: Event Module — Models
module: Event
last_updated: 2026-06-14
---

# Event Module — Models

This directory contains documentation for the three concrete Eloquent models in the `modules/Event/` module.

| Model | Table | Description |
|-------|-------|-------------|
| [Calendar](./calendar.md) | `calendars` | Organizes events into named, colored containers owned by a user; supports global and per-user access control |
| [CalendarPermission](./calendar-permission.md) | `calendar_permissions` | Per-user permission record for a calendar (`view`, `create`, `edit`, `delete`, `admin`) |
| [Event](./event.md) | `events` | A scheduled occurrence owned by any polymorphic eventable entity; supports date/time ranges, types, statuses, and calendar grouping |

## Module Traits

Event-module-owned traits are documented in [`../traits/`](../traits/index.md):

- [HasColor](../traits/has-color.md) — hex color storage with contrast and opacity helpers (used by `Calendar`)
