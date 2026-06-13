---
title: Everspot System Wiki — Foundation
status: foundational
version: 3
last_updated: 2026-06-12
---

# Everspot System Wiki — Foundation

This document defines what the Everspot System Wiki is, the principles it lives by, how it is structured, and how it is maintained. It is the foundational reference for the wiki; detailed command and prompt specifications live separately (`meta/commands.md`) and build on the model described here.

Where this document describes a mechanism whose exact implementation is still open (most notably how schema is extracted from Laravel), it states the intent and the shape, and leaves the precise mechanics to be settled and tested during implementation.

---

## 1. Purpose

The Everspot System Wiki is an **AI-maintained, searchable internal documentation repository** for the Everspot cemetery-management software. Its primary consumer is an AI agent — Claude Code, running inside the wiki repository — which uses it to answer questions about the system, assist with development, and reason about the data the application stores. Internal staff are a secondary, occasional audience.

The wiki's central concern is the **data model**: what the application stores, how it is structured, and how its pieces relate. Documenting every model is the primary goal. A lighter, broader pass over the system as a whole (architecture, multi-tenancy, integrations, authentication) surrounds that core so the model documentation has context to link to.

The working aim is that the large majority of questions are answerable from the wiki alone, with the remainder requiring the agent to leave the wiki and read the Everspot source directly. That ratio is observed rather than asserted — see §6.4.

---

## 2. Guiding Principles

**AI-first.** Structure, format, and tooling are optimized for AI consumption and AI maintenance. Documents stay human-legible, but there is no presentation layer and human readability is not a design constraint beyond "a person could read it if they needed to."

**The code is the source of truth; the wiki is its optimized projection.** Every document corresponds to definitive source in the Everspot codebase and records what it derives from. The wiki never claims authority over the code.

**Self-contained on purpose.** Because AI agents locate schema and structure in raw source slowly and unreliably, model documents deliberately restate code-derived facts — full schema, properties, methods. Duplicating this *from the codebase into the wiki* is intended.

**Structured facts are rendered and verified, not improvised.** The correctness-critical sections (schema, relationships, method signatures) are rendered deterministically from parsed source and mechanically checked against it before commit. The agent's creative latitude is for prose — overview, usage narrative — not for the column list.

**DRY and MECE govern the wiki internally.** They apply to duplication *between wiki documents*, not to the deliberate code-to-wiki duplication above. Each concept is documented in exactly one canonical place; everything else links to it. Link integrity and coverage gaps are checked mechanically (§7); "the same concept in two places" is a semantic judgment held by the linking discipline and periodic review, not a guaranteed automated check.

**Minimal derived artifacts, and only when enforced.** A derived, committed artifact is avoided whenever a live alternative exists (so the search "map" is frontmatter-grep over live files, not a committed index — §3.2). Where a derived artifact is unavoidable because the live source can't be read at use time (the schema snapshot — §3.3), its integrity is maintained by regenerating and validating it against its authoritative source rather than trusting it to stay correct.

**Always current, against real dependencies.** A document is only trustworthy if you know how current it is, measured against *everything* it derives from. Freshness is anchored to commits over a computed dependency set, plus the schema snapshot (§3.4).

---

## 3. Architecture

### 3.1 Two repositories, canonical branch, config-resolved source

The wiki and the Everspot codebase are **two separate git repositories**. The wiki is installed on each developer's machine and is where Claude Code operates.

The wiki documents Everspot against a single **canonical branch** (`main`). All currency checks and the global sync baseline are defined relative to it, and documentation is never generated from a feature branch or unmerged code. To make branch and working-tree state irrelevant, the agent reads Everspot file contents via `git show origin/main:<path>` rather than off the working tree. The machine-local config (`wiki.config.json`, gitignored, with a committed `wiki.config.example.json`) therefore only needs to point at the Everspot **repository location** for git operations — not for direct file reads. Shared, non-machine-specific state (the sync baseline, the canonical branch name) lives in a committed `meta/wiki-state.json`.

Source references inside documents are written as **paths relative to the Everspot repository root** (e.g. `modules/Transaction/Models/Payment.php`).

