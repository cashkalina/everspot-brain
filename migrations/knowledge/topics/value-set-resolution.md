# topics/value-set-resolution.md

> **triggers:** `coded-values`, `enums`, `unresolved-ref` · stages: profile, map, wave-0b, assemble

Loaded when the profile shows columns with a small, repeating set of codes/labels
(burial type, suffix, relation, sex, service type) — i.e. anything that maps to a tenant
`list_option`.

## The rule

A value-set value must resolve to a **real tenant `list_option` id**, or it becomes a
**question**. **Never invent an id.** This is the single most important discipline here —
an invented id silently corrupts the target.

## How resolution works

1. **Wave-0** introspects the tenant via Orion → `ledger/reference_data.json` (the real option lists and their ids).
2. `scripts/resolve_list_option.py` (`rapidfuzz`) matches a raw value against that snapshot: exact → confident; strong fuzzy (≥90) → medium; weak (75–90) → low-confidence; unknown → `needs_llm`.
3. `assemble._resolve_reference` resolves coded cells to ids; an unresolved value raises a `unresolved_ref` needs-attention (never invented, never papered over).

## Wave-0b (creating what's missing)

After the question round, **Wave-0b creates the missing list_options via Orion**, then
**writes the new ids back to the ledger** (`reference_data.json` + the mapping's
`reference_resolution`) and re-assembles. The unresolved set should drop to zero.

*Illustrative (general pattern):* a flat register's `burial_type` column held several
types the seeded tenant didn't have; Wave-0b minted them as `interment_type` options,
wrote the ids back, and the unresolved-ref count went from hundreds to zero on re-assemble.

## What becomes a question vs. a default (see core/ask-policy)

- resolves cleanly + unambiguously to exactly one option → **confident default** (recorded);
- ambiguous meaning, or no matching option that data/codebase can settle → **`value_set` question**.

## Graduation

A value-set mapping that recurs identically across clients is **client-specific** and
stays in the ledger — it does **not** graduate to the shared layer. Only the *resolution
mechanism* is general (and already lives in the library).
