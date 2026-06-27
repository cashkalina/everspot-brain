"""Golden unit tests for the ``digits_only`` cleansing primitive (LIBRARY.md 7b).

Trivial deterministic normalizer for ID-like fields. ALWAYS confident; the
contract guarantee is that it NEVER routes to the LLM tier.
"""

import digits_only


def test_strips_all_non_digits():
    cell = digits_only.clean("abc123-456")
    assert cell.value == "123456"
    assert cell.confidence == 1.0
    assert cell.needs_llm is False
    assert cell.method == "digits_only"


def test_never_routes_to_llm_even_for_garbage():
    # A value with no digits is empty, but STILL never needs_llm — that is the
    # invariant this primitive guarantees (LIBRARY.md: "never routes to the LLM").
    cell = digits_only.clean("hello world")
    assert cell.value is None
    assert cell.needs_llm is False


def test_empty_input_is_confident_empty_and_never_routes():
    cell = digits_only.clean("")
    assert cell.value is None
    assert cell.confidence == 1.0
    assert cell.needs_llm is False