### 3.2 Search: native, no server, no manifest

Search is performed with Claude Code's built-in tools (Grep / Glob / Read), running ripgrep over the markdown directly. For a corpus of this size this is effectively instant, needs nothing installed, is identical on every machine, and searches the live files so it can never be stale. Structured lookups ("every model in a module," "which document owns a table," "what relates to Customer") are answered by grepping the YAML frontmatter, which is always current by construction. No committed manifest or search server is introduced; both would be derived artifacts that drift, and the live alternative is good enough. If the corpus ever outgrows frontmatter-grep, a generated manifest can return, but only with a CI check that regenerates it and fails on any difference.

### 3.3 Schema snapshots

Schema is the most correctness-critical content and the hardest to reconstruct statically (cumulative migrations, raw SQL, conditional logic), so it is **not parsed from migration files**. It is captured from a live, migrated database via Laravel's schema introspection (or an equivalent dump), and stored as a committed, per-connection snapshot the documents render from: `schema/central.json` and `schema/tenant.json`.

Two facts about Everspot shape this:

- **Each model belongs to exactly one connection** — central or tenant — and therefore has one schema. A `connection` tag on each model document records which, and it can be *derived* by which snapshot the table appears in rather than hand-assigned.
- **Tenant databases are provisioned per tenant (stancl/tenancy) and all share one schema.** Capturing the tenant snapshot therefore means being *in tenant context*: stand up a throwaway/reference tenant in the generation environment, capture its schema, tear it down. Because all tenants share a schema, any freshly migrated tenant is authoritative and a throwaway one is fully reproducible, including from scratch in CI.

The exact extraction tool (schema introspection vs. `schema:dump`, and the stancl-specific mechanics of entering tenant context) is an implementation detail to finalize and test while building — it does not affect the design here. What matters is the shape: a per-connection snapshot, generated from a live DB, that the Schema section renders from deterministically and is validated against before commit.

This requires the generation environment to have a **runnable Everspot with a migrated database per connection** (the central DB and a tenant context). Everspot already generates a central schema from a live database today, so this is an extension of an existing capability, not a new class of dependency.

### 3.4 Freshness

A model document has two independent freshness inputs:

- **Schema** comes from its connection's snapshot. The snapshot records the commit it was generated through; it is regenerated when new migrations appear in that connection's configured migration paths, and the regenerated snapshot is diffed to find which tables changed.
- **Everything else** (behavior, relationships, methods) derives from a computed `source_paths` set — the model class, its traits and parent, observer registrations, and the inverse sides of its relationships. The set is not hand-maintained; the generate/sync step derives it and recomputes it on every regeneration. A document is current on this axis when `git log built_at..origin/main -- <source_paths>` returns nothing — a range form that is inherently ancestry-aware and so correct across merges.

A document is current when both hold: its table is unchanged in the latest snapshot and no commit since `built_at` touches its `source_paths`. Because `source_paths` is itself derived and can miss a newly added dependency, **freshness is re-derived from current `main`, not trusted from the stored set, wherever it is checked** (§6.1, §7) — closing the gap where a new migration or newly added trait would otherwise leave a document reporting current while stale.

### 3.5 Operating model: single writer, many readers

The **write** operations (sync, snapshot, generate, update — anything that stamps commits, regenerates snapshots, or rewrites docs) are run by a **single actor**: one designated maintainer running Claude Code in v1, and CI once the process is proven. Writes run against `origin/main`. Everyone else consumes the wiki **read-only** — they search, read, and may run the read-only audit locally, but do not commit generated output. This avoids constant merge conflicts on stamped documents, snapshots, and shared state, and guarantees documentation is produced only from merged, canonical code.

Because v1 concentrates write authority in one person, the write process is documented as a runbook in `meta/`, and the maintainer role has a designated backup, so "how to run sync correctly" does not live only in one head before CI takes over.

---

## 4. Repository Structure

The structure mirrors Everspot's organization, with `modules/` as the primary focus. The tree shows the **pattern**; modules and models are not enumerated.

