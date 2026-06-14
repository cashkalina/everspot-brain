---
title: Sync Command
purpose: Incremental update of all affected documents since the last sync baseline
last_updated: 2026-06-14
---

# Sync

**Purpose:** Incremental update of all affected documents since the last sync baseline.

**Operation type:** Write

**Inputs:**
- `meta/wiki-state.json` — contains `synced_through` commit hash
- `wiki.config.json` — Everspot repository location
- Current `schema/central.json` and `schema/tenant.json`

**Preconditions:**
- `synced_through` is set and points to an ancestor of current `origin/main`
- Everspot repository is accessible
- Schema snapshots exist

**Process:**

### Gather changes

1. Read `synced_through` from `meta/wiki-state.json`.
2. Fetch `origin/main` in the Everspot repository: `git fetch origin main`.
3. List all commits between `synced_through` and `origin/main`:
   ```bash
   git log --pretty=format:"%H" <synced_through>..origin/main
   ```
4. For each commit, list changed files:
   ```bash
   git show --name-only --pretty=format:"" <commit-hash>
   ```

### Detect schema changes

For each database connection (central, tenant):

1. Identify migration paths from `../conventions.md` (e.g., `database/migrations/` for central, `database/migrations/tenant/` for tenant).
2. Check if any commits since `synced_through` touched files in those paths.
3. If yes, regenerate that connection's schema snapshot ([Snapshot-schema](./snapshot-schema.md)).
4. Diff the regenerated snapshot against the previous committed snapshot:
   - For each table: compare column list, types, nullable, defaults, indexes, foreign keys.
   - Record tables with any difference as "changed tables."
5. If no migration changes, no schema regeneration needed — the existing snapshot is current.

### Map changes to affected documents

