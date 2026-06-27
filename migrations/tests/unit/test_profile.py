"""Unit tests (SPEC §12) — the runnable `profile` stage (§8 stage 3).

Asserts per-column stats, candidate-key detection (single + composite), value-set
candidate detection, and data-shape signal tagging on a SMALL SYNTHETIC table — no
client data, no network, no LLM.
"""

import pandas as pd
import pytest

import profile as P


@pytest.fixture
def synth_df() -> pd.DataFrame:
    # A synthetic register of 10 rows. section/row/grave is a NEAR-unique locator: the two
    # double-occupancy graves (A/1/1) collide, so no single column nor the locator alone is
    # unique — disambiguation needs a name column → a composite natural key. `id` IS a
    # single-column key. Names repeat (SMITH x2) so name columns are not single keys.
    n = 10
    return pd.DataFrame(
        {
            "id": [str(i) for i in range(1, n + 1)],
            "section": ["A", "A", "B", "B", "C", "C", "A", "B", "C", "A"],
            "row":     ["1", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
            "grave":   ["1", "1", "5", "9", "2", "3", "7", "8", "4", "6"],
            "sur_name": ["SMITH", "SMITH", "DOE", "JONES", "DOE", "BROWN", "LEE", "LEE", "KING", "FOX"],
            # Names repeat (John x2, Bob x2) so NO single name column is a key — the
            # natural key genuinely needs the locator + BOTH name columns.
            "first_name": ["John", "Jane", "Bob", "Amy", "Bob", "Ray", "John", "Mia", "Lou", "Pat"],
            "status":  ["active", "active", "inactive", "active", "active", "inactive",
                        "active", "active", "inactive", "active"],
            "phone":   ["(205) 555-1212", "205-555-3434", "2055559090", "205.555.0001",
                        "205-555-7777", "(205)555-8888", "2055551111", "205.555.2222",
                        "205-555-3333", "205 555 4444"],
            "price":   ["$1,200.00", "$950.00", "$2,000.00", "$500.00", "$1,000.00",
                        "$750.00", "$1,500.00", "$2,250.00", "$300.00", "$1,100.00"],
            "born":    ["1/2/1923", "3/4/45", "12/31/1980", "6/6/1990", "5/5/55",
                        "7/7/1977", "8/8/88", "9/9/1999", "1/1/2001", "2/2/1962"],
            "owner_pair": ["John & Jane", "Bob and Sue", "Amy", "Tom & Lee", "Sue",
                           "Ray", "Ed & Lou", "Mia", "Lou", "Pat & Sam"],
            "blank_col": ["", "  ", "", "", "", "", "", "", "", ""],
        }
    )


def test_column_stats_counts_and_dtype(synth_df):
    tp = P.profile_table(synth_df, "reg")
    cols = tp.columns
    assert tp.row_count == 10
    assert cols["id"].dtype == "integer"
    assert cols["price"].dtype == "money"
    assert cols["section"].non_null == 10
    assert cols["section"].distinct == 3  # A, B, C
    # blank/whitespace-only cells are counted as blank, not non-null.
    assert cols["blank_col"].non_null == 0
    assert cols["blank_col"].blank == 10


def test_sample_is_capped_pii_aware(synth_df):
    tp = P.profile_table(synth_df, "reg")
    # The sample never exceeds the cap (PII-aware — no whole-column dumps).
    for cp in tp.columns.values():
        assert len(cp.sample) <= P._SAMPLE_CAP


def test_single_column_candidate_key(synth_df):
    tp = P.profile_table(synth_df, "reg")
    single = [k for k in tp.candidate_keys if k["columns"] == ["id"]]
    assert single and single[0]["unique"] is True
    assert single[0]["uniqueness_ratio"] == 1.0


def test_composite_natural_key_surfaced(synth_df):
    tp = P.profile_table(synth_df, "reg")
    locator = {"section", "row", "grave"}
    name_cols = {"sur_name", "first_name"}
    # A composite natural key combining a LOCATOR column with a NAME column is surfaced
    # and unique — the locator alone is near-unique (double-occupancy collision) so a name
    # column completes it. (This is the section/row/grave + name pattern, generalized.)
    composite_unique = [
        set(k["columns"])
        for k in tp.candidate_keys
        if k["unique"] and len(k["columns"]) >= 2 and (set(k["columns"]) & locator)
    ]
    assert any((s & locator) and (s & name_cols) for s in composite_unique)


def test_locator_alone_is_not_unique(synth_df):
    """The section/row/grave locator is near-unique (collision), not a standalone key."""
    unique, ratio = P._is_unique(synth_df, ["section", "row", "grave"])
    assert unique is False
    assert ratio >= 0.85


def test_value_set_candidates(synth_df):
    tp = P.profile_table(synth_df, "reg")
    # status is low-cardinality → a value-set candidate with a value→frequency map.
    assert "status" in tp.value_sets
    assert tp.value_sets["status"]["values"]["active"] == 7
    # A high-cardinality / unique column is NOT a value-set candidate.
    assert "id" not in tp.value_sets


def test_data_shape_signals(synth_df):
    tp = P.profile_table(synth_df, "reg")
    sig = tp.to_dict()["signals"]
    assert "phone" in sig and "phone" in sig["phone"]
    assert "money" in sig and "price" in sig["money"]
    assert "name" in sig and "sur_name" in sig["name"]
    assert "joint_name" in sig and "owner_pair" in sig["joint_name"]
    assert "two_digit_year" in sig and "born" in sig["two_digit_year"]


def test_bare_integer_is_not_money(synth_df):
    """Regression: a column of bare small integers (grave numbers) is integer, not money."""
    tp = P.profile_table(synth_df, "reg")
    assert tp.columns["grave"].dtype == "integer"
    assert "money" not in tp.columns["grave"].signals
