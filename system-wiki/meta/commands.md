---
title: Everspot System Wiki — Command Specifications
status: foundational
version: 1
last_updated: 2026-06-12
---

# Everspot System Wiki — Command Specifications

This document provides detailed specifications for all wiki maintenance operations. It is the authoritative reference for implementing and executing these commands. This specification assumes familiarity with `meta/foundation.md`, which defines the architecture, principles, and maintenance model these commands implement.

**Audience:** AI agents (Claude Code) executing these commands and the human maintainer who supervises them.

**Relationship to foundation.md:** The foundation defines what the wiki is and how it works conceptually. This document specifies exactly how to perform each maintenance operation.

---

## 1. Command Overview

All commands fall into two categories:

- **Write operations** (sync, generate, update, snapshot-schema, bootstrap) — modify wiki files, regenerate snapshots, stamp commits. Run only by the designated maintainer per foundation §3.5, against `origin/main`.
- **Read-only operations** (audit, review-coverage) — surface issues and patterns without making changes. Runnable by anyone.

Every command that reads Everspot source uses `git show origin/main:<path>` from the Everspot repository location specified in `wiki.config.json`, never reading the working tree. This makes branch state and local modifications irrelevant.

---

## 2. Generate

**Purpose:** Create a single new model document from scratch.

**Operation type:** Write

**Inputs:**
- Model class path relative to Everspot repository root (e.g., `modules/Transaction/Models/Payment.php`)
- Implicit: `wiki.config.json` for Everspot repository location
- Implicit: Current `schema/central.json` and `schema/tenant.json`

**Preconditions:**
- Schema snapshots exist and are current
- Model class exists at the specified path in `origin/main`

**Process:**

### 2.1 Derive source_paths

The `source_paths` set is computed, never hand-maintained. It includes every file this document's content derives from:

