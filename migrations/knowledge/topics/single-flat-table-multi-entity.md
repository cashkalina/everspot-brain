# topics/single-flat-table-multi-entity.md

> **triggers:** `flat-register`, `one-row-many-entities`, `multi-occupancy` · stages: map, assemble

Loaded when the profile shows **one flat table where a single row carries more than one
target entity** — e.g. a burial register where each row is a grave that may also hold a
decedent.

## The shape

One flat row → **Property + Customer + Interment**. The grave location (Section/Row/Grave
+ lat/long) is the property; the decedent's names/dates are the customer + interment.

## How the assembler handles it

`mapping.yaml` declares `secondary_entities`. `assemble._build_combined_table` honors it:

- **routes columns by entity-qualified target** — `property.section`, `customer.last_name`, `interment.dod.year`, `customer.attributes.maiden_name`;
- **dedups the parent** (the property) by its `external_id`-action key → N rows on the same grave produce **1 property + N interments** (multi-occupancy);
- **emits a secondary entity only when the row has triggering evidence** — a non-null field outside `_NON_TRIGGER_FIELDS` (e.g. an interment is created only if burial_type / first_name / a date is present; a surname-only-no-evidence row stays property-only);
- composes split Y/M/D columns via `_compose_partial_date`; resolves coded values via `_resolve_reference`.

*(Historical bug: `secondary_entities` was once dead config — `build_table` dispatched
each table to a single hardcoded builder by primary `target_entity` and never read it.
The combined-table path fixed that; see LESSONS.md.)*

## Identity when there's no client key

A flat register often has **no stable client PK**. Identity then = a composite of the
identifying columns (e.g. Section + Row + Grave + Surname + First). If that composite is
unique, it's a confident `source_key`; if not, it's a `source_key` question (never
guessed silently). See `core/ask-policy`.

## Domain rules to honor (general to this shape)

- multi-occupancy = 1 property + N interments;
- **a decedent is never buried twice → every interment gets its own distinct customer** (no cross-row merge, even on a shared surname);
- decedent dates (birth/death) go on the **interment** (`dob`/`dod`/`doi`), not the customer; the customer carries names + suffix_id + maiden_name.

*Illustrative (general pattern, not a client fact):* a 2,421-row flat register with 2
double-occupancy graves assembled to 2,419 properties + N customers + N interments with 0
dangling refs — the parent-dedup + triggering-evidence rules are what made the counts come
out right.
