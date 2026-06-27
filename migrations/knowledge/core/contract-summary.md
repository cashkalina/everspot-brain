# core/contract-summary.md — the target contract (§6), one screen

**Always loaded. Keep tight.** This is the stable *summary + pointer*. The contract
itself is generated and committed; **do not copy its contents here** — read the files.

## What it is

The single machine-readable definition of every target entity, **derived from
Everspot**. It kills schema drift (the old failure: 4 drifting definitions per
entity — canonical schema, `assemble.py`, `emit_excel.py`, `orion_load.py` — three of
which silently diverged, ~50 drifts including silent-drop bugs).

## Where it lives (the source of truth — read these, not this file)

- `contract/target_schema.json` — **generated** from Everspot: a small artisan generator boots tenant context, introspects the live tenant DB (columns/types/nullability/defaults/FKs), reflects each model's `casts()`, and writes a diffable, version-stamped file.
- `contract/overlay.yaml` — the small tracked overlay supplying the three things the schema can't express:
  - **list_option type bindings** (e.g. `interment_type_id → interment_type`, `suffix_id → name_suffix`, `nok_relation_id → customer_relation`);
  - **partial-date groupings** (collapse `dob_year/_month/_day/_estimated` → one logical `dob`);
  - **attribute (custom-field) area codes** for `HasAttributes` models (e.g. property location → `location-property`).

> NOTE: the contract files are authored by a separate workstream. This page is the
> stable description, not a snapshot of their current contents.

## Per-field content (§6.3)

`table`, the `/api/v1/<resource>` route, and per field:
`{type, nullable, required_on_insert, default, fk_target, list_option_type}`.
Partial-date families and attribute-bag fields are expressed as **logical** fields per
the overlay.

## One loader, three call sites (§6.4)

`scripts/contract.py` exposes `validate_record(entity, record)`. **`assemble.py`,
`emit_excel.py`, and `orion_load.py` all call it.** An unknown field, a missing
required field/FK, or a type mismatch is a **loud build/load-time failure, never a
silent drop**. `canonical-record.schema.json` is regenerated *from* the contract (so it
is not an independent 5th definition).

## Drift = a loud failure (§6.5)

A conformance test re-runs the generator against a sandbox tenant and diffs vs. the
committed file → **a stale contract fails CI**.

## Scope (§6.6)

v1: **cemetery, property_group, property, customer, interment** + **list_option**.
Financial entities are v1.1.