1. **The model class itself** — the input path.
2. **Traits used by the model** — parse the class via `git show origin/main:<model-path>`, extract `use TraitName` declarations in the class body, resolve each to its file path (follow PSR-4 namespace mapping from Everspot's `composer.json`), recursively include traits those traits use.
3. **Parent classes** — if the model extends a non-framework class (e.g., a custom base model in `app/Models/`), include that class file and recursively include its parent and traits.
4. **Observer registrations** — grep `app/Providers/EventServiceProvider.php` (and any other configured observer registration locations per `meta/conventions.md`) for this model's fully qualified class name. If registered, include the provider and the observer class file.
5. **Inverse relationship sides** — for each relationship defined in this model that points to another model, include that related model's file, because the inverse relationship's existence and name affect this model's documentation.

Store these paths in the frontmatter `source_paths` array, relative to Everspot repository root.

### 2.2 Determine connection

The model's database connection (central or tenant) is derived, not specified manually:

1. Parse the model class. If it has an explicit `$connection` property, use that value.
2. If no explicit connection, use Everspot's default connection for the model's location (modules use tenant by default per Everspot conventions; `app/Models/User` and core auth models use central).
3. Cross-check: the model's `$table` property (or conventionally derived table name) must exist in exactly one schema snapshot. If the derived connection conflicts with snapshot membership, fail with an error requiring investigation.

Store the connection as `connection: central` or `connection: tenant` in frontmatter.

### 2.3 Render schema

From the appropriate schema snapshot (`schema/central.json` or `schema/tenant.json`):

1. Locate the table entry matching the model's `$table` (or conventional table name derived from the model class name).
2. Render the Schema section as a markdown table with columns: Column, Type, Nullable, Default, Description.
3. For each column in the snapshot: extract name, type, nullable, default. Leave Description empty (to be filled by AI prose or left blank).
4. Include index information below the table (primary key, unique indexes, regular indexes).
5. Include foreign key constraints if present in the snapshot.

The rendered schema is deterministic — given the same snapshot, the output is identical. This section is validated before commit (§2.6).

### 2.4 Parse relationships, methods, scopes

Via `git show origin/main:<model-path>`:

1. **Relationships** — parse method signatures returning relationship instances (`hasMany`, `belongsTo`, `belongsToMany`, `morphTo`, etc.). Extract the method name, relationship type, related model class, and any non-default foreign key or pivot table arguments.
2. **Key methods** — identify public methods beyond relationships and framework boilerplate. Include signature (name, parameters, return type if declared), exclude method body. Focus on business logic methods, not auto-generated or purely mechanical ones.
3. **Scopes** — methods matching `scope*` pattern, extract name and signature.
4. **Properties, casts, accessors, mutators** — extract `$fillable`, `$casts`, `$appends`, and methods matching `get*Attribute` / `set*Attribute` patterns.

### 2.5 Denormalize related frontmatter

For reverse-relationship lookups via frontmatter grep:

1. From the parsed relationships, extract every distinct related model class name (short name, not fully qualified).
2. Store in frontmatter as `related: [ModelA, ModelB, ModelC]` in alphabetical order.

This allows an agent to find all models that relate to a given model by grepping `related:` in frontmatter, without parsing every model document's relationship prose.

### 2.6 Apply model-template.md

Using the structure defined in `meta/model-template.md` (foundation §5.3):

1. Populate frontmatter: model, module, table, connection, source_paths, related, built_at (current `origin/main` commit hash), last_updated (current date), completeness (determined by rule in `meta/conventions.md`), deprecated (false for new docs), tags (inferred or left for manual refinement).
2. Generate Overview section — AI-written prose describing what the model represents and its business role.
3. Insert rendered Schema section from §2.3.
4. Document Properties/Casts, Relationships, Key Methods, Scopes from parsed data.
5. Add Common Usage section with placeholder or basic examples.
6. Insert human-content marker block:
   ```markdown
   <!-- human:begin -->
   ## Business Logic Notes
   <!-- human:end -->
   ```

### 2.7 Validation gate

Before writing the file:

1. **Schema validation** — diff the rendered Schema section against the source snapshot table. Any mismatch (column missing, type wrong, nullability wrong) blocks the commit with a detailed error.
2. **Relationship validation** — for each documented relationship, verify the related model class exists in Everspot source and the inverse relationship is plausible (not necessarily named, but the relationship type is consistent — a `belongsTo` should have a `hasMany`/`hasOne` inverse).
3. **Method signature validation** — cross-check documented method names and signatures against parsed source.

Validation failures produce a detailed report. The command does not commit the document until all validations pass.

### 2.8 Write and stamp

1. Write the document to the appropriate path: `modules/<module-kebab>/models/<model-kebab>.md` or `system/models/<model-kebab>.md`.
2. Stamp `built_at` with the current `origin/main` commit hash of the Everspot repository.
3. Report completion: document path, validation status, derived connection, number of source_paths.

**Outputs:**
- New `.md` file at the derived path
- Stamped with `built_at` commit and complete metadata

**Error handling:**
- Model class not found in `origin/main` — fail with clear error
- Table not found in either snapshot — fail, report which snapshots were checked
- Connection conflict (derived vs. snapshot membership) — fail, require investigation
- Validation failure — fail, report specific mismatches, do not write file
- Trait or parent class resolution failure — fail, report unresolved class

---

## 3. Sync

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

### 3.1 Gather changes

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

### 3.2 Detect schema changes

For each database connection (central, tenant):

1. Identify migration paths from `meta/conventions.md` (e.g., `database/migrations/` for central, `database/migrations/tenant/` for tenant).
2. Check if any commits since `synced_through` touched files in those paths.
3. If yes, regenerate that connection's schema snapshot (§4 Snapshot-schema).
4. Diff the regenerated snapshot against the previous committed snapshot:
   - For each table: compare column list, types, nullable, defaults, indexes, foreign keys.
   - Record tables with any difference as "changed tables."
5. If no migration changes, no schema regeneration needed — the existing snapshot is current.

### 3.3 Map changes to affected documents

For each changed file from §3.1 and each changed table from §3.2:

**Per changed file:**

1. If the file is a model class (in `modules/*/Models/` or `app/Models/`), add the document for that model to the affected set.
2. If the file is a trait, parent class, or observer: grep all existing documents' frontmatter for `source_paths` containing this file path (but do not trust stored paths alone — re-derive for each candidate).
3. If the file is in a migration path, the changed tables handle it (§3.2).

**Per changed table:**

1. Find the document whose frontmatter `table:` matches this table name.
2. Add to affected set.

**Re-derive source_paths before trusting membership:**

For each candidate document from the above mapping:

1. Re-derive its `source_paths` using the same logic as Generate §2.1, reading from current `origin/main`.
2. If the changed file appears in the re-derived set, confirm the document is affected.
3. If a new dependency (trait, observer) was added since the document was last built, the re-derivation will catch it even though the stored `source_paths` did not include it.

This re-derivation step closes the gap where a newly added dependency would otherwise leave a document falsely reporting current.

### 3.4 Regenerate affected documents

For each document in the affected set:

1. Perform the same process as Generate §2, but updating the existing file rather than creating new.
2. Preserve human-authored content blocks (§3.7).
3. Re-derive `source_paths` and `related` — always from scratch, never trusted from the existing frontmatter.
4. Re-render Schema from the current snapshot.
5. Re-parse relationships, methods, scopes from current `origin/main` source.
6. Validate (§2.6).
7. Stamp `built_at` with the current `origin/main` commit.
8. Update `last_updated` to current date.

### 3.5 Handle lifecycle

**New models:**

If a new model class appears in commits since `synced_through`:

1. Detect by finding model classes in changed files that have no existing document.
2. Run Generate for each.

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

### 3.6 Fix or flag inbound links

When a model is deprecated:

1. Grep the wiki for links to the deprecated document.
2. If `successor` is set, attempt to rewrite links automatically (replace `[OldModel](path/to/old.md)` with `[NewModel](path/to/new.md)`).
3. If no successor or rewrite is ambiguous, flag the linking documents in the sync report.

### 3.7 Human-content reconciliation

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

### 3.8 Advance synced_through

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

### 3.9 Report

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

---

## 4. Snapshot-schema

**Purpose:** Regenerate `schema/central.json` and `schema/tenant.json` from live, migrated databases.

**Operation type:** Write

**Inputs:**
- Runnable Everspot instance with:
  - Migrated central database
  - Configured tenant context (stancl/tenancy) with at least one migrated tenant database
- `wiki.config.json` for Everspot repository location

**Preconditions:**
- Everspot codebase is functional and can boot
- Central database is migrated to latest
- Tenant context can be entered and a fresh tenant database exists and is migrated

**Process:**

### 4.1 Capture central schema

1. From the Everspot repository, run Laravel schema introspection on the central connection:
   ```bash
   php artisan schema:dump --connection=central --format=json
   ```
   Or use an equivalent method (e.g., `DB::connection('central')->getDoctrineSchemaManager()->listTableDetails()`).

2. Output format (JSON):
   ```json
   {
     "snapshot_commit": "<current origin/main commit hash>",
     "connection": "central",
     "tables": {
       "users": {
         "columns": [
           {"name": "id", "type": "bigint", "nullable": false, "default": null},
           {"name": "email", "type": "varchar(255)", "nullable": false, "default": null},
           ...
         ],
         "indexes": [
           {"name": "primary", "columns": ["id"], "unique": true},
           {"name": "users_email_unique", "columns": ["email"], "unique": true}
         ],
         "foreign_keys": [
           {"columns": ["role_id"], "references": "roles.id", "on_delete": "cascade"}
         ]
       },
       ...
     }
   }
   ```

3. Record `snapshot_commit` as the current `origin/main` commit hash of Everspot at the time of generation.

4. Write to `schema/central.json`.

### 4.2 Capture tenant schema

1. Enter tenant context using stancl/tenancy:
   ```bash
   php artisan tenants:run <tenant-id> --command="schema:dump --connection=tenant --format=json"
   ```
   Or programmatically: `Tenant::find($id)->run(function() { /* introspect schema */ })`.

2. Use a reference tenant or create a throwaway tenant, migrate it, capture schema, optionally destroy it. Any freshly migrated tenant is authoritative because all tenants share one schema.

3. Output same JSON format as central, with `"connection": "tenant"` and `snapshot_commit` set to Everspot's current `origin/main`.

4. Write to `schema/tenant.json`.

### 4.3 Validation

After generation:

1. Verify each snapshot is valid JSON and contains expected structure.
2. Check that at least one table exists per connection (empty snapshots indicate failure).
3. Cross-check: every model document's `table` should appear in exactly one snapshot. If a documented table is missing, flag for investigation.

**Outputs:**
- `schema/central.json` with current schema
- `schema/tenant.json` with current schema
- Each stamped with `snapshot_commit` for table-change detection

**Error handling:**
- Everspot cannot boot — fail with clear error. If this is a permanent environment issue, produce a skeleton JSON structure with a `"error": "everspot_unavailable"` marker and document in `meta/` as a blocker for schema-dependent operations.
- Tenant context cannot be entered — fail, report stancl/tenancy configuration issue
- Schema introspection returns empty or malformed — fail, do not overwrite existing snapshots
- JSON write failure — fail, report file system issue

---

## 5. Update

**Purpose:** Force-regenerate a single existing model document, ignoring freshness.

**Operation type:** Write

**Inputs:**
- Model document path (e.g., `modules/transaction/models/payment.md`) OR model name (e.g., `Payment`)
- Implicit: same as Generate (§2)

**Preconditions:**
- The document exists
- Schema snapshots exist and are current

**Process:**

1. If input is a model name, locate the document by grepping frontmatter for `model: <name>`.
2. Perform the same regeneration as Generate §2, but for an existing file:
   - Re-derive `source_paths` and `related`
   - Re-render Schema from snapshot
   - Re-parse relationships, methods, scopes
   - Preserve human-content blocks (same as Sync §3.7)
   - Validate
   - Stamp `built_at` with current `origin/main` commit
3. Write the updated file.

**Use cases:**
- Manual refresh of a single document after reviewing it
- Fixing a document with known issues
- Testing template changes on a single document before a full sync

**Outputs:**
- Updated `.md` file, validated and stamped

**Error handling:**
- Document not found — fail with clear error
- Same validation and error handling as Generate §2

---

## 6. Audit

**Purpose:** Surface issues without fixing them. Re-derive all dependencies from current `origin/main` to ensure staleness checks are accurate.

**Operation type:** Read-only

**Inputs:**
- Current wiki repository state
- `wiki.config.json` for Everspot repository location
- Current `schema/central.json` and `schema/tenant.json`

**Preconditions:**
- None (can run in any state, even with stale or broken documents)

**Process:**

### 6.1 Coverage check

**Goal:** Find models that should have documentation but don't.

1. Read the model-enumeration rule from `meta/conventions.md` (concrete Eloquent classes in `modules/*/Models/` and `app/Models/`, excluding abstract base classes, excluding bare pivot models per the rule).
2. List all model classes in `origin/main` matching the rule:
   ```bash
   git ls-tree -r --name-only origin/main | grep -E 'modules/.*/Models/.*\.php|app/Models/.*\.php'
   ```
3. For each file, check if it is abstract (parse `abstract class`), check if it is a bare pivot (no custom columns or logic per conventions rule).
4. For each in-scope model, grep wiki frontmatter for `model: <ClassName>`.
5. Report models with no corresponding document.

### 6.2 Staleness check

**Goal:** Find documents whose content is outdated.

For each model document:

1. **Re-derive source_paths** from current `origin/main` using Generate §2.1 logic. Do not trust the stored `source_paths` in frontmatter.
2. **Check source freshness:**
   ```bash
   git log <built_at>..origin/main -- <re-derived-source_paths>
   ```
   If any commits appear, the document is stale on the source axis.

3. **Check schema freshness:**
   - Find the document's connection and table from frontmatter.
   - Check the snapshot's `snapshot_commit`.
   - If `snapshot_commit` is ahead of the document's `built_at`, check if the table changed:
     - Retrieve the table definition from the snapshot at `built_at` (via git or stored historical snapshots if available, or assume changed if not provable).
     - Compare to current snapshot. If different, document is stale on schema axis.

4. **Check review_after (for system docs):**
   - If frontmatter has `review_after: <date>` and today's date is past it, flag as stale.

5. Report all stale documents with reason (source touched, schema changed, review_after passed).

### 6.3 Link integrity check

**Goal:** Find broken internal links.

1. Grep all `.md` files for markdown links: `\[.*?\]\((.*?)\)`.
2. Extract link targets. For relative links, resolve to absolute wiki paths.
3. Check if each target file exists.
4. Report broken links: source document, link text, target path.

### 6.4 Deprecation check

**Goal:** Find deprecated documents that still have inbound links.

1. Grep frontmatter for `deprecated: true`.
2. For each deprecated document, grep the wiki for links to it (excluding the deprecated doc's own `successor` mention).
3. Report deprecated docs with inbound links, listing the linking documents.

### 6.5 Invalidated human notes check

**Goal:** Surface human-authored blocks flagged for review.

1. Grep all `.md` files for `<!-- possibly-invalidated`.
2. Parse the flagged blocks and their reasons.
3. Report each flagged block: document, section, reason.

### 6.6 Validation check

**Goal:** Find documents whose structured sections don't match source.

For each model document:

1. Re-parse the Schema section.
2. Diff against the current snapshot (same as Generate §2.6 validation).
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

---

## 7. Review-coverage

**Purpose:** Analyze the fallback log to identify recurring gaps and propose concrete improvements.

**Operation type:** Read-only

**Inputs:**
- `.fallback.log` (gitignored, written by the agent when it reads Everspot source instead of wiki)
- Current wiki state

**Preconditions:**
- Fallback log exists and has entries (if not, report "no fallback data")

**Log entry format:**

Each entry is appended when the agent cannot answer from the wiki alone:

```
[2026-06-12 14:23:15] Topic: How does payment refund validation work?
Consulted: modules/transaction/models/payment.md, modules/transaction/models/refund.md
Source read: modules/Transaction/Models/Payment.php (method validateRefund, lines 45-67)
---
```

**Process:**

### 7.1 Parse log

1. Read all entries from `.fallback.log`.
2. For each entry, extract:
   - Topic (the question or task)
   - Consulted docs (which wiki documents were read)
   - Source read (which Everspot files and what content was accessed)

### 7.2 Identify patterns

**Recurring topics:**

1. Group entries by similar topic strings (fuzzy match, keyword overlap).
2. If the same topic or closely related topics appear multiple times, flag as recurring.

**Recurring source files:**

1. Count how often each Everspot source file appears in "Source read."
2. If a file is read frequently and is not a model class (e.g., a service, a helper, a config), it may warrant a new wiki document.

**Recurring gaps in existing docs:**

1. If the same model document is consulted repeatedly, but the agent always falls back to source for the same kind of information (e.g., a specific method, a specific relationship detail), that section may be incomplete or unclear.

### 7.3 Propose adjustments

Based on patterns, generate proposals:

- **Missing documents:** "Frequently consulted source file `modules/Transaction/Services/PaymentProcessor.php` is not documented. Consider creating a service documentation page."
- **Sections to expand:** "Model document `payment.md` consulted 8 times, but `validateRefund` method required reading source every time. Consider expanding the Key Methods section with this method's logic and validation rules."
- **Links to add:** "Topic 'payment and invoice relationship' recurs. Documents consulted: `payment.md`, `invoice.md`. Neither links to the other. Add cross-references."
- **New coverage rules:** "Non-model class `app/Services/TenantProvisioner.php` read 5 times. Current coverage rule excludes services. Consider extending documentation scope."

### 7.4 Output

Generate a report:

1. **Summary statistics:** total fallback entries, date range, most-consulted documents, most-read source files.
2. **Recurring patterns:** grouped topics, gap types.
3. **Concrete proposals:** enumerated list of suggested additions, expansions, and links, with evidence (frequency, entry excerpts).

**Outputs:**
- Report written to terminal or `meta/coverage-review-<date>.md`
- Proposals are actionable: specific document, specific section, specific reason

**Error handling:**
- Log file missing or empty — report "no fallback data, coverage cannot be assessed"
- Malformed log entries — skip invalid entries, report count of skipped
- Review-coverage never fails; it reports what it can analyze

---

## 8. Bootstrap

**Purpose:** Perform the initial full build of the wiki.

**Operation type:** Write

**Scope note:** This command is mentioned in foundation §8 but its full specification is deferred to implementation, as it is a combination of existing commands. The outline below establishes intent and structure.

**Inputs:**
- Runnable Everspot instance (for schema snapshots)
- `wiki.config.json` for Everspot repository location
- Empty or partially populated wiki repository

**Process (conceptual):**

1. **Generate schema snapshots** — run Snapshot-schema (§4) for both connections.
2. **Enumerate all models** — use the coverage rule from Audit §6.1 to list every in-scope model in `origin/main`.
3. **Generate documents for all models** — for each model, run Generate (§2). Process in batches if necessary for resumability.
4. **Set initial synced_through** — record the current `origin/main` commit hash as the first baseline in `meta/wiki-state.json`.
5. **Validate the full set** — run Audit (§6) to check for any generation failures, broken links, or coverage gaps.
6. **Commit the initial wiki** — commit all generated documents, snapshots, and state.

**Resumability:**

Because generating hundreds of models may take significant time and is interruption-prone:

1. Track which models have been generated in a temporary state file (gitignored).
2. On resume, skip already-generated models.
3. Once all models are generated, remove the temporary state and commit the final result.

**Outputs:**
- Full set of model documents
- Schema snapshots for both connections
- `meta/wiki-state.json` with first `synced_through`
- Initial commit establishing the wiki baseline

**Error handling:**
- Same per-model error handling as Generate
- On failure, report failed models and allow resume
- Do not set `synced_through` until all models are successfully generated

**Deferred:** Exact command interface, progress reporting, and batch size tuning to be determined during implementation.

---

## 9. Command Execution Principles

### 9.1 Reading Everspot source

**Always via git show:**

Every read of an Everspot file uses:

```bash
git show origin/main:<relative-path-from-everspot-root>
```

Never read from the working tree. This makes:

- Branch state irrelevant (feature branches, dirty working trees, stashes)
- Everspot config (`wiki.config.json`) need only specify repository location, not assume a specific branch checked out
- All commands idempotent with respect to Everspot's local state

### 9.2 Source_paths derivation

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

### 9.3 Connection determination

**Derived from snapshot membership:**

The model's database connection is not manually assigned. It is:

1. Inferred from the model's `$connection` property or conventional default.
2. Validated by checking which schema snapshot contains the model's table.
3. If inference and snapshot membership conflict, the command fails and requires investigation.

This prevents:

- Incorrect connection tags from manual error
- Documents claiming a table is central when it is actually tenant or vice versa

### 9.4 Validation gate

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

### 9.5 Human content reconciliation

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

### 9.6 Resumability and partial failure

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

This document (commands.md) is the authoritative specification. Where foundation.md describes intent, this document specifies mechanism. Where conventions.md establishes rules, this document specifies how those rules are applied during execution.

---

## 11. Summary Table

| Command | Type | Purpose | Key Inputs | Key Outputs |
|---------|------|---------|------------|-------------|
| **Generate** | Write | Create new model doc | Model class path | New .md file, validated, stamped |
| **Sync** | Write | Incremental update all affected docs | synced_through, origin/main | Updated docs, new synced_through, commit |
| **Snapshot-schema** | Write | Regenerate schema JSONs from live DBs | Runnable Everspot, migrated DBs | central.json, tenant.json with snapshot_commit |
| **Update** | Write | Force-regenerate single doc | Model doc path or name | Updated .md file, validated, stamped |
| **Audit** | Read-only | Surface issues without fixing | Current wiki + Everspot source | Report: coverage, staleness, links, deprecations, notes, validation |
| **Review-coverage** | Read-only | Analyze fallback log, propose adjustments | .fallback.log | Report: patterns, proposals |
| **Bootstrap** | Write (deferred spec) | Initial full build | Runnable Everspot, empty wiki | Full doc set, snapshots, first synced_through |

---

**End of Command Specifications**

All operations defined here are implemented by Claude Code executing these specifications as prompts. The human maintainer supervises, reviews reports, and reconciles flagged human content. CI will eventually assume the write operations once the process is proven.
