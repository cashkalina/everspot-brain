# Migration Project Template (EXAMPLE)

This directory is a **populated example** of a single migration project, for the
fictional client **Acme Memorial Gardens** (`acme-cemetery`). It shows the layout
`/migrate init <client-slug>` scaffolds and how the artifacts fit together. All
content is sample data, clearly marked `EXAMPLE`.

For the *why* behind this structure, read [`../SPEC.md`](../SPEC.md) (the design
source of truth — §4 the three-layer memory model, §16 the directory structure).
The JSON Schemas every file here validates against live in
[`../schemas/`](../schemas/).

## The three-part split (the core design)

A project keeps **Ledger**, **Snapshots**, and **Runs** strictly separate. That
separation is what makes v2+ drops cheap (SPEC §4, §10).

```
acme-cemetery/                  # the project root (named by client slug)
  project.yaml                  # client meta · sandbox target · per-table source_key declarations · snapshot list
                                #   └ schema: schemas/project.schema.json
  ledger/                       # DURABLE MEMORY — survives every drop, keyed by what a decision is ABOUT
    mapping.yaml                #   column → target field + transform (versioned)        [mapping.schema.json]
    value_sets.yaml             #   coded-value translations + provenance                [value_sets.schema.json]
    parse_rules.yaml            #   human-PINNED transform-cache rules (Tier-3) source of truth [parse-rules.schema.json]
    transform_cache.sqlite      #   derived value-cache: parse each distinct string once (seeded from parse_rules.yaml)
    external_ids.json           #   source_id → external_id → everspot_id (minted once)  [external-ids.schema.json]
    questions/                  #   answered question records (canonical; prevents re-asking)
      q_0007.json               #     one answered value_set question                    [question.schema.json]
  snapshots/                    # immutable drops; raw bytes are never mutated
    .gitkeep                    #   (v1/, v2/, … land here: raw/, tables/, source_index.parquet, delta.json)
                                #     source_index → schemas/source-index.schema.json
                                #     delta.json    → schemas/delta.schema.json
  runs/                         # DISPOSABLE per-drop working artifacts (regenerable from snapshot + ledger)
    v1/
      questions.md              #   question round RENDERED from the JSON question records (operator edits in place)
                                #   (also: clean/, canonical/*.ndjson, validation/, answers.json, output/, load/, report/)
                                #     canonical NDJSON → schemas/canonical-record.schema.json
  logs/                         # provenance / audit trail
    .gitkeep
```

## What's illustrated in this example

- **`project.yaml`** — three source tables (`MASTER_OWNERS`, `PLOTS`, `BURIALS`).
  Two have a confirmed `source_key`; `BURIALS` has **no stable key**, so its
  identity is `deferred` to a question round item rather than guessed (SPEC §5, §9).
- **`ledger/mapping.yaml`** — realistic columns including a `split_name`
  (`OWNER_NAME` → name parts), a `value_map` (`STAT` → status), an `external_id`
  declaration, an `unmapped` column, a `derive` (FK link), and a
  `reference_resolution` block resolving suffixes to real tenant list_option IDs.
- **`ledger/value_sets.yaml`** — `STAT` codes `A/R/C` → `customer`/`lead`, each with
  `decided_by` / `decided_at` provenance, sourced from question `q_0007`.
- **`ledger/parse_rules.yaml`** — two human-**pinned** Tier-3 transform-cache rules
  (SPEC §5 memoization tiers): a gnarly clergy/compound-surname name
  (`"St. John-Smith, Rev. Dr. A."` → name parts) and an ambiguous MDY date pinned
  with an explicit `context_signature`. Pinned rules win over derived entries and are
  version-independent; they seed `transform_cache.sqlite` (the fast derived cache).
- **`ledger/external_ids.json`** — two source-keyed mints plus one `canonical:*`
  merged entity (a decedent who is also an owner).
- **`ledger/questions/q_0007.json`** — the canonical JSON form of an *answered*
  value-set question.
- **`runs/v1/questions.md`** — how a set of JSON question records **renders to
  markdown** for the operator: checkboxes, blanks, and proposed answers.

## Identity is sacred

Every `source_id` (`<table>:<source_key>`) maps to a permanent `external_id`. The
same client record always becomes the same Everspot record across every drop and
re-load — that is what makes loads idempotent (upsert by `external_id`) and v2
*update* rather than duplicate. See SPEC §5.
