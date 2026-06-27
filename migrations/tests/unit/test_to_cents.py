"""Golden unit tests for the ``to_cents`` cleansing primitive (LIBRARY.md 7b).

Money → integer cents, EXACT via Decimal (never float). Currency symbols and
parentheses-negatives handled. Non-numeric free text → ``needs_llm`` (extract, never
LLM-arithmetic). ``digits_only`` is trivial and never routes; ``to_cents`` does.
"""

import to_cents


def test_currency_symbol_and_thousands_separator_to_exact_cents():
    cell = to_cents.clean("$1,200.00")
    assert cell.value == 120000
    assert isinstance(cell.value, int)
    assert cell.confidence == 0.99
    assert cell.needs_llm is False


def test_parentheses_negative_is_negative_cents():
    cell = to_cents.clean("(1,200.00)")
    assert cell.value == -120000
    assert cell.needs_llm is False


def test_leading_minus_is_negative_cents():
    assert to_cents.clean("-50").value == -5000


def test_decimal_precision_is_exact_not_float():
    # 1234.5 dollars → 123450 cents, exact (a float path could drift).
    assert to_cents.clean("1234.5").value == 123450
    # Classic float-error value: 19.99 → 1999, never 1998.
    assert to_cents.clean("$19.99").value == 1999


def test_half_cent_rounds_half_up():
    # 0.005 dollars → 0.5 cents → ROUND_HALF_UP → 1 cent.
    assert to_cents.clean("0.005").value == 1


def test_non_numeric_free_text_routes_to_llm_to_extract():
    cell = to_cents.clean("paid in full")
    assert cell.value is None
    assert cell.needs_llm is True
    assert cell.meta.get("reason") == "non-numeric"


def test_empty_input_is_confident_empty_and_never_routes():
    cell = to_cents.clean("")
    assert cell.value is None
    assert cell.confidence == 1.0
    assert cell.needs_llm is False
