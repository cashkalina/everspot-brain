# topics/partial-dates.md

> **triggers:** `dates`, `dob-dod`, `partial-dates`, `split-ymd-columns` · stages: cleanse, assemble

Loaded when the profile shows date columns — especially DOB/DOD/DOI, year-only or
month-only values, or dates pre-split into separate Y/M/D columns.

## The model

Everspot stores `dob`/`dod`/`doi` (interment) and `dob` (customer) as
`_year/_month/_day/_estimated` columns via `PartialDateCast`. The canonical artifact
carries them as partial-date objects `{year, month, day, estimated}` — **any part may be
null** (cemetery records are frequently year- or month-only).

## The library

`scripts/normalize_date.py` (`dateutil`) → a partial-date cell. It also flags:
- `"circa 1923"` / `"c. 1923"` / `"abt 1923"` → `estimated=true`, needs_llm review of the qualifier;
- ambiguous DD/MM vs MM/DD when both ≤ 12 → needs_llm;
- **2-digit years** (century ambiguity) → low confidence / needs_llm;
- free text it can't parse → needs_llm.

## Two hard validity rules (server's `PartialDate` rejects violations)

`assemble._compose_partial_date` enforces both — do not bypass:

1. **Calendar validity** — no Feb-29 in a non-leap year, no Apr-31, etc. → **drop the offending day** (keep year + month).
2. **"day requires month"** — an orphan day with no month → **null the day**.

A `0`/blank component composes silently to null; a genuinely out-of-range value composes
to null **and** raises a `data_quality` flag (e.g. a year value that leaked into a
"Death Month" column).

## interment.date NOT-NULL sentinel

`interments.date` is NOT NULL. When no real date is known, compose from dod → doi → dob,
else use the **flagged sentinel `1900-01-01`**. The flag is what lets the report and the
user find these later. (Making the column nullable is an open Orion-ergonomics item.)

## Graduation

The calendar + "day requires month" rules have already **graduated into the assembler**
(`_compose_partial_date`) and the regression suite — this prose is the explainer; the
code is the source of truth.