```
everspot-system-wiki/
│
├── wiki.config.json            # machine-local: everspot repo location (gitignored)
├── wiki.config.example.json    # committed template
│
├── index.md                    # master entry point
│
├── schema/                     # committed, generated schema snapshots
│   ├── central.json
│   └── tenant.json
│
├── system/                     # cross-cutting system docs (lighter depth)
│   ├── index.md
│   ├── architecture.md
│   ├── multi-tenancy.md
│   ├── database.md
│   ├── authentication.md
│   ├── integrations.md
│   └── models/                 # core app/Models documentation
│
├── modules/                    # PRIMARY FOCUS — one folder per module
│   ├── index.md
│   ├── transaction/
│   │   ├── index.md
│   │   └── models/
│   │       ├── index.md
│   │       ├── payment.md
│   │       └── [...]
│   └── [... one folder per module ...]
│
└── meta/                       # the wiki's own documentation and state
    ├── foundation.md           # this document
    ├── conventions.md          # naming, tag vocabulary, completeness + model-enumeration rules
    ├── model-template.md       # standard model-doc template
    ├── commands.md             # detailed command/prompt specs
    ├── runbook.md              # how to run the write operations
    └── wiki-state.json         # committed: synced_through, canonical_branch
```

The agent's source-fallback log (§6.4) is written to a gitignored local path and is not committed.

**Naming:** module folders and model files are kebab-case versions of their PHP names; every directory has an `index.md`.

---

## 5. Documentation Standards

### 5.1 DRY and MECE in practice

Each concept is documented once, and everything else links to it. A model's own document carries its full schema and methods (duplicated from code by design); where it references another model it links to that model's document; a cross-cutting concept (multi-tenancy, an integration, an auth pattern) is written once in `system/` and linked to. Link integrity and coverage are checked by the audit; semantic duplication is held by discipline and review (§7).

### 5.2 What a model document contains

- **Overview** — what the model represents and its business role (AI-owned prose).
- **Connection & Table** — central or tenant, and the table name.
- **Schema** — every column (name, type, nullability, default, description), rendered from the connection snapshot.
- **Properties / casts / accessors / mutators**.
- **Relationships** — each relationship, what it means, and a **link** to the related model's document. Related model names are also denormalized into frontmatter so reverse-relationship lookups are trustworthy.
- **Key methods** — signature and purpose, not full bodies.
- **Scopes**, **events/observers**, **common usage** (a few examples).
- **Business logic notes** — human-authored insight not derivable from code (§6.3).

Deliberately excluded (left to the source-fallback case): full method bodies, framework boilerplate, anything purely mechanical the agent can retrieve directly.

**What counts as a model** (for coverage): concrete (non-abstract) Eloquent classes in the module `Models/` directories and `app/Models/`. Abstract base classes are documented once as concepts, not counted as coverage. Pivot and polymorphic-intermediary models are documented only when they carry their own columns or business logic beyond a bare relationship link. The precise rule lives in `meta/conventions.md`.

### 5.3 Single Table Inheritance (STI) pattern documentation

When multiple concrete models share a single database table via Single Table Inheritance (discriminated by a `type` column), they are documented according to these rules:

**Base model** (e.g., Transaction):
- Owns and renders the **full shared-table schema** from the connection snapshot
- Lists all subtypes in frontmatter: `sti_subtypes: [Payment, Refund, ...]` (derived from code analysis)
- Frontmatter includes: `sti: base`
- Documents base-level relationships, methods, scopes, and events
- The schema table is rendered once in the base document only

**Subtype models** (e.g., Payment, Refund):
- Do **NOT** render the full schema table
- Link to the base model for schema: "See [Transaction](./transaction.md) for full schema"
- Document the discriminator value clearly: `type=payment`
- Frontmatter includes: `sti: subtype`, `sti_base: Transaction`, `sti_discriminator: type=payment`
- Document only subtype-specific content:
  - Subtype-specific relationships (beyond inherited ones)
  - Subtype-specific methods, scopes, and events
  - Global scopes that filter to this subtype
  - Casts or accessors unique to this subtype
- Still link to the base document's table field: `table: transactions` (same as base)

