# Everspot Autonomous Data-Migration Pipeline — SPEC

**Status:** Living specification. This is the single source of truth for *what we are building toward* and *how it is designed*. It consolidates and supersedes the prior narrative docs (`data-migration-pipeline-plan.md`, `01-operating-model.md`, `HANDOFF.md`, `README.md`, `NEXT-SESSION.md`).

**Division of labor between this doc and other records:**
- **This SPEC** = the target design and the rationale (stable; changes only by deliberate decision).
- **The `data-migration-pipeline` file-memory entry** = the running state log (which fixes landed, which datasets ran, current branch). Read it for "where exactly are we today."
- **The `/migrate` command (`.claude/commands/migrate.md`), `schemas/`, `scripts/`, `contract/`, `knowledge/` files** = the operational implementation the SPEC describes.

> **Conflict rule:** where any source disagreed during consolidation, the decisions reached in the design conversation that produced this SPEC win — chiefly: (1) a **single** question round, not two gates; (2) the **Orion API as the primary load path**, with Excel as the alternate; (3) the **codebase-derived target contract** (§6); and (4) the **self-improvement engine** design (§11).

---

## Table of Contents
1. [North Star](#1-north-star)
2. [Current State & The Gap](#2-current-state--the-gap)
3. [Core Principles](#3-core-principles)
4. [The Three-Layer Memory Model](#4-the-three-layer-memory-model-ledger--snapshots--runs)
5. [Identity, External IDs & the Memoization Tiers](#5-identity-external-ids--the-memoization-tiers)
6. [The Target Contract (codebase-derived)](#6-the-target-contract-codebase-derived)
7. [The Canonical Artifact & Everspot Target Facts](#7-the-canonical-artifact--everspot-target-facts)
8. [The Pipeline Stages](#8-the-pipeline-stages)
9. [The Single Question Round & Ask-Policy](#9-the-single-question-round--ask-policy)
10. [The Incremental v1→v2 Engine](#10-the-incremental-v1v2-engine)
11. [The Self-Improvement Engine](#11-the-self-improvement-engine)
12. [The Test Suite](#12-the-test-suite)
13. [Orion API Integration](#13-orion-api-integration)
14. [Sandbox Automation (the load target)](#14-sandbox-automation-the-load-target)
15. [User Experience & Review Surfaces](#15-user-experience--review-surfaces)
16. [Directory Structure](#16-directory-structure)
17. [Roadmap & Sequencing](#17-roadmap--sequencing)
18. [Binding Rules & Locked Decisions](#18-binding-rules--locked-decisions)
19. [Glossary](#19-glossary)

---

## 1. North Star

A migration should cost the **user** (a migration specialist) almost nothing:

1. The user runs **one** Claude Code slash command (`/migrate`), drops the source file(s), and adds a sentence or two of context.
2. The pipeline does **everything else autonomously**: identifies/prepares the target sandbox, profiles the data, **consults the Everspot codebase itself** to understand the target schema and semantics, auto-drafts the mapping, and surfaces **only** the questions it genuinely cannot answer from the data + codebase + its own learned patterns.
3. It asks those questions **once**, in a single batched round, **each with a proposed answer** so the user can "accept all" or override.
4. After the answers, it runs to completion **unattended** — cleanse → assemble → validate → create any missing reference data → load all records via the **Orion API** → reconcile — and hands back a single report.
5. It is **self-improving** along three loops (§11): it refines its own orchestrator prompt/skills/knowledge; it maintains a curated, tested library of reusable transforms/validators; and every error it hits is root-caused, fixed generally, and locked behind a regression test so that class of error never recurs.

The engine that makes a migration correct already exists and is proven. The work ahead is closing the gap between "a pipeline an engineer babysits" and "a command the user runs and walks away from."

---

## 2. Current State & The Gap

### Built and proven
- **Deterministic spine runs end-to-end**: `ingest → delta → cleanse → assemble → validate → emit → reconcile`, integration-tested on a synthetic dataset and on two real datasets (CCMP/Columbiana customer slice; Bell's Chapel full flat-register).
- **Orion API load path built and proven**: `orion_load.py` + `migrate.py load --live` loaded **2,419 properties + 910 customers + 910 interments + 4,240 external_ids** into the `bellschapel-sb` sandbox cleanly — 0 failed, 0 dangling FKs, idempotent upserts, atomic batches.
- **Incremental engine proven**: a v1→v2 synthetic run classified NEW/CHANGED/UNCHANGED/REMOVED correctly; a CHANGED row whose name was unchanged got a transform-cache **hit** (zero re-parse); external_ids stayed stable across drops.
- **Sandbox automation proven cross-environment**: pull a prod tenant → scrubbed dev sandbox at a deterministic `<prefix>-sb.<root>` domain; refresh/cache rebuild works offline.
- **Orion Phase-A read layer** landed in the Everspot repo (ExternalId fix, 6 added resources, searchableBy).

### The gap (what makes it not-yet the north star)
| Gap | Today | Target |
|---|---|---|
| **Entry point** | many manual CLI calls + hand-authored stages | one `/migrate` orchestrator (§8) |
| **Question gates** | two separate gates (mapping, then exceptions) | **one** batched round (§9) |
| **Schema authority** | 4 drifting definitions of each entity (canonical schema, assemble, emit, orion_load) — drifted 3× with silent drops | **one** codebase-derived target contract (§6) |
| **Profile + mapping** | profiling + authoring `mapping.yaml`/`value_sets.yaml` done by hand each run | runnable `profile` stage that auto-drafts the mapping (§8) |
| **Validate/reconcile** | print "hand off to Claude Code" | runnable, self-verifying (§8) |
| **Safety net** | none — a global change had nothing to catch breakage | golden-file + conformance + regression test suite (§12) |
| **Learning** | ad hoc, in memory entries | versioned, test-gated self-improvement engine (§11) |

---

## 3. Core Principles

1. **Claude Code is the conductor.** The orchestrator is Claude Code itself driving a file-based run workspace — not an external Python/LangGraph runtime. Each stage is a skill/subagent that reads only its inputs + the relevant knowledge slice, writes a checkpoint, and is independently re-runnable. Resume + audit come from the artifacts.
2. **Deterministic-first, LLM-fallback.** Python scripts handle the predictable 80–90%. The LLM is a scalpel for the messy residual + unstructured fields — always via **structured output (tool calling)**, always **confidence-scored**, always **re-validated through the same Python library** (the library, not the model, is the source of truth). The LLM **never does arithmetic**.
3. **One convergence point.** Everything funnels into a single **canonical, external-id-keyed NDJSON artifact** (§7). Both the Orion loader (primary) and the Excel emitter (alternate) read that one artifact.
4. **One schema authority.** Every stage validates against the **target contract** (§6), derived from Everspot. Drift becomes a build/load-time failure, never a silent drop.
5. **Memory ≠ run.** Durable decisions live in the per-client **ledger**; working artifacts are disposable **runs** (§4). This is what makes re-drops cheap.
6. **No silent failures.** Unresolved required fields, dangling FKs, low-confidence cells, ambiguous entities, unresolved value-sets — all surface as flagged exceptions or questions. A required reference is **never** papered over with null.
7. **Ask once, ask narrow.** A single batched question round, governed by a crisp ask-policy (§9). Everything answerable from data + codebase + learned patterns is answered autonomously with a recorded default.
8. **Self-improving, test-gated, reversible.** The system learns (§11), but every self-change is a tracked, reversible diff that ships only when the test suite (§12) passes. General learnings go to the shared layer; client facts go to that client's ledger only — never crossed.

---

## 4. The Three-Layer Memory Model (Ledger ↔ Snapshots ↔ Runs)

A migration is a long-lived **Project** (one client/engagement). Three things are kept strictly separate, and that separation is what makes incremental re-runs cheap.

| Layer | What it is | Scope | Lifetime |
|---|---|---|---|
| **Snapshots** | each immutable *drop* of client data (`v1`, `v2`, …); raw files never mutated | one client | permanent (append-only) |
| **Ledger** | the project's durable **memory**: mappings, value-set translations, entity merges, cell overrides, answered questions, minted external_ids, the transform cache, the Wave-0 reference snapshot | one client | permanent |
| **Runs** | disposable per-drop working artifacts: cleansed cells, the canonical NDJSON, validation reports, the load report, the user report | one drop | regenerable from `snapshot + ledger` anytime |

> **The core invariant:** any record's output is a pure function of `(its source data) × (the ledger) × (the script/mapping versions)`. Nothing is recomputed unless one of those three changed *for that record*. That single rule is the whole answer to "don't redo the work."

**The ledger is keyed by what a decision is *about*** — a column, a source record's stable id, a value — *not* by row position or by which drop it came from. So it survives across drops and is re-applied automatically.

**Strict separation of learning (binding):** client-specific facts (a client's columns, their value-set meanings, their answered questions, their minted ids) live in **that client's ledger only**. General learnings (heuristics, reusable transforms, target-schema gotchas) live in the **shared general layer** (§11). Client data must never leak into a shared script, and a shared script must never hardcode a client's column names.

---

## 5. Identity, External IDs & the Memoization Tiers

### 5.1 Source identity
Computed per source row at ingest:
- **`source_id`** = `"<table>:<source_key>"`. The `source_key` is the column(s) that uniquely identify a record *in the client's system* (their PK / account number / GUID), declared per table. If the client has **no stable key**, "which column(s) uniquely identify an X?" is itself a question — never guessed silently; if truly keyless, fall back to a deterministic hash of the identifying columns and **flag the fragility**.
- **`row_hash`** = a stable hash of the row's normalized raw cell values; detects whether a record *changed* between drops.

Both are written to `snapshots/<v>/source_index.parquet`.

### 5.2 External IDs (why `source_id` is sacred)
The **`external_id`** minted for a record is derived from, and permanently bound to, its `source_id` (format `src:<entity>:<source-id-token>`). So the same client record always maps to the same Everspot record across every drop and re-load. That is what makes loads **idempotent** (upsert by `external_id`) and makes v2 **update** rather than **duplicate**. **Never re-mint an `external_id` for a record that already has one.**

### 5.3 The three memoization tiers
| Tier | Key | Decides | Owner |
|---|---|---|---|
| **1 — row** | `source_id + row_hash` | which rows to process at all | `delta.py` |
| **2 — cell** | `source_id + column + script/mapping version` | within a CHANGED row, skip cells whose own input didn't change | `ledger.py` |
| **3 — value (transform cache)** | `transform + version + normalized_input [+ context_signature]` | has *this exact string* ever been parsed by this transform? | `transform_cache.py` |

Tier 3 guarantees **no second LLM call even when other cells in the row change**, and dedups within a drop (50 identical name strings → one parse, 49 hits). `context_signature` captures only the column-level decisions that change the output (e.g. `name_order=last_first`, `date_format=MDY`) — preventing reuse of a parse that was only correct under a since-changed interpretation. Human-pinned rules (`ledger/parse_rules.yaml`) **win and are version-independent**; LLM entries are cached version-scoped behind a confidence floor (poisoning guard); a version bump lazily recomputes only re-encountered strings.

---

## 6. The Target Contract (codebase-derived)

**The single machine-readable definition of every target entity, derived from Everspot.** It kills schema drift and powers self-service answers (the orchestrator reads it to answer "what does column X map to / what values are valid" *without* asking the user).

### 6.1 The problem it solves
Today the canonical schema, `assemble.py`, `emit_excel.py`, and `orion_load.py` each carry their own definition of each entity — ~50 concrete drifts identified, including silent-drop bugs (e.g. `section/lot/space` are first-class scalars in one place, dynamic attributes in another, and concatenated into a `description` string in a third). Four definitions, three of which can silently diverge.

### 6.2 Design decision: generated-and-committed artifact
- **Mechanism = live introspection; product = a committed file.** A small artisan generator boots tenant context, introspects the live tenant DB schema (columns/types/nullability/defaults/FKs), reflects each model's `casts()`, and writes `contract/target_schema.json`. It is **derived from Everspot** (accurate, re-runnable after any schema change) but **materialized as a diffable, reviewable, version-stamped file** — satisfying the self-modification guardrail (tracked + reversible) and decoupling the Python spine from a live Laravel boot at run time.
- **Why not `$fillable` introspection:** the target models use `guarded = []` (mass-assignment open), so `$fillable` yields nothing. The real source of truth is **migrations** (columns, types, NOT-NULL-without-default = required-on-insert) + **`casts()`** (partial dates, money, json) + **list_option type bindings** (which live in app logic).
- **A small tracked overlay** (`contract/overlay.yaml`) supplies the three things the schema can't express:
  - **list_option type bindings** — e.g. `interment_type_id → interment_type`, `suffix_id → name_suffix`, `nok_relation_id → customer_relation`.
  - **partial-date groupings** — collapse `dob_year/_month/_day/_estimated` into one logical `dob` partial-date field.
  - **attribute (custom-field) area codes** for `HasAttributes` models (e.g. property location → `location-property`).

### 6.3 Contract content (per entity)
`table`, `/api/v1/<resource>` route, and per field: `{type, nullable, required_on_insert, default, fk_target, list_option_type}`. Partial-date families and attribute-bag fields are expressed as logical fields per the overlay.

### 6.4 One loader, three call sites
`scripts/contract.py` exposes `validate_record(entity, record)`. **`assemble.py`, `emit_excel.py`, and `orion_load.py` all call it** → an unknown field, a missing required field/FK, or a type mismatch becomes a **loud build/load-time failure instead of a silent drop**. `canonical-record.schema.json` is regenerated *from* the contract, so it stops being an independent 5th definition.

### 6.5 Conformance test
A test re-runs the generator against a sandbox tenant and diffs vs. the committed file → a **stale contract fails CI** (§12).

### 6.6 Scope
v1 contract covers the non-financial-core entities: **cemetery, property_group, property, customer, interment**, plus **list_option**. Financial entities (order/payment/plan/certificate/delivery) are v1.1.

---

## 7. The Canonical Artifact & Everspot Target Facts

### 7.1 The canonical artifact
One NDJSON file per entity (`customer.ndjson`, `property.ndjson`, `interment.ndjson`, …). Each line:
- a stable **`external_id`**;
- every **FK as the parent's `external_id`** (a `*_ref`), never a row position or internal id;
- canonical-typed fields: **money in integer cents**, **phones digits-only**, **dates as partial-date objects** `{year, month, day, estimated}` (any part may be null), **value-set values resolved to the real tenant `list_option` id** (never raw codes);
- `_provenance` (`{table, row}`) and `_confidence`.

Example:
```json
{"external_id":"src:interment:48213","cemetery_ref":"src:cemetery:MAIN","deceased_ref":"src:customer:8841","status":"completed","dob":{"year":1923,"month":4,"day":null,"estimated":true},"dod":{"year":1981,"month":11,"day":2},"property_ref":"src:property:SEC-A-12-3","interment_type_id":11,"_provenance":{"table":"BURIALS","row":4821},"_confidence":0.84}
```

### 7.2 Everspot target facts (the semantics the pipeline must honor)
These are the codebase realities the contract (§6) encodes and the assembler obeys:
- **Decedents *are* Customers.** Each burial source row splits into a **Customer** (the person) + an **Interment** whose **`deceased_ref` is required and non-null**. A decedent is never buried twice → every interment gets its own distinct customer.
- **A grave space** = one **Property** under a **PropertyGroup** under a **Cemetery**. Multi-occupancy = 1 property + N interments (dedup the property by its `external_id`-action key).
- **Property requires** `property_type_id` + `property_group_id` + `cemetery_id` (all NOT NULL).
- **`interments.date` is NOT NULL.** Historical interments with no known date currently use a flagged sentinel (`1900-01-01`); making this nullable is an open Orion-ergonomics decision (§13.3d).
- **Partial dates** (`dob`/`dod`/`doi` on interment; `dob` on customer) are stored as `_year/_month/_day/_estimated` columns via `PartialDateCast`. They must be **calendar-valid** (no Feb-29 non-leap, no Apr-31) and honor the **PartialDate contract** ("day requires month" — an orphan day → null).
- **Enums are list_options.** `interment_type`, `name_suffix`, `customer_relation`, `sex`, `service_type`, etc. A value-set value must resolve to a real tenant `list_option` id **or become a question** — never invented.
- **Property location** (section/lot/space) belongs in the **Attribute engine** (custom fields, area code `location-property`), not a free-text `description`. The loader writes it as structured custom-field values via the idempotent `attribute-values/batch-upsert` Orion endpoint after each property is created (§13.3c — **DONE**, loader-side only); the `location-property` area + its attributes are resolved once over the Orion read backbone and surface as a Wave-0b reference gap if absent (ids never invented).
- **Cemetery requires** `attribute_data`/`config_data` as JSON (send `{}` strings, not arrays).
- **Models use `guarded = []`**, soft deletes, and audit fields (`created_by/updated_by/deleted_by`) on Customer/Property/Interment.
- **Ownership** is a chain (PropertyCommitment → OwnerFileLine → OwnerFile, customers attached via pivot roles) — v1.1 for financial completeness, but the non-financial core does not require it.

> The pipeline reads these from the codebase via **codebase-memory-mcp** (structural questions) + the generated contract — it does not hardcode them per client.

---

## 8. The Pipeline Stages

The target flow, driven autonomously by the `/migrate` orchestrator. `[auto]` = deterministic Python, `[AI]` = Claude Code reasoning, `[user]` = the single gate.

| # | Stage | Type | What it does | Review artifact |
|---|---|---|---|---|
| 0 | **Acquire sandbox** | auto | pull/refresh a scrubbed prod tenant → `<prefix>-sb.<root>`; stamp provenance | sandbox domain serves 200 |
| 1 | **Intake** | user→AI | user drops files + one sentence of context; orchestrator infers per-sheet "what a row is" + key column (asks only if undecidable) | `project.yaml` |
| 2 | **Ingest** | auto | raw → normalized tables; compute `source_id` + `row_hash`; immutable snapshot | `manifest.json` (counts) |
| 3 | **Profile** | auto | per-column stats, candidate keys, value-sets, data-shape signals | `profile/*.json` |
| 4 | **Wave-0 introspect** | auto/AI | read tenant reference data via Orion → `ledger/reference_data.json`; gap report | `reference_gap.md` |
| 5 | **Auto-draft mapping** | AI | draft `mapping.yaml` + `value_sets.yaml` resolved against the **target contract** + the **pattern library**; resolve value-sets to real tenant ids | `mapping_review.md` |
| 6 | **Discovery (dry assemble + validate)** | auto | dry-run assemble + validate to surface ALL projected ambiguities **and** exceptions | `needs_attention.json` |
| — | **THE QUESTION ROUND** | **user** | one batched questionnaire of everything undecidable (§9); each pre-answered | `questions.md` |
| 7 | **Reference reconcile (Wave-0b)** | auto | create missing list_options / cemetery via Orion; write new ids back to the ledger | updated `reference_data.json` |
| 8 | **Cleanse** | auto (+LLM tier, held) | deterministic primitives → `{value, confidence, method, needs_llm}`; residuals to the LLM tier when authorized | `sample_review`, `residuals.jsonl` |
| 9 | **Assemble** | auto | build the canonical graph (burial split, dedup parent, partial dates, resolved ids); validate against the contract | `canonical/*.ndjson` |
| 10 | **Validate + reconcile** | auto | schema + referential integrity + count conservation + field-level sampling | `validation/*`, `reconciliation.md` |
| 11 | **Load** | auto | **Orion API**, wave-ordered, idempotent (upsert by external_id, skip-unchanged, atomic batch-create + external-id register). `emit` = the Excel alternate. | `load/results.jsonl` |
| 12 | **Post-load reconcile + report** | auto | canonical ↔ live tenant (Orion read); one consolidated report | `REPORT.md` |
| 13 | **Next drop (v2+)** | auto | ingest → delta → assemble(scoped) → load — only NEW/CHANGED reprocess (§10) | `delta_review.md` |

**Wave dependency order** (drives load + emit): Wave 0 reference data (cemetery, list_options, property_type) → Wave 1 PropertyGroup → Property | Customer → Wave 2 Interment (+ ownership chain, v1.1) → Wave 3+ financial (v1.1).

**Key shift from today:** stages 3, 5, 6, 10 are *runnable* (auto-drafted/self-verifying), and the two old gates collapse into the **single** question round between stage 6 and stage 7.

---

## 9. The Single Question Round & Ask-Policy

The **only** point where the user is involved. A single DISCOVERY pass (profile + auto-draft mapping + dry assemble + validate) surfaces ALL ambiguities **and** projected exceptions up front, batched into **one** questionnaire. Ask once, record to the ledger, then run to completion unattended.

### 9.1 The ask-policy
**Ask ONLY what is BOTH:**
- (a) undecidable from data + codebase + the pattern library, **AND**
- (b) materially affects correctness or is irreversible.

Everything else gets a **confident default, recorded** for post-hoc review (never silently guessed — recorded and auditable).

### 9.2 What must become a question (never auto-resolved)
- a stable `source_key` is absent for a table (`kind: source_key`);
- an ambiguous value-set whose codes' meaning isn't clear from profile + naming (`kind: value_set`, low confidence);
- an unmapped column that feeds a required target field, or a required target field with no source column (`kind: unmapped` / `missing_required`);
- a value-set value that does not resolve to a real tenant `list_option` id (the `missing` set);
- a borderline entity-merge pair (`kind: entity_merge`);
- a **blocking** validation failure that data cannot fill (`kind: validation`).

### 9.3 What gets a confident default (recorded, optionally surfaced as low-friction "accept-all" item)
- a column with an obvious 1:1 target + high-confidence transform;
- a value-set value that resolves cleanly and unambiguously to exactly one tenant `list_option`;
- an obviously-ignorable column (export artifact, blank) → `unmapped` with a note;
- a warning-level validation finding (acceptable confidence, cosmetic difference).

### 9.4 Question records are JSON-first
Authored as JSON, rendered to Markdown (so future export into the customer-management app is free). Required fields: `id`, `gate`, `kind` (`value_set | unmapped | missing_required | source_key | entity_merge | validation`), `question`, `proposed_answer` (mandatory — enables "accept all"), `options`, `allow_custom`, `handoff` (`internal | client | either`), `status` (`open | answered | auto-resolved | skipped`).

### 9.5 Persistence & idempotency
Every resolved question (answered / auto-resolved / skipped-with-rationale) is written to `ledger/questions/<id>.json`. A question whose subject already has a ledger record is **never re-asked** — the answer is re-applied. This is what makes v2 cheap. Auto-resolution is always **logged** (recorded as `auto-resolved` with the proposed value), never silent.

> **Hard rule (orchestrator):** never proceed past the question round while any question is `open`.

---

## 10. The Incremental v1→v2 Engine

When the client sends an updated/corrected/next export, we do **not** re-map, re-ask answered questions, re-mint external_ids, or re-cleanse unchanged records.

### 10.1 Delta classification (join v2 to prior snapshot on `source_id`)
| Class | Condition | Action |
|---|---|---|
| **UNCHANGED** | in both, `row_hash` equal | zero work; reuse cached canonical + existing external_id |
| **CHANGED** | in both, `row_hash` differs | re-process **only that record**; re-apply ledger; external_id unchanged → load = update; a changed cell that breaks an assumption → a *targeted* question |
| **NEW** | only in v2 | full pipeline; mint a new external_id; mappings/value-sets apply automatically; only genuinely new value-set values / ambiguous entities raise questions |
| **REMOVED** | only in v1 | **never auto-delete**; listed in a "disappeared records" report for user judgment |

### 10.2 Version-aware invalidation
Cached cells record the `script_version` and `mapping_version` they were produced under. Improving a script later (bump its version) recomputes **only** the cells that script touched, surfacing only *new* exceptions — never a full redo. Changing a mapping recomputes only the affected column's cells.

### 10.3 Idempotent re-load
Delta-scoped emit/load by default (only CHANGED + NEW). Because every record carries a stable `external_id` and the loader upserts by it, a full re-load is also safe (unchanged rows are no-ops). v2 **updates** what v1 created and **inserts** the new — never duplicates.

> A clean v2 with no new value-sets/columns is nearly a **one-command refresh**: `ingest → delta → (auto) → load`.

---

## 11. The Self-Improvement Engine

Foundational machinery, built early so every run feeds it. Three learning loops, all versioned, in-repo, and test-gated.

### 11.1 The three loops
- **7a — Process knowledge.** The orchestrator's instructions and sub-skills are maintained, versioned artifacts. A persistent knowledge base (`knowledge/`) holds heuristics, question patterns, target-schema/codebase gotchas, "how X works in Everspot." The orchestrator **reads** the relevant slice at the start of a run and **appends** general learnings at the end. It may author new sub-skills for recurring sub-tasks. Goal: it asks fewer questions each run.
- **7b — Script library.** A curated, versioned, **tested** library of dataset-agnostic utilities: parsers (names, dates, phones, addresses), **validators** (calendar + partial-date-contract validity), normalizers, money. Every script is version-stamped (feeds the transform cache), covered by golden tests, documented, and **general only**. `profile`/`map`/`cleanse` reach for this library **before inventing** anything; a new data shape that demands a new utility adds it here *with tests*, so the next dataset benefits automatically.
- **7c — Permanent error remediation.** Every error is root-caused, fixed **generally**, and locked in with a **regression test** so that class cannot recur. A failure→fix→test loop + a short lessons log. Recurring data-quality issues graduate into validators (7b); recurring questions graduate into defaults/patterns (7a or the ledger).

### 11.2 How learning is triggered and kept
At the end of each run the orchestrator reflects on three questions and appends **only if the answer is general** (never client-specific):
1. a reusable heuristic / Everspot gotcha? → a knowledge entry (7a);
2. a transform/validator worth keeping? → the script library *with a golden test* (7b);
3. an error? → root-cause, general fix, regression test (7c).

Every self-edit lands as a tracked diff with a one-line rationale in `CHANGELOG.md`. Nothing ships to the general layer until the test suite passes (§12).

### 11.3 Anti-bloat (keeping AI context small over time)
Four defenses, in order of importance:

1. **Graduation (the real mechanism).** Knowledge moves *downward* from expensive prose into cheap code over its life: a recurring **data-quality lesson** → a **validator** (and is **deleted from the prose KB**); a recurring **question** → a **default in the ask-policy** (no longer asked); a recurring **transform** → a **library function + test** (referenced by name, not re-derived). The prose KB's job is to hold things only until they harden into code, so it does not grow unbounded. The append-only history lives in `CHANGELOG.md` / `LESSONS.md`, which are an **audit log never read in full** — only on demand.
2. **Tiered loading.** Three tiers: **core** (always loaded, strict size budget — ask-policy, contract summary, Everspot cheatsheet); **topics** (`knowledge/topics/*.md`, one concern each, loaded on demand); **code/tests** (never loaded as prose — consulted by *running* them).
3. **Retrieval by index + descriptions.** `knowledge/INDEX.md` carries one line per topic with a `description` + `triggers` (data-shape tags + which stage). The orchestrator reads the cheap index, then pulls only the topic files whose triggers match the current run's profile and current stage. Knowledge is **stage-scoped and shape-scoped** — nothing loads "just in case." (This mirrors the file-memory `MEMORY.md` pattern.)
4. **Subagent isolation.** Context-heavy reads (codebase introspection, profiling, old run artifacts) are delegated to subagents that return the **conclusion, not the file dumps** — the bytes never enter the orchestrator's context.

### 11.4 Self-modification guardrails (binding)
- All self-changes are **tracked files in version control**, summarized in `CHANGELOG.md`, and **reversible**. No silent free-form rewrites — append/refine with a stated rationale.
- The **test suite gates self-modification**: a prompt/skill/script change does not "ship" until the suite passes. (This is why §12 tests + §6 contract come first.)
- **Strict separation:** general learnings → the shared layer (prompt / skills / library / knowledge); client-specific facts → that client's ledger only.
- Self-edits are conservative and human-auditable; the user can review/revert any evolution at any time.

---

## 12. The Test Suite

The safety net that makes everything above safe to change. Lives in `tests/` (pytest).

- **Golden-file fixtures** — synthetic inputs → expected canonical NDJSON + expected emit payloads + expected Orion load (dry) plan. Seeded from the existing `acme` project-template. A change that alters output fails loudly with a diff.
- **Schema-conformance tests** — every canonical record validates against `canonical-record.schema.json`; every emit/Orion payload validates against the **target contract** (§6).
- **Contract-conformance test** — re-run the contract generator against a sandbox tenant and diff vs. the committed `target_schema.json`; a stale contract fails.
- **Script-library unit tests** — golden inputs/outputs for every cleansing primitive and validator (this *is* 7b's coverage).
- **Regression tests** — one named test per fixed error (7c), institutionalizing prior fixes: snapshot case-normalization, the `__NULL__` sentinel, partial-date calendar + contract validity, the non-atomic-batch duplication, the canonical↔emit FK name mismatch, etc.
- **(Optional) live-sandbox contract test** — a smoke load against a sandbox.

**Gate:** the suite must pass before any self-modification (§11.4) or schema/contract change ships.

---

## 13. Orion API Integration

### 13.1 Read backbone (works today)
Orion (`/api/v1/<resource>`) is the read/reference backbone from day one: Wave-0 tenant introspection (resolve list_option ids, read cemeteries/products/property_types/attribute schema, dedup against existing customers/properties). `filterableBy/sortableBy=['*']` + pagination on every exposed resource. **There is NO auth-guard bug** — the token middleware sets the user on the `web` guard; Sanctum resolves `config('sanctum.guard')=['web']` first, so policy-enforced reads/writes work given a `user-id` header for a user with the right Spatie permissions. **Never "fix" a guard mismatch; never touch `AuthenticateTenantApiToken` or token generation without explicit approval.**

### 13.2 Write path (the primary load path now)
`orion_load.py` loads the canonical NDJSON in wave order, POSTs each record, registers its `external_id` on the polymorphic `external-ids` resource, resolves FKs via the external_id→internal-id map built as it loads, and is idempotent: prefetch existing external-ids → skip already-loaded-unchanged, PATCH delta-CHANGED, batch-create NEW (chunks of 100) + batch-register. `config/orion.php` `transactions.enabled=true` makes batches atomic (a failed batch rolls back, so the per-record fallback is safe). Auth: tenant token (`staff_api_token` = sha256 of plaintext, ≤7-day expiry, IP-whitelisted) + `user-id` header. Prefix `/api/v1`; `verify=False` for Herd's self-signed cert.

### 13.3 Write ergonomics backlog (Everspot repo — SPEC + approval each; do NOT touch auth)
Each is a user decision, to be specced separately before coding:
- **(a)** upsert-by-external_id **OR** accept `external_id` in the create payload + atomic `HasExternalIds` registration (removes the prefetch-all + check-then-create round-trip).
- **(b)** batch transactions default-on for the migration token.
- **(c)** a first-class **Attribute-engine write path** for grave location — **DONE** (loader-side, via the existing `attribute-values/batch-upsert` Orion endpoint; no longer punted into `description`).
- **(d)** consider **nullable `interment.date`** for historical interments (currently a flagged `1900-01-01` sentinel).

> Optional Orion 1d items: validation Request classes (safe); a migration-token type lifting the 7-day cap while keeping the IP whitelist (**auth-adjacent — explicit approval required**).

---

## 14. Sandbox Automation (the load target)

The pipeline loads into a **dev sandbox** pulled from production — never the live client tenant. One codebase; role decided by config (`config/sandbox.php`).

- **Server role (production):** authenticated central-domain export endpoints — `GET /api/sandbox/tenants`, `POST /api/sandbox/exports {tenant_id}`, `GET /api/sandbox/exports/{id}`. Dumps tenant DB → zip → S3 (`primary` disk), returns a signed URL. Hardened by `AuthorizeSandboxExportApi` (enabled-flag → 404, token → 401, IP allowlist → 403) + throttle. Async status in the central `sandbox_files` catalog (type-discriminated: `export` rows on S3, `import` rows on the non-suffixed `sandbox_artifacts` disk).
- **Client role (dev):** `ProductionSandboxApiClient` (list/request/poll/download). `pullFromProduction()` = request+poll+download → import via the manifest/zip path with provenance (`source`, `source_tenant_id`, `pulled_at`) + post-import secret scrubbing (Stripe/QBO/mail nulled). `refreshFromProduction()` is **cache-first** (rebuild from the last cached artifact offline; fall back to a fresh pull on miss).
- **Deterministic domain:** `<prod-prefix>-sb.<DEFAULT_ROOT_URL>` with `-1/-2` collision uniquify. Because refresh deletes first, a re-pull lands on the **same** domain — the operator targets by domain, never repoints.
- `sandbox:prune-files` (scheduled weekly) keeps N-per-source + an age cap.

A typical loop: pull a fresh sandbox of the client's current production tenant, run the migration into it, reconcile, iterate the ledger until clean, then run the same ledger against the real target. Refresh re-baselines the sandbox between iterations without losing the ledger (the ledger lives in the project dir, not the tenant).

---

## 15. User Experience & Review Surfaces

### 15.1 The cleansed data is visible *outside* Everspot
Every run materializes the data on disk before and independent of loading:
- **`runs/<ts>/canonical/*.ndjson`** — the assembled records exactly as they'll load (external-id-keyed, FKs resolved, dates composed, money in cents). Machine truth.
- **`runs/<ts>/emit/wave*.xlsx`** — the same data as **wave-ordered Excel files you can open and eyeball**, per entity.
- **`runs/<ts>/needs_attention.json`** — every flagged record/cell (joint names, junk phones, out-of-range dates, unresolved references), **grouped by kind** so structural cases surface instead of drowning.

So the user can audit the exact records — open the Excel, grep the NDJSON — and compare against source, with zero Everspot access.

### 15.2 How the user reviews what happened
- **`runs/<ts>/REPORT.md`** — the single consolidated report: **count conservation** (source → canonical → loaded, with anything dropped called out), what loaded per entity, the questionnaire answered, data-quality flags, and the post-load reconcile (canonical ↔ what's live now). The design intent: answers "is this correct and what do I need to look at?" in one screen.
- **The evidence behind it:** the canonical NDJSON / emit Excel (above), the answered questionnaire, and the **ledger as a full audit trail** — every decision, every minted id, every answer recorded and diffable. A second drop's report shows exactly what changed vs. last time.

### 15.3 The four review lenses
Review is progressively narrowing, not one monolithic approval: **shape** (profile) → **mapping** (the question round) → **transformation** (cleanse before→after + confidence histogram) → **correctness** (validate: schema/referential/count-conservation + reconciliation, with examples of offending rows).

---

## 16. Directory Structure

```
everspot-brain/migrations/               # THE GENERAL LAYER (tracked, shared across clients; its own repo)
├── CLAUDE.md                            # operating instructions (auto-loaded when run here)
├── .claude/commands/migrate.md          # the /migrate orchestrator command
├── SPEC.md                              # this file — the design source of truth
├── pipeline.toml                        # MACHINE-LOCAL config (everspot_codebase_path); gitignored; env wins (§18)
├── pipeline.example.toml                # committed template for pipeline.toml
├── CHANGELOG.md                         # append-only audit of self-edits (never read in full)
├── LESSONS.md                           # 7c failure→fix→test log (audit, not context)
├── contract/                            # §6 the target contract
│   ├── target_schema.json               #   generated from Everspot
│   └── overlay.yaml                     #   list_option bindings, partial-date groups, attr areas
├── knowledge/                           # §11 7a the general brain (prose)
│   ├── INDEX.md                         #   tiny: one line/topic + description + triggers + stage
│   ├── core/                            #   ALWAYS loaded (size-budgeted)
│   │   ├── ask-policy.md
│   │   ├── everspot-cheatsheet.md
│   │   └── contract-summary.md
│   └── topics/                          #   loaded ON DEMAND by trigger
│       ├── name-parsing.md
│       ├── partial-dates.md
│       └── orion-load-gotchas.md
├── schemas/                             # JSON Schemas (canonical-record regenerated from contract)
├── scripts/                             # §11 7b the engine + script library (code, never loaded as prose)
│   ├── migrate.py                       #   the CLI
│   ├── snapshot.py identity.py delta.py ledger.py external_ids.py transform_cache.py
│   ├── cellcontract.py cleanse_runner.py contract.py config.py
│   ├── assemble.py emit_excel.py orion_client.py orion_load.py reconcile.py llm_fallback.py
│   ├── parse_name.py normalize_date.py normalize_phone.py standardize_address.py
│   │   to_cents.py digits_only.py resolve_list_option.py
│   ├── LIBRARY.md                       #   index of utilities + versions
│   └── .venv/                           #   NOT committed (rebuild per §18)
├── tests/                               # §12 the safety net (gates all self-changes)
│   ├── golden/  unit/  regression/  conformance/
└── project-template/                    # a populated acme example

.context/migration-projects/<client>/    # THE CLIENT LAYER (per-client, gitignored)
├── project.yaml                         # client meta; sandbox target; source-key declarations
├── ledger/                              # durable CLIENT memory (loaded only for this client)
│   ├── mapping.yaml  value_sets.yaml  reference_data.json
│   ├── entities.jsonl  cell_overrides.jsonl  external_ids.json
│   ├── parse_rules.yaml  transform_cache.sqlite  questions/*.json
├── snapshots/<v>/{raw/, tables/, source_index.parquet, profile/, delta.json}
└── runs/<v>/{clean/, canonical/, validation/, questions.md, answers.json,
              emit/, load/, needs_attention.json, REPORT.md}
```

**Relocation — DONE (2026-06-27).** The general layer now lives in its own repo at `everspot-brain/migrations/` (a sibling of `system-wiki/`). Only the Orion build-out + the `migration:generate-contract` command stay in the Everspot repo; the pipeline *reads* Everspot and invokes the contract generator via `config.generate_contract_argv()` (which passes `--pipeline-root` so the Everspot-side command writes the contract back here). Because the pipeline is no longer inside Everspot, the relative default codebase-path no longer points at Everspot, so the machine-local `pipeline.toml` (or `EVERSPOT_CODEBASE_PATH`) must be set per §18 — `scripts/config.py` resolves the override ahead of the default. `/migrate` is run from this directory.

---

## 17. Roadmap & Sequencing

**Foundation first** (makes every later change safe AND lets each run feed the learning loops):
1. **§12 test suite** — golden fixtures + schema/contract conformance + regression tests institutionalizing prior fixes.
2. **§6 target contract** — generator + overlay + `contract.py` + wire the three call sites + conformance test.
3. **§11 self-improvement substrate** — `knowledge/` (INDEX + core + topics), `CHANGELOG.md`, `LESSONS.md`, `LIBRARY.md`.

**Then:** runnable **profile + auto-draft mapping** (§8 stage 3/5) and **runnable validate/reconcile** (§8 stage 10) → the **single question round** (§9) → **the `/migrate` orchestrator** (§8, idempotent + resumable).

**Then:** **Orion write ergonomics** (§13.3, after approval), deepen §11, and robustness for unattended runs: fuzzy rematch in `delta` (key drift ≠ remove+add), a first-class partial-date/data-quality subsystem + standardized report, full structured error capture + resumable/checkpointed load, and a PII-id policy (opaque/hashed vs. documented exposure of names in source_ids/external_ids).

**Land incrementally, each with tests.** Do not attempt it all at once.

---

## 18. Binding Rules & Locked Decisions

**Locked decisions (do not re-litigate):**
- **Claude Code orchestrates** (not external Python/LangGraph); Python does source-side cleansing; PHP does Orion + the loader.
- **Orion API = the primary load path** (Excel emit = the alternate); Orion read = the reference backbone from day one.
- **One convergence point** = the canonical external-id-keyed NDJSON artifact.
- **One question round**, JSON-first, proposed-answer-mandatory; the ask-policy (§9.1) governs.
- **Identity anchored to the client's own key**, surfaced as a question when absent — never silently guessed; `source_id → external_id` never moves.
- **V1 scope = non-financial core** (Customer, Property, Interment, + Cemetery/list_option reference); financial tail is v1.1.
- **Three memoization tiers**; version-aware; loads delta-scoped and idempotent.
- **Deterministic-first, LLM-fallback**; LLM never does arithmetic; re-validate every LLM output through the same library.

**Hard rules (binding):**
- **CLAUDE.md governs.** Never `git checkout` (ask the user). Never `./vendor/bin/pint` without a path. Use **codebase-memory-mcp** for structural code questions (also how the pipeline self-answers schema questions). Use `tenancy()->initialize()/->end()` for tenant DB access.
- **AI may process real client data** per the user's standing authorization — there is **no PII prohibition** on the LLM tier and **no `--authorize-llm` gate**. `MIGRATION_LLM_DRYRUN=1` remains an **optional** cost/speed/determinism switch (offline path), **not** a safety gate. The tier goes live **only** when the user opts in **and** `ANTHROPIC_API_KEY` is present (or an explicit client is passed); with no key it physically cannot call and stays deterministic — so default/CI runs never fire a live call. Every LLM output is still re-validated through the same Python library (the library, not the model, is truth).
- **General fixes only** — client-specific decisions live in a project's ledger/mapping, never in `scripts/`.
- **No Orion auth-guard bug exists** — never "fix" one; do not touch `AuthenticateTenantApiToken` / token generation without explicit approval.
- Changes stay **uncommitted on the working branch unless the user asks for a PR** (base `dev`, never `main`).
- **Use sub-agents** for context-heavy work. **Update the `data-migration-pipeline` memory entry** as work lands.

**Environment:** PRODUCTION = `/Users/cashkalina/code/everspot` (Herd `everspot.test`). DEV/SANDBOX = the `manama-v1` workspace (Herd `manama-v1.test`). Live sandbox tenant `bellschapel-sb.manama-v1.test`, user `cash@everspot.io` / `password123` (Super Admin), API token on the tenant (re-provision if expired). Orion prefix `/api/v1`; `verify=False` for Herd's cert.

**Everspot codebase path (configurable hook — survives the §16 relocation).** The pipeline needs the Everspot checkout on disk for (a) codebase-memory-mcp / grep self-introspection and (b) `php artisan migration:generate-contract` (run with `cwd` set to that dir). `scripts/config.py:everspot_codebase_path()` resolves it with precedence **env `EVERSPOT_CODEBASE_PATH` → `pipeline.toml` (key `everspot_codebase_path`) → default** = the repo root two levels above the pipeline root (i.e. today's in-Everspot layout, `docs/migration-pipeline/` → repo root). When the general layer moves into its own repo (§16), set `EVERSPOT_CODEBASE_PATH` (or `pipeline.toml`) and nothing else changes. `config.artisan_command(...)` builds the artisan argv; `config.has_php()` / `everspot_codebase_exists()` guard the runner.

**LLM:** `ANTHROPIC_API_KEY` enables the live tier (optional; absent ⇒ deterministic, no call). `MIGRATION_LLM_DRYRUN=1` forces the offline path regardless of key (cost/determinism switch). `MIGRATION_LLM_MODEL` overrides the model.

**Rebuild the venv** (not committed):
```bash
cd docs/migration-pipeline && python3 -m venv .venv
./.venv/bin/pip install pandas pyarrow pyyaml openpyxl python-dateutil nameparser \
  phonenumbers rapidfuzz requests anthropic jsonschema pytest
```

---

## 19. Glossary

- **Project** — one client/engagement; holds a ledger + many snapshots + runs.
- **Snapshot** — one immutable drop of client data (`v1`, `v2`, …).
- **Ledger** — the project's durable memory (decisions, value-sets, entities, external_ids, transform cache, answered questions, reference snapshot).
- **Run** — disposable per-drop working artifacts; regenerable from `snapshot + ledger`.
- **source_id** — `"<table>:<source_key>"`; the stable identity of a source record.
- **external_id** — derived from `source_id`, permanently bound; the canonical/load key (`src:<entity>:<token>`).
- **Canonical artifact** — the external-id-keyed NDJSON, one file per entity; the single convergence point.
- **Target contract** — the codebase-derived machine-readable schema (`contract/target_schema.json` + `overlay.yaml`) every stage validates against.
- **Transform cache (Tier 3)** — value-level parse memory: each distinct string parsed at most once per transform version.
- **Wave 0 / Wave-0b** — tenant introspection / missing-reference-data creation.
- **The question round** — the single batched HITL gate.
- **Graduation** — promoting a recurring prose lesson into deterministic code (validator/default/library fn) and removing it from the prose KB — the primary anti-bloat mechanism.
</content>
</invoke>
