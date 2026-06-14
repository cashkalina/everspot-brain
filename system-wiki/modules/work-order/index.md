---
title: WorkOrder Module
module: WorkOrder
last_updated: 2026-06-14
---

# WorkOrder Module

The WorkOrder module provides field task management for the cemetery — from grounds maintenance requests to monument repair jobs. It is the operational layer that bridges administrative scheduling with field staff execution.

## Key Concepts

- **Work Orders** — the central record type: a task scoped to a cemetery, optionally linked to a customer, interment, memorials, and properties. Carries status, priority, due date, and assigned staff.
- **Time Entries** — polymorphic time-log records attached to a work order. Staff log hours, and the total aggregates automatically into the work order's `time_spent` column.
- **Work Order Categories** — hierarchical classification tags (with an optional parent-child structure) for filtering and reporting.
- **Recurrence** — work orders can be made recurring via the `Repeatable` trait, allowing scheduled maintenance tasks to generate new instances automatically.
- **Template system** — work orders can be saved as reusable templates (`is_template = true`) and cloned as new jobs.
- **Staff QR access** — each work order has a unique `staff_access_key` that can be rendered as a QR code for field staff to view the work order without authenticating.

## Directory Structure

```
modules/work-order/
├── index.md               # This file
├── models/
│   ├── index.md           # Models index
│   ├── time-entry.md      # TimeEntry model
│   ├── work-order.md      # WorkOrder model
│   └── work-order-category.md  # WorkOrderCategory model
└── traits/
    ├── index.md           # Traits index
    └── has-time-entries.md # HasTimeEntries trait deep doc
```

## Models

- [TimeEntry](./models/time-entry.md) — polymorphic time-log records
- [WorkOrder](./models/work-order.md) — the core work task record
- [WorkOrderCategory](./models/work-order-category.md) — hierarchical category classification

## Module-Owned Traits

- [HasTimeEntries](./traits/has-time-entries.md) — enables polymorphic time tracking on any model
