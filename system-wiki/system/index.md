---
title: System Documentation
purpose: Cross-cutting architecture and system-wide concepts
last_updated: 2026-06-12
---

# System Documentation

This directory contains cross-cutting system documentation for Everspot — concepts and architecture that span multiple modules.

## Overview

The system documentation provides context for the model documentation. It is maintained at lighter depth than the model docs, with the goal of giving each cross-cutting concept a canonical place to link to.

## Subsystem Documents

This is the **canonical registry of subsystem documents** (foundation.md §5.6). Each documents a bounded, cross-model mechanism following `meta/subsystem-template.md`. Foundation points here rather than listing them itself, so adding a subsystem doc costs one row here and **zero** lines in foundation.

| Document | Mechanism | Status |
|---|---|---|
| **[imports.md](./imports.md)** | Spreadsheet (Excel/CSV) import: `BaseImport` contract, Livewire→Job→Excel flow, registry. Per-import column docs live in each module's `imports/` folder (18 imports + 1 multi-sheet variant). | active (reference example) |

_Candidates from `meta/non-model-surface.md` (not yet written): events/listeners graph, service families, jobs._

## Planned Documents

The following system documents are planned for future phases:

- **architecture.md** — Overall system architecture, Laravel structure, key patterns
- **multi-tenancy.md** — How multi-tenancy works (stancl/tenancy), central vs tenant databases
- **database.md** — Database connections, migration strategy, schema organization
- **authentication.md** — Authentication and authorization patterns
- **integrations.md** — External integrations (QuickBooks, payment gateways, etc.)

These will be created as needed to support model documentation and provide linking targets.

## Core Models

See `./models/` for documentation of models in `app/Models/` (Laravel's core models directory).

---

**Status:** Placeholder directory for Phase 1. Documents will be created in later phases.
