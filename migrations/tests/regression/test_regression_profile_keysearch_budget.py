"""Regression — M6: candidate-key search is combinatorial (perf/DoS).

THE BUG: when no single-column unique key exists, ``candidate_keys`` enumerated
``combinations(cols, 2..5)`` over ALL columns, each running a FULL-table groupby. On a
wide table (~40 cols) with no early low-arity unique key the combination count explodes
(C(40,5) ~= 650k) × a full scan per combo — a DoS-grade blowup. Bell's Chapel only
survived because it happens to find a key early.

THE FIX (all of):
  - restrict composite candidates to the top-K highest-cardinality columns;
  - short-circuit combos whose max single-column distinct count can't reach uniqueness;
  - bound the total combos evaluated with an explicit budget, and RECORD truncation
    (``candidate_keys`` is wrapped so the profile output flags TRUNCATED).
  - keep natural-key completion working (still finds the section/row/grave + name key).

This test is DETERMINISTIC: it counts how many ``_is_unique`` evaluations the composite
search performs and asserts the budget is respected (not a wall-clock flake), and that
the search reports truncation on a wide no-early-key table. A generous time bound is also
asserted as a backstop.
"""

from __future__ import annotations

import time

import pandas as pd

import profile as P


def _profiles(df: pd.DataFrame) -> dict:
    n = len(df)
    return {c: P.profile_column(df[c], c, n) for c in df.columns if c not in P._RESERVED_COLS}


def _wide_no_early_key_df(rows: int = 400, cols: int = 40) -> pd.DataFrame:
    """A wide table where every column is HIGH-cardinality but NO low-arity combo is unique.

    Each column repeats every value exactly twice (distinct == rows/2), so:
      - no single column is unique;
      - the distinct-product lower bound does NOT short-circuit any combo (two ~rows/2
        columns multiply well past the row count), so the search must actually SCAN —
        exactly the worst case the budget exists to bound;
      - by construction no pair/triple/etc. up to size 5 is unique (every column's
        duplicate pairs line up on the same rows), so the search cannot finish early and
        must hit the budget → report truncation.
    """
    half = rows // 2
    data = {}
    for c in range(cols):
        # value depends only on (row mod half) with a per-column offset — each value
        # appears on exactly two rows (r and r+half), and the SAME two rows for every
        # column, so no combination of columns ever distinguishes those two rows.
        data[f"c{c:02d}"] = [f"c{c:02d}_v{((r % half) + c) % half}" for r in range(rows)]
    return pd.DataFrame(data)


def test_keysearch_budget_respected_and_truncation_reported():
    df = _wide_no_early_key_df(rows=200, cols=40)
    profiles = _profiles(df)

    # Count groupby/uniqueness evaluations the search makes.
    calls = {"n": 0}
    orig = P._is_unique

    def _counting(d, cols):
        calls["n"] += 1
        return orig(d, cols)

    P._is_unique = _counting
    try:
        t0 = time.monotonic()
        result = P.candidate_keys(df, profiles)
        elapsed = time.monotonic() - t0
    finally:
        P._is_unique = orig

    # Budget: total uniqueness evaluations must stay well under the naive blowup.
    # Naive C(40,2..5) alone is ~700k+; assert we are orders of magnitude below.
    assert calls["n"] <= P._COMPOSITE_KEY_BUDGET + len(df.columns) + 100, (
        f"key search made {calls['n']} evaluations — budget not enforced"
    )

    # Backstop wall-clock bound (generous): must be fast, not minutes.
    assert elapsed < 10.0, f"key search took {elapsed:.1f}s — too slow"

    # No unique key exists here, so the result must report the search was truncated.
    truncation = P.last_keysearch_truncated()
    assert truncation is True, "wide no-early-key search should report truncation"


def test_keysearch_finds_simple_unique_key_quickly():
    """A normal table with a real unique key still finds it (no truncation needed)."""
    rows = 100
    df = pd.DataFrame({
        "id": [f"K{i:04d}" for i in range(rows)],
        "status": ["A" if i % 2 else "B" for i in range(rows)],
        "kind": ["x" if i % 3 else "y" for i in range(rows)],
    })
    profiles = _profiles(df)
    keys = P.candidate_keys(df, profiles)
    unique_single = [k for k in keys if k["unique"] and k["columns"] == ["id"]]
    assert unique_single, f"single-column unique key not found: {keys}"


def test_keysearch_completes_natural_business_key_under_budget():
    """A section/row/grave + name natural key must still surface (M6 must not break it).

    The locator (section,row,grave) is near-unique (a few graves hold 2 people) and is
    completed to uniqueness with the name columns — exactly the Bell's Chapel shape. No
    small column subset is unique on its own, so the completion path must fire.
    """
    # Mirror the Bell's Chapel shape: (section,row,grave) is a near-unique locator (a few
    # graves hold 2 people), completed to uniqueness by the name parts. The only other
    # accidental unique keys involve a derived measurement (coordinate) — a POOR key — so
    # the completed business key (locator + names) is the natural one.
    rows_section = list("ABCDE")
    records = []
    surnames = [f"Sur{i:02d}" for i in range(10)]
    firsts = [f"First{i:02d}" for i in range(10)]
    idx = 0
    for sec in rows_section:
        for r in range(8):
            for g in range(6):
                # two occupants share a few graves to make the locator near- (not fully) unique
                occupants = 2 if (g == 0) else 1
                for _occ in range(occupants):
                    records.append({
                        "section": sec,
                        "row": str(r),
                        "grave": str(g),
                        "sur_name": surnames[idx % len(surnames)],
                        "first_name": firsts[(idx // len(surnames)) % len(firsts)],
                        # derived measurement (poor key, but high-cardinality) — per row
                        "latitude": f"{40.0 + idx * 1e-4:.6f}",
                        "longitude": f"{-74.0 - idx * 1e-4:.6f}",
                    })
                    idx += 1
    df = pd.DataFrame(records)
    profiles = _profiles(df)

    keys = P.candidate_keys(df, profiles)
    unique = [k for k in keys if k["unique"]]
    assert unique, f"no unique key found for natural-key table: {keys}"
    # At least one unique key must be the completed business key: locator + name parts.
    has_name_key = any(
        {"sur_name", "first_name"} <= set(k["columns"])
        and {"section", "row", "grave"} & set(k["columns"])
        for k in unique
    )
    assert has_name_key, f"natural business key (section/row/grave+name) not surfaced: {unique}"
