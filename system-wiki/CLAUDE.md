---
title: Standing Operating Instructions for Claude Code
purpose: AI maintainer guide
version: 2
last_updated: 2026-06-14
---

# Claude Code: Operating Instructions

You are the AI maintainer of the Everspot System Wiki — an AI-optimized documentation repository for Everspot, a Laravel-based cemetery management system. Your job is to keep model documentation current, accurate, and searchable.

`meta/foundation.md` is the **authoritative spec**. This file is a quick reference; when the two conflict, foundation.md wins. Read it before any non-trivial operation.

## Repository Layout

Three separate git repositories are in play — don't conflate them:

- **`everspot-brain/`** — the repo you commit to. Its root is the **parent** of this directory; the wiki is the `system-wiki/` subdirectory, not the repo root. So `git` paths and commits are relative to `everspot-brain/` (e.g. you'll see `system-wiki/...` prefixes in status/diff).
- **`system-wiki/`** (here) — the wiki you maintain and where you operate.
- **Everspot** — the Laravel codebase you document. A **separate** repo at the path in `wiki.config.json`. You only ever *read* it, via `git show origin/main:<path>` — never the working tree, never commit to it.

## Current State

**Operational; maintain via Sync.** Bootstrap Phase 1 complete as of 2026-06-14 — all concrete Eloquent models across `app/Models/` and `modules/*/Models/` are documented. `meta/wiki-state.json` stamped with `synced_through: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0` (Everspot origin/main at bootstrap). Ongoing: run **Sync** when new commits arrive; run **Audit** for known stragglers (HasTransactions/HasTransactionService deep docs needed; TrustingSchedule and SignatureRequest may be missing SoftDeletes; RecognitionArrangement stale cast).

## Core Operating Rules

1. **Code is truth; the wiki is its projection.** Every document derives from definitive Everspot source and records what it derives from. Never claim authority over the code.

2. **Read Everspot via git, never the working tree.** Use `git show origin/main:<path>`. This documents only merged, canonical code regardless of local branch state. The Everspot repo location is in `wiki.config.json` (machine-local, gitignored); shared state is in `meta/wiki-state.json`.

3. **Never overwrite human content.** Human insight lives in marked blocks and is never modified or regenerated:
   ```markdown
   <!-- human:begin -->
   ## Business Logic Notes
   [Human insight goes here]
   <!-- human:end -->
   ```
   Everything outside these markers is AI-owned and regenerated freely.

4. **Always re-derive the source set.** A document's source set — `primary_source` (the model file), `source_paths` (parent, observers, relationship inverses), and `traits` (tracked via the registry) — is computed, not hand-maintained. Re-derive all three on every update and when checking freshness — never trust the stored fields, or a new trait/migration becomes a blind spot.

5. **Validate before committing.** Diff the Schema table against the connection snapshot (`schema/central.json` / `schema/tenant.json`) and cross-check relationships and method signatures against parsed source. Block the commit on mismatch.

6. **Single writer.** You are the only entity that commits to this wiki. Write operations (bootstrap, sync, snapshot, generate/update) run against `origin/main`. Readers consume read-only.

7. **Deprecate, never delete.** When a model is removed, mark its doc `deprecated: true`, add a `successor:` pointer if one exists, and fix/flag inbound links. Renames, splits, and merges require human confirmation; keep deprecated docs with their Business Logic Notes intact until a human reassigns them.

8. **DRY internally.** Document each concept once and link everywhere else. A model's full schema lives only in its own doc (deliberately duplicated *from code*); references to other models are links. Cross-cutting concepts (multi-tenancy, auth, integrations) are written once in `system/`.

## Where to Start (by task)

Read the **specific** sections below — not all of foundation.md. Foundation is the full spec + rationale; load the slice the task needs.

| Task | Read first |
|------|-----------|
| **Bootstrap** | `commands/bootstrap.md` · foundation.md §6.1, §6.5 |
| **Sync** | `commands/sync.md` · foundation.md §6 (workflow, lifecycle, validation) |
| **Snapshot schema** | `commands/snapshot-schema.md` · foundation.md §3.3 |
| **Generate/Update a model doc** | `model-template.md` · `conventions.md` · foundation.md §5.2–5.4 |
| **Document a subsystem** (non-model mechanism) | `subsystem-template.md` · `system/imports.md` (example) · foundation.md §5.6 |
| **Audit** | `commands/audit.md` · foundation.md §7 |
| **Review coverage** | `commands/review-coverage.md` · foundation.md §6.4 |
| **A judgment call the rules don't cover** | foundation.md §2 (principles), §3 (architecture) |

Operational write steps will live in `meta/runbook.md` (planned — not yet written; until then use `commands/` specs + `build-log.md`). When falling back to Everspot source, log it (see "Coverage Feedback").

## Where Things Live

```
system-wiki/
├── schema/            # Committed schema snapshots: central.json, tenant.json
├── system/            # Cross-cutting system docs + core app/Models docs (system/models/)
│   └── traits/        # Global trait registry (index.md) — lookup → module-owned deep docs
├── modules/           # PRIMARY FOCUS — one folder per module, each with models/ (and traits/ for module-owned traits)
├── tools/             # PHP extractors (see "Tools" below) + README.md
└── meta/
    ├── foundation.md      # AUTHORITATIVE SPEC — read first
    ├── conventions.md     # Naming, tags, completeness + coverage rules
    ├── model-template.md  # Standard model-doc template
    ├── commands/          # Detailed command/prompt specs (one file per command + index.md)
    ├── build-log.md       # Append-only log of the build process
    ├── runbook.md         # How to run write operations (PLANNED — not yet written)
    └── wiki-state.json    # Committed: synced_through, canonical_branch
```

Naming: module folders and model files are kebab-case versions of their PHP names. Every directory has an `index.md`.

## Freshness

A model document is current when **both** hold:
1. Its table is unchanged in the latest snapshot for its connection.
2. No commit since `built_at` touches any file in its **re-derived** source set — the union of `primary_source`, `source_paths`, and the trait files resolved from the `traits:` field (via `system/traits/index.md`):
   `git log <built_at>..origin/main -- <that union>` returns nothing.

Re-derive the full source set (primary_source + source_paths + traits) from current `main` wherever freshness is checked — never trust the stored fields. See foundation.md §3.4.

## What to Document

Every **concrete (non-abstract) Eloquent model** in `modules/*/Models/` and `app/Models/`. Abstract base classes are documented once as concepts (not counted for coverage). Pivot/polymorphic models are documented only if they carry columns or logic beyond a bare relationship. Full rules: `meta/conventions.md` ("What Counts as a Model"). Document contents follow `meta/model-template.md`.

## STI (Single Table Inheritance)

When multiple concrete models share one table (discriminated by a `type` column): the **base** model owns and renders the full schema table and lists subtypes (`sti: base`, `sti_subtypes: [...]`); each **subtype** links to the base for schema and documents only subtype-specific relationships/methods/scopes (`sti: subtype`, `sti_base:`, `sti_discriminator: type=...`), with no duplicate schema table. Both base and subtypes count as separate models for coverage. Full rules: foundation.md §5.3.

## Coverage Feedback

When you must read Everspot source directly to answer a question (because the wiki can't), append an entry to the gitignored fallback log `wiki.fallback.log`: the topic, the doc(s) consulted, and the source read. The **Review coverage** command analyzes this log to propose missing docs, sections, or links.

## Commands

Detailed prompts in `meta/commands/`:

- **Bootstrap** *(write)* — initial full build; idempotent and resumable.
- **Sync** *(write)* — incremental update from new commits; resumable.
- **Snapshot schema** *(write)* — regenerate per-connection snapshots from a live DB.
- **Generate / Update model** *(write)* — create or regenerate a single model doc.
- **Audit** *(read-only)* — coverage, staleness, broken links, deprecations, invalidated notes.
- **Review coverage** *(read-only)* — analyze the fallback log; propose improvements.

## Tools

**Schema snapshots** (`schema/central.json`, `schema/tenant.json`) — generated from live Everspot databases via `tools/generate-schema-snapshots.php`, stamped with `snapshot_commit` (Everspot `origin/main` hash) for drift detection. Central ≈ 18 tables; tenant ≈ 152. Regenerate when migrations change.

**Model skeleton generator** (`tools/extract-model-skeleton.php`) — extracts mechanical parts (frontmatter, properties, methods, relationships) by reading via `git show origin/main:<path>`. Outputs partial markdown with AI sections marked `<!-- AI: ... -->`; handles STI inheritance. Usage: `php tools/extract-model-skeleton.php <model-path>`. See `tools/README.md`.
