# knowledge/INDEX.md — the retrieval surface (§11.2, §11.3)

The orchestrator reads **only this index** at the start of a run (it is cheap), then
pulls the topic files whose `triggers` match the current run's data-shape and stage.
Nothing else loads "just in case." This mirrors the file-memory `MEMORY.md`
one-line-pointer pattern.

## The tier model (what is loaded, when)

| Tier | What | Loading rule |
|---|---|---|
| **core** | `core/*.md` — ask-policy, Everspot cheatsheet, contract summary | **Always loaded.** Strict size budget — keep lean and scannable, no padding. |
| **topics** | `topics/*.md` — one concern each | **On demand**, only when a topic's `triggers` match this run's profile + current stage. |
| **code / tests** | `scripts/*.py`, `tests/*` | **Never loaded as prose.** Consulted by *running* them. The library (`scripts/LIBRARY.md`) is the index of what exists. |

## The graduation rule (the primary anti-bloat mechanism — §11.3)

Knowledge moves **downward** from expensive prose into cheap code over its life. The
prose KB holds a thing only until it hardens into code:

- a recurring **data-quality lesson** → a **validator** in the script library, **and is deleted from the prose KB**;
- a recurring **question** → a **default in the ask-policy** (`core/ask-policy.md`), so it is no longer asked;
- a recurring **transform** → a **library function + golden test** (`scripts/LIBRARY.md`), referenced by name, not re-derived.

So a topic file is provisional. When it graduates, delete its prose and leave only a
one-line CHANGELOG note recording where it went. `CHANGELOG.md` and `LESSONS.md` are
append-only **audit logs, never read in full** — consulted on demand only.

## core (always loaded)

| File | Purpose |
|---|---|
| `core/ask-policy.md` | §9 ask-policy as operational rules: when to ask vs. record a confident default. |
| `core/everspot-cheatsheet.md` | §7.2 Everspot target facts (the load-target semantics) as a fast reference. |
| `core/contract-summary.md` | One-screen summary + pointer to the generated target contract (§6). |

## topics (loaded on demand by trigger)

| Topic | Description | Triggers (data-shape tags · stage) |
|---|---|---|
| `name-parsing` | nameparser usage; joint two-people-in-one-cell (no auto-split, flag `two_people`→needs_llm); compound given-names over-segment. | `person-names`, `joint-names`, `freetext-name` · cleanse, assemble, entity-resolve |
| `partial-dates` | PartialDateCast `_year/_month/_day/_estimated`; calendar validity; "day requires month"; 2-digit-year ambiguity; interment.date NOT-NULL sentinel. | `dates`, `dob-dod`, `partial-dates`, `split-ymd-columns` · cleanse, assemble |
| `value-set-resolution` | enums → real tenant `list_option` ids or a question; Wave-0b creates missing options then writes ids back to the ledger; never invent an id. | `coded-values`, `enums`, `unresolved-ref` · profile, map, wave-0b, assemble |
| `single-flat-table-multi-entity` | one flat row → Property + Customer + Interment via `secondary_entities`; dedup parent by external_id-action key; emit secondary only on triggering evidence. | `flat-register`, `one-row-many-entities`, `multi-occupancy` · map, assemble |
| `orion-load-gotchas` | `/api/v1` prefix; `verify=False` for Herd cert; cemetery JSON-string fields; external-id `model_type`=FQCN; atomic batches (transactions.enabled); token model (no auth bug); `paginate()` not `search()`. | `orion-load`, `live-load`, `reference-write` · wave-0, wave-0b, load, reconcile |
| `sandbox-acquisition` | pull/refresh a scrubbed prod tenant → deterministic `<prefix>-sb.<root>` domain; refresh is cache-first; load into the sandbox, never the live tenant. | `sandbox`, `acquire-target` · acquire-sandbox |
| `incremental-delta` | NEW/CHANGED/UNCHANGED/REMOVED on source_id; reuse cached output + external_ids for unchanged; never re-mint or auto-delete; the 3 memoization tiers. | `v2`, `re-drop`, `incremental` · ingest, delta, assemble, load |

## Rules baked into retrieval

- Knowledge is **stage-scoped and shape-scoped** — a topic loads only when both its
  shape tag is present in the profile and its stage is the current stage.
- Context-heavy reads (codebase introspection, profiling, old run artifacts) go to a
  **subagent** that returns the *conclusion*, not file dumps — the bytes never enter
  the orchestrator's context (§11.3 #4).
- Client-specific facts never live here. General only. Bell's Chapel / CCMP appear in
  topic files **only as illustrative examples of a general pattern**.
