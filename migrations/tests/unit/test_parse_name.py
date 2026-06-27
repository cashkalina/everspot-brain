"""Golden unit tests for the ``parse_name`` cleansing primitive (LIBRARY.md 7b).

Captures the PROVEN current behavior of ``parse_name.clean`` as golden:
happy path, reversed "Last, First", the two-people-in-one-cell ``needs_llm`` route
(the safety property behind regression #7), single-token ambiguity, and empties.
"""

import parse_name
from cellcontract import Cell


def test_full_name_reversed_last_first_unreverses_with_suffix():
    cell = parse_name.clean("Smith, John A Jr")
    assert cell.value == {
        "title": None, "first": "John", "middle": "A",
        "last": "Smith", "suffix": "Jr", "nickname": None,
    }
    assert cell.confidence == 0.95
    assert cell.method == "nameparser"
    assert cell.needs_llm is False
    assert cell.meta.get("reversed_input") is True


def test_simple_first_last_is_confident():
    cell = parse_name.clean("John Smith")
    assert cell.value["first"] == "John"
    assert cell.value["last"] == "Smith"
    assert cell.needs_llm is False
    assert cell.confidence == 0.95


def test_two_people_in_one_cell_ampersand_routes_to_llm():
    cell = parse_name.clean("Robert & Phyllis")
    assert cell.needs_llm is True
    assert cell.value == {"raw": "Robert & Phyllis"}
    assert cell.meta.get("reason") == "two-people-in-one-cell"
    assert cell.meta.get("two_people") is True
    assert cell.confidence < 0.8


def test_two_people_in_one_cell_word_and_routes_to_llm():
    cell = parse_name.clean("John and Mary Smith")
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "two-people-in-one-cell"


def test_single_token_name_is_ambiguous_and_routes_to_llm():
    cell = parse_name.clean("Madonna")
    assert cell.value["first"] == "Madonna"
    assert cell.value["last"] is None
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "ambiguous-structure"


def test_empty_input_is_confident_empty_and_never_routes():
    cell = parse_name.clean("")
    assert isinstance(cell, Cell)
    assert cell.value is None
    assert cell.confidence == 1.0
    assert cell.needs_llm is False


def test_none_and_nan_treated_as_empty():
    assert parse_name.clean(None).value is None
    assert parse_name.clean(float("nan")).value is None
