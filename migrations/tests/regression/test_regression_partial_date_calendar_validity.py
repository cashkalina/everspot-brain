"""Regression — LESSONS.md #4: partial dates violated calendar + contract validity.

THE BUG: ``assemble`` composed dates from split Y/M/D source columns without checking
calendar validity, producing impossible dates (Feb-29 in a non-leap year, Apr-31) and
orphan days with no month — all of which the server's ``PartialDate`` cast rejects.

THE FIX: ``assemble._compose_partial_date`` enforces calendar validity (drop the
offending day to null + report it) AND the "day requires month" contract (orphan day →
null). Genuinely out-of-range parts (a year leaked into the month column) → null + a
``data_quality`` report.

A reversion fails these: an impossible day would survive instead of being dropped.
"""

from assemble import _compose_partial_date


def test_regression_partial_date_calendar_validity_feb_29_non_leap_drops_day():
    partial, out_of_range = _compose_partial_date({"year": 1981, "month": 2, "day": 29})
    assert partial == {"year": 1981, "month": 2, "day": None, "estimated": True}
    assert "day" in out_of_range


def test_feb_29_leap_year_is_kept():
    partial, out_of_range = _compose_partial_date({"year": 1980, "month": 2, "day": 29})
    assert partial == {"year": 1980, "month": 2, "day": 29, "estimated": False}
    assert out_of_range == []


def test_apr_31_drops_day():
    partial, out_of_range = _compose_partial_date({"year": 2000, "month": 4, "day": 31})
    assert partial["day"] is None
    assert partial["month"] == 4
    assert "day" in out_of_range


def test_orphan_day_without_month_is_dropped():
    # Day requires month (PartialDate contract): a day with no month → null, no anomaly.
    partial, out_of_range = _compose_partial_date({"year": 1981, "month": None, "day": 12})
    assert partial == {"year": 1981, "month": None, "day": None, "estimated": True}
    # An orphan day is "incomplete", not "out of range" → it is dropped, not reported.
    assert out_of_range == []


def test_year_leaked_into_month_column_is_out_of_range_and_dropped():
    partial, out_of_range = _compose_partial_date({"year": None, "month": 1981, "day": None})
    # Month 1981 is impossible → dropped to null + reported.
    assert "month" in out_of_range
    # Nothing survives → null partial date.
    assert partial is None


def test_zero_placeholders_are_benign_unknowns_no_flag():
    partial, out_of_range = _compose_partial_date({"year": 1923, "month": 0, "day": 0})
    assert partial == {"year": 1923, "month": None, "day": None, "estimated": True}
    assert out_of_range == []


def test_complete_valid_date_is_not_estimated():
    partial, out_of_range = _compose_partial_date({"year": 1981, "month": 11, "day": 2})
    assert partial == {"year": 1981, "month": 11, "day": 2, "estimated": False}
    assert out_of_range == []