**Non-STI models:**
- Omit the `sti` frontmatter field entirely (or use `sti: none`)
- Render full schema as normal

**Coverage and enumeration:**
- Both base and subtypes count as models for coverage purposes
- Each subtype is documented as a separate model file
- STI hierarchies are detected by multiple concrete models resolving to the same table name

### 5.4 Model document template

```markdown
---
model: Payment
module: Transaction
table: payments
connection: tenant            # central | tenant (derived from which snapshot holds the table)
source_paths:                 # computed; recomputed on every regeneration
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Models/Concerns/HasRefunds.php
  - app/Providers/EventServiceProvider.php
related: [Transaction, Refund, Customer]   # derived; powers reverse-relationship lookups
built_at: <main commit this document was generated against>
last_updated: 2026-06-12       # informational only; currency is built_at + sources + snapshot
completeness: complete         # complete | partial | stub (rule-based; see conventions)
deprecated: false              # if true, requires `successor:`
tags: [financial, payment, core]   # controlled vocabulary
---

# Payment

**Primary source:** `modules/Transaction/Models/Payment.php`

## Overview
What this model represents and why it exists. AI-owned.

## Connection & Table
Tenant · `payments`

## Schema
| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| ...    | ...  | ...      | ...     | ...         |
<!-- rendered from schema/tenant.json; validated against it before commit -->

## Properties / Casts
...

## Relationships
- `transaction()` — belongs to [Transaction](./transaction.md): the parent financial record.

## Key Methods
- `process()` — ...

## Scopes / Events / Observers
...

## Common Usage
```php
// representative examples
```

<!-- human:begin -->
## Business Logic Notes
Human-authored insight. Never overwritten by the agent. See §6.3.
<!-- human:end -->
```

`built_at` plus `source_paths` plus the connection snapshot define currency; `last_updated` is a human-facing wall-clock timestamp only.

### 5.5 System and module documentation

Beyond models, the wiki makes a reasonable but shallow effort to document the system as a whole, primarily so model docs have canonical concepts to link to. Freshness for these is chosen per document: a doc that maps to a bounded set of files uses the same range check over those paths; a broad doc like `architecture.md`, where any path set is either noisy or lossy, uses a `review_after` date as its primary freshness mechanism, surfacing on a cadence rather than on every commit to a large directory.

---

## 6. Maintenance Model

Maintenance is **manual** for now — a deliberate choice to observe the process before automating it. All write operations follow §3.5.

### 6.1 The sync workflow

1. Read `synced_through` from `meta/wiki-state.json` and fetch `origin/main`.
2. Gather every commit on `main` since `synced_through`.
3. If new migrations appear in any connection's migration paths, regenerate that connection's schema snapshot and diff it to find changed tables.
4. Map changes to affected documents using the changed files, the changed tables, and each document's **re-derived** `source_paths` (not the stored set), so a new migration, trait, or observer maps to the docs that depend on it.
5. For each affected document: recompute `source_paths` and `related`, regenerate derivable content (rendering Schema from the snapshot), validate structured sections against source (§6.5), and stamp `built_at`.
6. Handle the full lifecycle (§6.2) and human-content reconciliation (§6.3).
7. Advance `synced_through` — but **only past changes whose affected documents were successfully regenerated**. Sync is resumable: on partial failure it does not advance past the unfinished work, reports the failed documents, and reprocesses them next run. This prevents a skipped document's new dependency from becoming a permanent blind spot.

### 6.2 Lifecycle

Sync creates documents for new models, updates changed ones, and **retires** removed ones. Retire means **deprecate, not delete**: the file is marked `deprecated: true` with a `successor:` pointer where one exists, and inbound links are fixed or flagged — a hard delete would silently break the links the agent navigates by. Deprecated documents are excluded from normal search results and the agent is required to respect the flag.

**Renames, splits, and merges are not trusted to git's heuristic detection** where human-authored content is at stake. They are surfaced for human confirmation, and the source documents stay deprecated with their Business Logic Notes intact until a human reassigns those notes — notes are never auto-dropped or auto-duplicated.

### 6.3 Human-authored content

