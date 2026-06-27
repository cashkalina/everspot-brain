"""Golden unit tests for the ``normalize_date`` cleansing primitive (LIBRARY.md 7b).

Captures the partial-date output {year,month,day,estimated} and every documented
LLM-fallback route: circa/estimated, DD-MM ambiguity, 2-digit-year century
ambiguity, and unparseable free text.
"""

import normalize_date


def test_year_only_is_confident_partial_date():
    cell = normalize_date.clean("1923")
    assert cell.value == {"year": 1923, "month": None, "day": None, "estimated": False}
    assert cell.confidence == 0.97
    assert cell.needs_llm is False


def test_year_month_only_is_confident_partial_date():
    cell = normalize_date.clean("2003-04")
    assert cell.value == {"year": 2003, "month": 4, "day": None, "estimated": False}
    assert cell.needs_llm is False


def test_full_unambiguous_date_is_confident():
    # day=13 > 12 → order is unambiguous (must be DD/MM... no: MM>12 impossible, so MDY)
    cell = normalize_date.clean("13/01/1990")
    assert cell.value == {"year": 1990, "month": 1, "day": 13, "estimated": False}
    assert cell.needs_llm is False
    assert cell.confidence == 0.95


def test_circa_qualifier_marks_estimated_and_routes_to_llm():
    cell = normalize_date.clean("circa 1923")
    assert cell.value == {"year": 1923, "month": None, "day": None, "estimated": True}
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "circa-qualifier"


def test_ambiguous_dd_mm_both_le_12_routes_to_llm():
    cell = normalize_date.clean("05/06/1981")
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "ambiguous-dd-mm"
    assert cell.meta.get("ambiguous_components") == [5, 6]


def test_two_digit_year_century_ambiguity_routes_to_llm():
    cell = normalize_date.clean("3/25/81")  # day 25 → unambiguous order, but 2-digit year
    assert cell.value == {"year": 1981, "month": 3, "day": 25, "estimated": False}
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "2-digit-year"
    assert cell.confidence == 0.55


def test_unparseable_free_text_routes_to_llm_with_null_value():
    cell = normalize_date.clean("sometime in the spring")
    assert cell.value == {"year": None, "month": None, "day": None, "estimated": False}
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "unparseable-free-text"


def test_empty_input_is_confident_empty_and_never_routes():
    cell = normalize_date.clean("")
    assert cell.value is None
    assert cell.confidence == 1.0
    assert cell.needs_llm is False
