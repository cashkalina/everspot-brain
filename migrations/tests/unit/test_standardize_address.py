"""Golden unit tests for the ``standardize_address`` primitive (LIBRARY.md 7b).

Freeform US address → {line_one,line_two,city,state,zip}. Ambiguous / garbage /
plot-bleed → ``needs_llm``; the parse is NEVER silently dropped.

NOTE on the install matrix: ``usaddress`` is an OPTIONAL dependency (not in the
SPEC §18 base install list). These tests therefore assert the *contract guarantees*
that hold in BOTH states rather than the exact tag output (which only exists when
usaddress is installed):

  - an empty cell → confident-empty, never routes;
  - any non-empty cell that cannot be confidently parsed → ``needs_llm`` with the
    best-effort value preserved (so the LLM tier has a prior).

When usaddress IS installed, the additional ``test_clean_address_*`` assertions
exercise the real tag path; they self-skip otherwise so the suite stays green
offline on the base install.
"""

import pytest

import standardize_address as addr

_HAS_USADDRESS = getattr(addr, "usaddress", None) is not None


def test_empty_input_is_confident_empty_and_never_routes():
    cell = addr.clean("")
    assert cell.value is None
    assert cell.confidence == 1.0
    assert cell.needs_llm is False


def test_none_is_confident_empty():
    assert addr.clean(None).value is None


def test_garbage_routes_to_llm_and_keeps_a_prior():
    cell = addr.clean("???")
    assert cell.needs_llm is True
    # Best-effort value preserved (never silently dropped).
    assert cell.value is not None


def test_plot_designation_in_address_routes_to_llm():
    cell = addr.clean("Section 5 Lot 2 Grave 3")
    assert cell.needs_llm is True


@pytest.mark.skipif(not _HAS_USADDRESS, reason="usaddress (optional dep) not installed")
def test_clean_us_address_resolves_components_when_usaddress_present():
    cell = addr.clean("123 Main St, Springfield, IL 62704")
    assert cell.value["line_one"] is not None
    assert cell.value["state"] == "IL"
    assert cell.value["zip"] == "62704"
    assert cell.needs_llm is False


@pytest.mark.skipif(not _HAS_USADDRESS, reason="usaddress (optional dep) not installed")
def test_missing_components_route_to_llm_when_usaddress_present():
    cell = addr.clean("Main Street")  # no number, no city/state/zip
    assert cell.needs_llm is True
