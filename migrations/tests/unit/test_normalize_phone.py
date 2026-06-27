"""Golden unit tests for the ``normalize_phone`` cleansing primitive (LIBRARY.md 7b).

Phones normalize to digits-only (E.164-ish). Multi-number / junk → ``needs_llm``.
"""

import normalize_phone


def test_valid_us_number_is_digits_only_and_confident():
    cell = normalize_phone.clean("(415) 555-1234")
    assert cell.value == "14155551234"
    assert cell.confidence == 0.98
    assert cell.needs_llm is False
    assert cell.method == "phonenumbers"


def test_multi_number_with_or_routes_to_llm():
    cell = normalize_phone.clean("415-555-1234 or 415-555-9999")
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "multi-number-or-extension"


def test_extension_routes_to_llm():
    cell = normalize_phone.clean("415-555-1234 ext 5")
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "multi-number-or-extension"


def test_unparseable_junk_routes_to_llm():
    cell = normalize_phone.clean("call me later")
    assert cell.needs_llm is True
    assert cell.value is None
    assert cell.meta.get("reason") == "unparseable"


def test_short_invalid_number_routes_to_llm():
    cell = normalize_phone.clean("555-1234")
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "invalid-number"


def test_empty_input_is_confident_empty_and_never_routes():
    cell = normalize_phone.clean("")
    assert cell.value is None
    assert cell.confidence == 1.0
    assert cell.needs_llm is False
