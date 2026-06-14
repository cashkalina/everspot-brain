---
title: Everspot System Wiki — Command Specifications
status: foundational
version: 2
last_updated: 2026-06-14
---

# Everspot System Wiki — Command Specifications

This document provides detailed specifications for all wiki maintenance operations. It is the authoritative reference for implementing and executing these commands. This specification assumes familiarity with `meta/foundation.md`, which defines the architecture, principles, and maintenance model these commands implement.

**Audience:** AI agents (Claude Code) executing these commands and the human maintainer who supervises them.

**Relationship to foundation.md:** The foundation defines what the wiki is and how it works conceptually. This document specifies exactly how to perform each maintenance operation.

---

## Commands

- [Generate](./generate.md) — create a single new model document from scratch
- [Generate-trait-doc](./generate-trait-doc.md) — create or regenerate the deep documentation for a single trait
- [Sync](./sync.md) — incremental update of all affected documents since the last sync baseline
- [Snapshot-schema](./snapshot-schema.md) — regenerate schema JSONs from live, migrated databases
- [Update](./update.md) — force-regenerate a single existing model document, ignoring freshness
- [Audit](./audit.md) — surface issues without fixing them (read-only)
- [Review-coverage](./review-coverage.md) — analyze the fallback log to identify recurring gaps (read-only)
- [Bootstrap](./bootstrap.md) — perform the initial full build of the wiki

---

## 1. Command Overview

All commands fall into two categories:

- **Write operations** (sync, generate, generate-trait-doc, update, snapshot-schema, bootstrap) — modify wiki files, regenerate snapshots, stamp commits. Run only by the designated maintainer per foundation §3.5, against `origin/main`.
- **Read-only operations** (audit, review-coverage) — surface issues and patterns without making changes. Runnable by anyone.

Every command that reads Everspot source uses `git show origin/main:<path>` from the Everspot repository location specified in `wiki.config.json`, never reading the working tree. This makes branch state and local modifications irrelevant.

---

## 9. Command Execution Principles

### Reading Everspot source

**Always via git show:**

Every read of an Everspot file uses:

```bash
git show origin/main:<relative-path-from-everspot-root>
```

Never read from the working tree. This makes:

- Branch state irrelevant (feature branches, dirty working trees, stashes)
- Everspot config (`wiki.config.json`) need only specify repository location, not assume a specific branch checked out
- All commands idempotent with respect to Everspot's local state

### Source_paths derivation

**Never hand-maintained:**

The `source_paths` frontmatter array is always computed, never manually edited. Every write operation re-derives it from scratch:

1. Start with the model class file.
2. Parse the file, extract traits and parent classes.
3. Recursively include traits' files and their dependencies.
4. Grep observer registrations.
5. Include inverse relationship model files.

This ensures:

- Newly added traits, observers, or parent classes are caught immediately on next regeneration
- Staleness checks based on `source_paths` are reliable
- No manual bookkeeping to maintain

### Connection determination

**Derived from snapshot membership:**

The model's database connection is not manually assigned. It is:

1. Inferred from the model's `$connection` property or conventional default.
2. Validated by checking which schema snapshot contains the model's table.
3. If inference and snapshot membership conflict, the command fails and requires investigation.

This prevents:

- Incorrect connection tags from manual error
- Documents claiming a table is central when it is actually tenant or vice versa

### Validation gate

**All structured content validated before commit:**

Every write operation applies validation:

1. **Schema section** — diffed against the authoritative snapshot. Column name, type, nullable, default must match exactly.
2. **Relationships** — each documented relationship must have a corresponding method in the model source, related model must exist.
3. **Methods** — documented method signatures must match parsed signatures from source.

Validation failures:

- Block the commit (for Generate, Update, Sync).
- Produce detailed error messages (which column mismatched, which method signature wrong).
- Are surfaced in Audit for existing documents.

This ensures the wiki does not ship incorrect schema or relationship information.

### Human content reconciliation

**Marked blocks are sacred:**

Content between `<!-- human:begin -->` and `<!-- human:end -->` is never overwritten:

1. Extracted before regeneration.
2. Reinserted exactly as-is after regeneration.
3. Flagged `possibly-invalidated` only when a named identifier in the block is touched by the change.

**Targeted invalidation:**

- Parse the human block for column names, method names, model names.
- Compare against the specific changes in this sync.
- Flag only if a match is found.
- Avoid flagging every block on every sync (alarm fatigue).

This preserves human insight while surfacing genuine invalidations.

### Resumability and partial failure

**Sync advances only past successful work:**

When Sync processes multiple commits and documents:

1. Process commits in order.
2. For each commit, regenerate all affected documents.
3. If any document fails validation, halt.
4. Advance `synced_through` only to the last commit whose documents all succeeded.
5. On next sync, reprocess from that point.

This ensures:

- No commit's changes are silently skipped.
- A transient failure (missing file, network issue, parse error) is retried.
- Sync can be interrupted and resumed without losing progress.

---

## 10. Relationship to Other Meta Documents

- **foundation.md** — defines the architecture, principles, and maintenance model these commands implement.
- **conventions.md** — provides the model-enumeration rule, tag vocabulary, completeness criteria, and naming conventions referenced by these commands.
- **model-template.md** — the structure and section definitions applied by Generate and Sync.
- **runbook.md** — step-by-step human instructions for executing these commands in practice (to be written later).

The `meta/commands/` directory is the authoritative specification. Where foundation.md describes intent, these documents specify mechanism. Where conventions.md establishes rules, these documents specify how those rules are applied during execution.

---

## 11. Summary Table

| Command | Type | Purpose | Key Inputs | Key Outputs |
|---------|------|---------|------------|-------------|
| **[Generate](./generate.md)** | Write | Create new model doc | Model class path | New .md file, validated, stamped |
| **[Sync](./sync.md)** | Write | Incremental update all affected docs | synced_through, origin/main | Updated docs, new synced_through, commit |
| **[Snapshot-schema](./snapshot-schema.md)** | Write | Regenerate schema JSONs from live DBs | Runnable Everspot, migrated DBs | central.json, tenant.json with snapshot_commit |
| **[Update](./update.md)** | Write | Force-regenerate single doc | Model doc path or name | Updated .md file, validated, stamped |
| **[Audit](./audit.md)** | Read-only | Surface issues without fixing | Current wiki + Everspot source | Report: coverage, staleness, links, deprecations, notes, validation |
| **[Review-coverage](./review-coverage.md)** | Read-only | Analyze fallback log, propose adjustments | .fallback.log | Report: patterns, proposals |
| **[Bootstrap](./bootstrap.md)** | Write (deferred spec) | Initial full build | Runnable Everspot, empty wiki | Full doc set, snapshots, first synced_through |

---

**End of Command Specifications**

All operations defined here are implemented by Claude Code executing these specifications as prompts. The human maintainer supervises, reviews reports, and reconciles flagged human content. CI will eventually assume the write operations once the process is proven.
