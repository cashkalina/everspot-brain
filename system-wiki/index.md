---
title: Everspot System Wiki
purpose: Master entry point
last_updated: 2026-06-12
---

# Everspot System Wiki

This is the AI-maintained internal documentation repository for the Everspot cemetery-management software. The wiki's primary purpose is to document the data model comprehensively and provide searchable, current documentation optimized for AI consumption.

## Quick Navigation

- **[System Documentation](./system/index.md)** — Cross-cutting architecture, multi-tenancy, database, authentication, integrations
- **[Module Documentation](./modules/index.md)** — PRIMARY FOCUS: per-module model documentation
- **[Meta Documentation](./meta/foundation.md)** — How this wiki works, maintenance procedures, conventions

## Purpose

The wiki documents what Everspot stores, how data is structured, and how models relate. It is optimized for Claude Code to answer questions, assist with development, and reason about the system. Internal staff are a secondary audience.

## Structure

```
system/          Cross-cutting system documentation
  models/        Core app/Models documentation
modules/         Per-module documentation (PRIMARY FOCUS)
  [module]/
    models/      Model documentation for this module
schema/          Committed schema snapshots (central.json, tenant.json)
meta/            Wiki's own documentation and operating procedures
```

## How to Use This Wiki

### For AI Agents (Claude Code)
Read `CLAUDE.md` for standing operating instructions, then `meta/foundation.md` for the full specification. Use native search tools (Grep, Glob) to find models, relationships, and concepts.

### For Humans
Navigate via the structure above. Model documents live in `modules/[module-name]/models/`. Cross-cutting concepts are in `system/`. All documents are markdown with YAML frontmatter.

## Coverage Status

Run the audit to check coverage, staleness, and link integrity:
```
See meta/commands.md for audit command
```

## Maintenance

This wiki follows a **single-writer model**. Write operations (sync, snapshot, generate) are performed by one designated maintainer (or CI). All other users consume read-only.

See `meta/foundation.md` §6 for the maintenance model and `meta/runbook.md` (when created) for operational procedures.

## Freshness

Documents are current when:
1. Their table is unchanged in the latest schema snapshot
2. No commits since `built_at` have touched their `source_paths`

The canonical branch is `main`. All documentation is generated against `origin/main`.

---

**Last synced through:** See `meta/wiki-state.json`