Human insight lives in explicitly marked blocks (`<!-- human:begin --> … <!-- human:end -->`), most notably Business Logic Notes. The agent never guesses what is human-authored and never overwrites a marked block; all other sections are AI-owned and regenerated freely.

For the "preserve vs. correct" tension, the resolution is a third path with **targeted** attribution to avoid alarm fatigue: when a sync changes code, a marked note is flagged `possibly-invalidated` only when an identifier it actually names — a column, method, or model — appears in the change. A note that never mentions `status` is not flagged by a `status` change. Flagged notes are preserved intact, surfaced in the audit, and left for a human to reconcile.

### 6.4 Coverage feedback loop

When the agent cannot answer from the wiki and falls back to reading Everspot source, it appends an entry to a local, gitignored fallback log: the topic, the document(s) consulted, and the source it had to read. A review command analyzes the log for recurring fallbacks and proposes concrete adjustments — a missing document, a section to expand, a link that should exist — turning the "answerable from the wiki" aim into an actionable signal rather than an unmeasured target.

### 6.5 Validation gate

Before a regenerated document is committed, its structured sections are checked against authoritative source: the Schema table is diffed against the connection snapshot, and relationship and method lists are cross-checked against the parsed model. Mismatches block the commit (or flag the document) rather than shipping AI-derived content unverified. This is the mechanical complement to human review of the marked prose blocks.

---

## 7. The Audit

The audit is a **read-only** report that surfaces work without performing it, and it re-derives dependencies from current `main` rather than trusting stored state, so it gives the same staleness guarantee as sync. It checks:

- **Coverage** — models (per the §5.2 rule) with no document.
- **Staleness** — documents failing the §3.4 freshness check, including tables changed in a regenerated snapshot and newly added dependencies; and system docs past `review_after`.
- **Link integrity** — broken internal links, which every retire/rename/split/merge can create and which are a hard failure for a link-navigating agent.
- **Deprecations** — deprecated documents still receiving inbound links.
- **Invalidated human notes** — notes flagged `possibly-invalidated` awaiting reconciliation.
- **Validation failures** — structured sections that no longer match source.

Semantic MECE violations are explicitly *not* a guaranteed output, per §5.1.

---

## 8. Command Set (Conceptual)

Described conceptually here; detailed prompts live in `meta/commands.md`. Write commands are run only by the single maintainer (§3.5).

- **Bootstrap** *(write)* — the initial full build: generate snapshots and a document for every model, set the first `synced_through`. Idempotent and resumable, since a run over the full model set is long enough to be interrupted.
- **Sync** *(write)* — the incremental update of §6.1.
- **Snapshot schema** *(write)* — regenerate the per-connection schema snapshots from a live database. Invoked by bootstrap and sync; runnable on its own.
- **Generate model** / **Update model** *(write)* — create/regenerate or update a single model document.
- **Audit** *(read-only)* — the report of §7. Runnable by anyone.
- **Review coverage** *(read-only)* — analyze the fallback log (§6.4) and propose adjustments.

Search itself is not a command — it is the agent's native file search over the live wiki.

---

## 9. Scope and Evolution

**Now:** document every model comprehensively (the primary goal); cover the broader system at lighter depth; capture schema from live databases into committed per-connection snapshots; maintain manually via the single-writer, commit-anchored sync; search natively over the live files.

**Later, as the approach proves out:**

- Finalize and harden the schema-extraction mechanics (the introspection vs. dump choice and the stancl tenant-context details) against real runs.
- Extend documentation beyond models to services, actions, workflows, and API endpoints, on the same patterns.
- Promote sync and snapshot generation from a manual maintainer task to CI against `origin/main`.
- Reintroduce a generated manifest only if frontmatter-grep becomes slow, and only with a CI integrity check.
- Revisit a dedicated search engine or semantic search only if a human-facing portal or a substantially larger corpus makes the native approach insufficient.

The structure is meant to absorb this growth without redesign: the principles, the snapshot-plus-range freshness model, the single-writer operating model, and the DRY/MECE linking discipline apply equally well to a wiki many times this size.
