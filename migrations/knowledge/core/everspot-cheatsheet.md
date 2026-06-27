# core/everspot-cheatsheet.md — §7.2 target facts (fast reference)

**Always loaded. Keep tight.** The load-target semantics the contract (§6) encodes
and the assembler obeys. Read these from the codebase via **codebase-memory-mcp** +
the generated contract — never hardcode them per client.

## Entities & the burial split

- **Decedents ARE Customers.** Each burial source row splits into a **Customer** (the person) + an **Interment**. The interment's **`deceased_ref` is required, non-null**.
- A decedent is never buried twice → **every interment gets its own distinct Customer** (no cross-row merge, even on a shared surname).
- **Grave space = one Property** under a **PropertyGroup** under a **Cemetery**.
- **Multi-occupancy = 1 Property + N Interments.** Dedup the property by its `external_id`-action key (N rows on the same grave → 1 property, N interments).

## Required fields (NOT NULL on insert)

- **Property** requires `property_type_id` + `property_group_id` + `cemetery_id`.
- **Interment** requires `deceased_ref` and **`interments.date` (NOT NULL)**. Historical interments with no known date use a **flagged sentinel `1900-01-01`** (nullable date is an open Orion-ergonomics item).
- **Cemetery** requires `attribute_data` / `config_data` — send as JSON **strings** `"{}"`, not arrays.

## Partial dates

- `dob` / `dod` / `doi` on interment; `dob` on customer. Stored as `_year/_month/_day/_estimated` columns via `PartialDateCast`.
- Must be **calendar-valid** (no Feb-29 non-leap, no Apr-31 → drop the offending day).
- Honor the **PartialDate contract: "day requires month"** — an orphan day → null.

## Enums = list_options

- `interment_type`, `name_suffix`, `customer_relation`, `sex`, `service_type`, etc.
- A value-set value must **resolve to a real tenant `list_option` id OR become a question** — **never invented**. (Wave-0b can create missing options, then writes ids back to the ledger.)

## Property location (section/lot/space)

- Belongs in the **Attribute engine** (custom fields, area code `location-property`), not a free-text `description`.
- The loader writes section/lot/space as structured custom-field values via the idempotent `attribute-values/batch-upsert` Orion endpoint **after** each property is created (matched by attribute `key` → upsert-in-place, so re-runs never duplicate). Location is **no longer** put in `description`.
- The `location-property` area + its section/lot/space attributes are tenant reference data, resolved once over the Orion read backbone (like list_options). If absent they surface as a **Wave-0b reference gap** (`reference_gaps` in `load_report.json`) — ids are **never invented**.

## Model conventions

- Models use **`guarded = []`** (mass-assignment open → `$fillable` introspection yields nothing; the contract is derived from migrations + `casts()` + list_option bindings).
- Soft deletes; audit fields (`created_by/updated_by/deleted_by`) on Customer / Property / Interment.

## Out of v1 scope

- **Ownership** is a chain (PropertyCommitment → OwnerFileLine → OwnerFile; customers via pivot roles) — **v1.1**. The non-financial core does not require it.
- Financial entities (order / payment / plan / certificate / delivery) — **v1.1**.