For each changed file from [Gather changes](#gather-changes) and each changed table from [Detect schema changes](#detect-schema-changes):

**Per changed file:**

1. If the file is a model class (in `modules/*/Models/` or `app/Models/`), add the document for that model to the affected set.
2. If the file is a trait: **run [Generate-trait-doc](./generate-trait-doc.md) for it** — being existence/currency-based, it will detect that the trait source changed since the deep doc's `built_at` and rebuild the deep doc + registry row. Then grep all model docs' frontmatter `traits:` for that trait's short name and add those models to the affected set (their `## Traits` links and provenance markers may need refresh). If the file is a parent class or observer: grep all docs' frontmatter `source_paths` (and `primary_source`) for the path. In all cases, do not trust stored fields alone — re-derive for each candidate.
3. If the file is in a migration path, the changed tables handle it (see [Detect schema changes](#detect-schema-changes)).

**Per changed table:**

1. Find the document whose frontmatter `table:` matches this table name.
2. Add to affected set.

**Re-derive source_paths before trusting membership:**

For each candidate document from the above mapping:

1. Re-derive its `source_paths` using the same logic as [Generate › Derive primary_source, source_paths, and traits](./generate.md#derive-primary_source-source_paths-and-traits), reading from current `origin/main`.
2. If the changed file appears in the re-derived set, confirm the document is affected.
3. If a new dependency (trait, observer) was added since the document was last built, the re-derivation will catch it even though the stored `source_paths` did not include it.

This re-derivation step closes the gap where a newly added dependency would otherwise leave a document falsely reporting current.

### Regenerate affected documents

For each document in the affected set:

1. Perform the same process as [Generate](./generate.md), but updating the existing file rather than creating new.
2. Preserve human-authored content blocks ([Human-content reconciliation](#human-content-reconciliation)).
3. Re-derive `primary_source`, `source_paths`, `traits`, and `related_models` — always from scratch, never trusted from the existing frontmatter.
4. Re-render Schema from the current snapshot.
5. Re-parse relationships, methods, scopes from current `origin/main` source.
6. Validate ([Generate › Validation gate](./generate.md#validation-gate)).
7. Stamp `built_at` with the current `origin/main` commit.
8. Update `last_updated` to current date.

### Handle lifecycle

**New models:**

If a new model class appears in commits since `synced_through`:

1. Detect by finding model classes in changed files that have no existing document.
2. Run [Generate](./generate.md) for each.

**Removed models:**

If a model class was deleted in commits since `synced_through`:

1. Detect by identifying documents whose `source_paths` primary model file no longer exists.
2. Do not delete the document.
3. Mark `deprecated: true` in frontmatter.
4. If the commit or surrounding commits suggest a successor (rename, split, merge), add `successor: <new-model-name>` to frontmatter.
5. If the model was removed with no clear successor, leave `successor` unset.
6. Preserve the entire document including human-authored blocks — a human will reconcile.

**Renames, splits, merges:**

These are not auto-detected via git rename heuristics. Surface them for human confirmation:

1. If a model file was deleted and a new one appeared with similar structure, flag for review.
2. Do not auto-migrate human content.
3. Report in sync output: "Possible rename detected: OldModel -> NewModel. Requires human reconciliation."

### Fix or flag inbound links

When a model is deprecated:

1. Grep the wiki for links to the deprecated document.
2. If `successor` is set, attempt to rewrite links automatically (replace `[OldModel](path/to/old.md)` with `[NewModel](path/to/new.md)`).
3. If no successor or rewrite is ambiguous, flag the linking documents in the sync report.

### Human-content reconciliation

When regenerating a document:

1. Parse the existing file for `<!-- human:begin -->` and `<!-- human:end -->` markers.
2. Extract all content between these markers.
3. Regenerate all AI-owned sections (everything outside human blocks).
4. Reinsert the extracted human content exactly as it was.
5. **Targeted invalidation flagging:**
   - Parse the human block for identifiers (column names, method names, model names).
   - Compare identifiers against the changes being applied: if a changed column, method, or model is explicitly named in the human block, add `<!-- possibly-invalidated: <reason> -->` immediately after `<!-- human:begin -->`.
   - Example: If the human block mentions "status column controls payment flow" and the `status` column type changed, flag it. If the block discusses business rules about refunds and only a typo in a comment changed, do not flag.
6. Leave flagged blocks for human review; surface in audit.

This prevents false alarms (every sync flagging every human block) while catching real invalidations.

### Advance synced_through

**Resumability principle:** `synced_through` advances only past successfully processed changes.

1. After regenerating all affected documents and validating them, identify the latest commit that was fully processed (all its affected documents successfully regenerated).
2. Update `meta/wiki-state.json` with `synced_through: <latest-fully-processed-commit>`.
3. Commit the updated `wiki-state.json`, schema snapshots (if regenerated), and all regenerated documents.

**On partial failure:**

1. If any document fails validation or regeneration, halt sync.
2. Do not advance `synced_through` past the commit that introduced the failure.
3. Report failed documents with detailed error messages.
4. On next sync run, reprocess from the same `synced_through` baseline, attempting the failed documents again.

This ensures no commit's changes are silently skipped.

### Report

Output a summary:

- Commits processed: `<synced_through>..origin/main` range
- Schema snapshots regenerated: central, tenant, both, or neither
- Tables changed: count and list
- Documents affected: count and list
- New documents created: count and list
- Documents deprecated: count and list
- Possible renames/splits: list for human review
- Validation failures: detailed list
- New `synced_through` value

**Outputs:**
- Updated documents (regenerated, validated, stamped)
- New documents (for new models)
- Deprecated documents (marked, not deleted)
- Updated `meta/wiki-state.json` with new `synced_through`
- Regenerated schema snapshots (if migrations changed)
- Git commit with all changes

**Error handling:**
- `synced_through` not an ancestor of `origin/main` — fail, require manual resolution
- Schema snapshot regeneration failure — fail, do not advance `synced_through`
- Document validation failure — halt, report, do not advance past that commit
- Unresolvable dependency (missing trait, parent) — fail document, halt sync
- Human content block parse failure — fail, require manual fix
