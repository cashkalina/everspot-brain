---
title: WorkOrder Module — Models Index
module: WorkOrder
last_updated: 2026-06-14
---

# WorkOrder Module — Models

This directory contains documentation for every concrete Eloquent model in `modules/WorkOrder/Models/`.

| Model | Table | Description |
|-------|-------|-------------|
| [TimeEntry](./time-entry.md) | `time_entries` | Polymorphic time-log record attached to a work order (or any `HasTimeEntries` model); aggregates into the parent's `time_spent` column. |
| [WorkOrder](./work-order.md) | `work_orders` | Core operational record representing a field task or maintenance request; supports time tracking, recurrence, templating, and staff QR access. |
| [WorkOrderCategory](./work-order-category.md) | `work_order_categories` | Hierarchical classification for work orders; active/inactive flag and optional parent category. |

## Traits (owned by this module)

Module-owned traits live in `modules/work-order/traits/`. See the [global trait registry](../../../system/traits/index.md) for lookup.

| Trait | Deep doc |
|-------|----------|
| HasTimeEntries | [has-time-entries.md](../traits/has-time-entries.md) |
