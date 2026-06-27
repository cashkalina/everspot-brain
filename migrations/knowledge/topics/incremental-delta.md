# topics/incremental-delta.md

> **triggers:** `v2`, `re-drop`, `incremental` · stages: ingest, delta, assemble, load

Loaded when this is **not the first drop** — the client sent an updated / corrected /
next export. We do **not** re-map, re-ask answered questions, re-mint external_ids, or
re-cleanse unchanged records.

## Delta classification (§10.1 — join v2 to prior snapshot on `source_id`)

| Class | Condition | Action |
|---|---|---|
| **UNCHANGED** | in both, `row_hash` equal | zero work; reuse cached canonical + existing external_id |
| **CHANGED** | in both, `row_hash` differs | re-process **only that record**; re-apply ledger; external_id unchanged → load = update; a changed cell that breaks an assumption → a *targeted* question |
| **NEW** | only in v2 | full pipeline; mint a new external_id; mappings/value-sets apply automatically |
| **REMOVED** | only in v1 | **never auto-delete**; list in a "disappeared records" report for user judgement |

## The invariants

- **`source_id` → `external_id` is permanent.** Never re-mint an external_id for a record that already has one. This is what makes loads idempotent (upsert by external_id) and v2 **update**, not duplicate.
- **Never auto-delete REMOVED.** Surface it; let the user decide.

## The three memoization tiers (§5.3 — why a re-drop is cheap)

| Tier | Key | Decides |
|---|---|---|
| **1 — row** | `source_id + row_hash` | which rows to process at all |
| **2 — cell** | `source_id + column + script/mapping version` | within a CHANGED row, skip cells whose own input didn't change |
| **3 — value (transform cache)** | `transform + version + normalized_input [+ context_signature]` | has *this exact string* ever been parsed by this transform? |

Tier 3 guarantees **no second LLM call even when other cells in the row change**, and
dedups within a drop. `context_signature` captures only the column-level decisions that
change the output (e.g. `name_order=last_first`, `date_format=MDY`) — so a parse isn't
reused under a since-changed interpretation. Human-pinned rules
(`ledger/parse_rules.yaml`) **win and are version-independent**; LLM entries are cached
version-scoped behind a confidence floor; a version bump lazily recomputes only
re-encountered strings.

## Version-aware invalidation (§10.2)

Cached cells record their `script_version` + `mapping_version`. Bumping a script
recomputes **only** the cells that script touched; changing a mapping recomputes **only**
the affected column's cells. Never a full redo.

*Illustrative (general pattern):* in a synthetic v1→v2 run, a CHANGED row whose name was
unchanged got a transform-cache **hit** (zero re-parse), and external_ids stayed stable
across drops/drops-removals.

## The one-command refresh (§10.3)

A clean v2 with no new value-sets/columns is nearly `ingest → delta → (auto) → load`.
Loads are delta-scoped by default but a full re-load is also safe (unchanged rows are
no-ops).
