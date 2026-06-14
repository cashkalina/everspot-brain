---
title: Audit Command
purpose: Surface issues without fixing them
last_updated: 2026-06-14
---

# Audit

**Purpose:** Surface issues without fixing them. Re-derive all dependencies from current `origin/main` to ensure staleness checks are accurate.

**Operation type:** Read-only

**Inputs:**
- Current wiki repository state
- `wiki.config.json` for Everspot repository location
- Current `schema/central.json` and `schema/tenant.json`

**Preconditions:**
- None (can run in any state, even with stale or broken documents)

**Process:**

### Coverage check

**Goal:** Find models that should have documentation but don't.

1. Read the model-enumeration rule from `../conventions.md` (concrete Eloquent classes in `modules/*/Models/` and `app/Models/`, excluding abstract base classes, excluding bare pivot models per the rule).
2. List all model classes in `origin/main` matching the rule:
   ```bash
   git ls-tree -r --name-only origin/main | grep -E 'modules/.*/Models/.*\.php|app/Models/.*\.php'
   ```
3. For each file, check if it is abstract (parse `abstract class`), check if it is a bare pivot (no custom columns or logic per conventions rule).
4. For each in-scope model, grep wiki frontmatter for `model: <ClassName>`.
5. Report models with no corresponding document.

**Trait-doc coverage:**

6. Collect every distinct trait across all model docs' `traits:` frontmatter.
7. For each, confirm `system/traits/index.md` has a row and that its **Deep doc** link points to an existing file (not `_pending_`/missing).
8. Report any trait that is used by a model but lacks a built-out deep doc.

### Staleness check

**Goal:** Find documents whose content is outdated.

For each model document:

1. **Re-derive the full source set** from current `origin/main` using [Generate › Derive primary_source, source_paths, and traits](./generate.md#derive-primary_source-source_paths-and-traits) logic — `primary_source` + `source_paths` + the trait files resolved from `traits:` (via the registry). Do not trust the stored frontmatter.
2. **Check source freshness:**
   ```bash
   git log <built_at>..origin/main -- <re-derived primary_source + source_paths + trait paths>
   ```
   If any commits appear, the document is stale on the source axis. (A changed trait file also makes the trait's own deep doc stale; [Generate-trait-doc](./generate-trait-doc.md) detects that independently via its own `built_at`.)

3. **Check schema freshness:**
   - Find the document's connection and table from frontmatter.
   - Check the snapshot's `snapshot_commit`.
   - If `snapshot_commit` is ahead of the document's `built_at`, check if the table changed:
     - Retrieve the table definition from the snapshot at `built_at` (via git or stored historical snapshots if available, or assume changed if not provable).
     - Compare to current snapshot. If different, document is stale on schema axis.

4. **Check review_after (for system docs):**
   - If frontmatter has `review_after: <date>` and today's date is past it, flag as stale.

5. Report all stale documents with reason (source touched, schema changed, review_after passed).

### Link integrity check

**Goal:** Find broken internal links.

1. Grep all `.md` files for markdown links: `\[.*?\]\((.*?)\)`.
2. Extract link targets. For relative links, resolve to absolute wiki paths.
3. Check if each target file exists.
4. Report broken links: source document, link text, target path.

### Deprecation check

**Goal:** Find deprecated documents that still have inbound links.

1. Grep frontmatter for `deprecated: true`.
2. For each deprecated document, grep the wiki for links to it (excluding the deprecated doc's own `successor` mention).
3. Report deprecated docs with inbound links, listing the linking documents.

### Invalidated human notes check

**Goal:** Surface human-authored blocks flagged for review.

1. Grep all `.md` files for `<!-- possibly-invalidated`.
2. Parse the flagged blocks and their reasons.
3. Report each flagged block: document, section, reason.

### Validation check

**Goal:** Find documents whose structured sections don't match source.

For each model document:

1. Re-parse the Schema section.
2. Diff against the current snapshot (same as [Generate › Validation gate](./generate.md#validation-gate) validation).
3. Re-parse relationships and methods from current `origin/main`.
4. Cross-check against documented relationships and methods.
5. Report any mismatches.

**Outputs:**
- A structured report with six sections:
  1. **Coverage gaps:** models without docs
  2. **Stale documents:** docs out of date with reason
  3. **Broken links:** source doc, link, target
  4. **Deprecated with inbound links:** deprecated doc, linking docs
  5. **Invalidated human notes:** doc, section, reason
  6. **Validation failures:** doc, specific mismatch

- Report format: terminal output by default, optionally write to a file (e.g., `audit-report.md` in a gitignored location or `meta/audit-latest.md`).

**Error handling:**
- Everspot repository inaccessible — report error, skip source-dependent checks
- Snapshot missing — report error, skip schema-dependent checks
- Malformed document frontmatter — report document and parsing error
- Audit always completes and reports what it can check; it never fails entirely
