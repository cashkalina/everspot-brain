# topics/name-parsing.md

> **triggers:** `person-names`, `joint-names`, `freetext-name` · stages: cleanse, assemble, entity-resolve

Loaded when the profile shows person-name columns (single freetext name cell, or
"Last, First", or a column that may hold more than one person).

## The library

`scripts/parse_name.py` (`nameparser` / `HumanName`) → a cell whose value is
`{title, first, middle, last, suffix, nickname}`. Reach for it before inventing any
name logic. Reversed `"Last, First"` is detected and un-reversed deterministically.

## The two-people-in-one-cell (joint name) problem

A single cell can hold two people: `"Robert & Phyllis"`, `"John and Mary Smith"`,
`"Bob/Sue"`. The deterministic spine **does not auto-split** — splitting reliably (who
is the surname owner? who gets which dates?) needs judgement. `parse_name` detects this
and returns `needs_llm=True` with reason `two-people-in-one-cell`; the actual 1→N split
is the LLM / entity-resolve tier's job.

**This must surface, not vanish.** A joint collapse is otherwise *silent* — the row
keeps one collapsed person and the second is lost with no flag. The fix is a first-class
`needs_attention` category: `assemble.py` flags `needs_llm` cells (predicate = the
explicit `cell.needs_llm` flag, not a confidence floor) carrying
column/transform/reason but **no raw value** (PII-safe). `summarize_needs_attention()`
groups them so the structural cases (`parse_name/two-people-in-one-cell`) are visible at
the question round instead of drowning.

*Illustrative (general pattern, not a client fact):* in one flat-contact export, 36% of
the `FIRST_NAME` column held joint names — the gap between source rows and expected
output was entirely this 1→N split, and it was invisible until the category was added.

## Compound given-names over-segment

`"Robert James"` as a first-name cell over-segments into first + middle. This is a
**granularity mismatch, not a bug** — flag it low-confidence rather than treat it as a
correctness failure. Pass-through of a clean already-split `last_name` column should
**win-order** ahead of re-parsing.

## Graduation

If a joint-split heuristic becomes reliable and general, it graduates into the library
(a splitter function + golden test) and this prose shrinks to a pointer.
