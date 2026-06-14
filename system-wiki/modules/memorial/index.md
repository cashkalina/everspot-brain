---
title: Memorial Module
module: Memorial
last_updated: 2026-06-14
---

# Memorial Module

The Memorial module manages physical memorial markers — headstones, plaques, and monuments — associated with cemetery properties and the people they commemorate. It tracks the full lifecycle from ordering through installation, with support for dimensions, materials, partial dates, and tenant-configured status workflows.

## Contents

- [Models](./models/index.md) — `Memorial`, `MemorialPerson`

## Key Concepts

- **Memorials** carry physical specifications (dimensions, material, color, UOM), vendor links (manufacturer, dealer, installer), and three partial-date milestones (ordered, shipped, installed).
- **MemorialPersons** link a memorial to the individuals it commemorates, capturing their names, partial birth/death dates, and inscription text. Each person may optionally be linked to a `Customer` and an `Interment` record.
- The memorial's `display_name` is auto-generated from its people's names unless `manual_name = true`.
- Status values are tenant-configured via `memorials-module-config` settings rather than hard-coded.
- Memorials can be flagged as templates (`is_template = true`) for re-use as starting configurations.
