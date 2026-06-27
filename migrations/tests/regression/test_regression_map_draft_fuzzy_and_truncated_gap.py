"""Regression (L6): map_draft must not settle fuzzy / truncated value-sets at 1.0.

SPEC §8 stage 5 + §9.2 — a value-set draft may only settle (record a confident
default, no gap) when EVERY distinct source code resolved to a REAL tenant
list_option id by an EXACT match AND the profiler saw the WHOLE value set:

  (a) FUZZY-ONLY RESOLUTION. ``resolve_list_option`` returns confidence tiers:
      exact → 1.0, fuzzy ≥90 → <1.0 (with a ``fuzzy`` provenance flag), weak/unknown
      → missing. A value that resolved ONLY via a non-exact (fuzzy ≥90) match is a
      candidate, not a certainty — the draft must stay ``is_gap=True`` and carry a
      confidence < 1.0 so the human confirms it, rather than silently settling.

  (b) PROFILER-TRUNCATED VALUE SET. The profiler caps the value→freq map and marks
      the candidate ``truncated`` when ``distinct`` exceeds the cap. Codes beyond the
      cap were NEVER seen, so the mapping cannot claim completeness — a gap must be
      emitted even when every SEEN code resolved exactly.

Driven entirely off profile signals + the resolve_list_option result — no client
column names. Synthetic data only; ``draft_table`` is exercised directly.
"""

from __future__ import annotations

import map_draft

# A tenant list_option set whose names are slightly off from the source codes so a
# fuzzy (≥90) match is needed, plus an exact one for the control.
_REFERENCE_DATA = {
    "list_options": {
        "interment_type": [
            {"id": 11, "name": "Burial", "key": "interment-type-burial"},
            {"id": 12, "name": "Cremation", "key": "interment-type-cremation"},
        ]
    }
}


def _table_profile(values: dict[str, int], *, truncated: bool, distinct: int | None = None):
    """A minimal flat-register profile with a single coded value-set column ``itype``.

    A locator + name + date shape so entity routing yields interment as a secondary
    entity (the carrier of ``interment_type_id``), exactly like a real burial register
    — but the column itself is a generic ``itype`` code, no client names.
    """
    distinct = distinct if distinct is not None else len(values)
    return {
        "columns": {
            "section": {"non_null": 5, "distinct": 3, "signals": []},
            "lot": {"non_null": 5, "distinct": 5, "signals": []},
            "space": {"non_null": 5, "distinct": 5, "signals": []},
            "last": {"non_null": 5, "distinct": 5, "signals": ["name"]},
            "death_year": {"non_null": 5, "distinct": 4, "signals": ["date"]},
            "itype": {"non_null": 5, "distinct": distinct, "signals": []},
        },
        "signals": ["name", "date"],
        "value_set_candidates": {
            "itype": {"distinct": distinct, "values": values, "truncated": truncated},
        },
        "candidate_keys": [],
    }


def _itype_draft(td):
    return next(c for c in td.columns if c.source == "itype")


def test_fuzzy_only_resolution_stays_a_gap_not_confidence_one():
    # "Burials" / "Cremations" only fuzzy-match the singular tenant names → ≥90, not exact.
    profile = _table_profile({"Burials": 3, "Cremations": 2}, truncated=False)
    td = map_draft.draft_table("register", profile, _REFERENCE_DATA, source_key=["section"])

    draft = _itype_draft(td)
    assert draft.action == "value_map"
    # Every code resolved (no genuinely-missing code) ...
    vs = next(v for v in td.value_sets if v.column == "itype")
    assert vs.missing == [], f"expected fuzzy resolution of all codes, got missing={vs.missing}"
    assert set(vs.resolved.values()) == {11, 12}
    # ... but a fuzzy hit is not a certainty: it must remain a gap, NOT settle at 1.0.
    assert draft.is_gap is True, "a fuzzy-only value-set resolution must surface as a gap"
    assert draft.gap_kind == "value_set"
    assert draft.confidence < 1.0, "fuzzy resolution must not record full confidence"


def test_exact_resolution_settles_confidently():
    # Control: exact names settle (no gap, full confidence) — the fix must not over-fire.
    profile = _table_profile({"Burial": 3, "Cremation": 2}, truncated=False)
    td = map_draft.draft_table("register", profile, _REFERENCE_DATA, source_key=["section"])

    draft = _itype_draft(td)
    assert draft.is_gap is False, "an all-exact value-set must settle confidently"
    assert draft.confidence == 1.0


def test_profiler_truncated_value_set_emits_a_gap():
    # Every SEEN code resolves exactly, but the profiler truncated the value set:
    # codes beyond the cap were never seen → cannot claim completeness → gap.
    profile = _table_profile(
        {"Burial": 3, "Cremation": 2}, truncated=True, distinct=120
    )
    td = map_draft.draft_table("register", profile, _REFERENCE_DATA, source_key=["section"])

    draft = _itype_draft(td)
    vs = next(v for v in td.value_sets if v.column == "itype")
    assert vs.missing == [], "the seen codes all resolved exactly"
    assert draft.is_gap is True, "a truncated value set must surface as a gap (incomplete)"
    assert draft.gap_kind == "value_set"
