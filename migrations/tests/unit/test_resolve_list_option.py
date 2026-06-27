"""Golden unit tests for the ``resolve_list_option`` primitive (LIBRARY.md 7b).

Resolves a raw code/label to a REAL tenant list_option id from the Wave-0 snapshot.
Exact → confident; strong fuzzy (≥90) → resolved; unknown → ``needs_llm`` (a
value-set question). It NEVER invents an id.
"""

import resolve_list_option as rlo


def _options():
    return rlo.build_options([
        {"id": 4412, "key": "jr", "name": "Jr."},
        {"id": 4413, "key": "sr", "name": "Sr."},
        {"id": 11, "key": "burial", "name": "Burial"},
    ])


def test_exact_key_match_is_full_confidence():
    cell = rlo.clean("jr", _options())
    assert cell.value == 4412
    assert cell.confidence == 1.0
    assert cell.needs_llm is False


def test_exact_name_match_case_insensitive():
    cell = rlo.clean("Jr.", _options())
    assert cell.value == 4412
    assert cell.needs_llm is False


def test_strong_fuzzy_match_resolves_to_id():
    cell = rlo.clean("buriall", _options())  # typo of "burial"
    assert cell.value == 11
    assert cell.needs_llm is False
    assert cell.confidence >= 0.90
    assert cell.meta.get("fuzzy") is True


def test_unknown_code_routes_to_llm_and_never_invents_an_id():
    cell = rlo.clean("xyzzy", _options())
    assert cell.value is None
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "unknown-code"


def test_weak_label_without_a_close_match_routes_to_llm():
    # "Junior" is not close enough to "jr"/"Jr." on WRatio to clear the floor.
    cell = rlo.clean("Junior", _options())
    assert cell.needs_llm is True
    assert cell.value is None


def test_empty_input_is_confident_empty_and_never_routes():
    cell = rlo.clean("", _options())
    assert cell.value is None
    assert cell.confidence == 1.0
    assert cell.needs_llm is False


def test_no_options_unknown_routes_to_llm():
    cell = rlo.clean("anything", [])
    assert cell.value is None
    assert cell.needs_llm is True
