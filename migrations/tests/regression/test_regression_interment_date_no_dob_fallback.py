"""Regression — M3: interment.date must never use the decedent's BIRTHDAY, and is required.

THE ORIGINAL M3 BUG: ``_required_date`` walked ``("doi","dod","dob")``, so an interment
with only a date-of-birth got the decedent's BIRTHDAY stamped as the burial date.

THE RULE (ck decision): ``interments.date`` is a required (NOT NULL) operational column.
The loader composes it from ``doi`` (date of interment) or ``dod`` (date of death) when
present, else defaults to **Jan 1 of the current year** — never the birthday, never null,
never the old ``1900-01-01`` sentinel. The semantic date of interment lives in ``doi``,
which stays null when truly unknown; only the operational ``date`` column gets the default.
"""

from datetime import datetime, timezone

import orion_load


def _rec(**dates):
    return {"external_id": "src:interment:1", **dates}


def _jan1_current_year() -> str:
    return f"{datetime.now(timezone.utc).year:04d}-01-01"


def test_dob_only_interment_defaults_to_jan1_not_birthday():
    rec = _rec(dob={"year": 1950, "month": 6, "day": 15})
    date_str = orion_load._interment_date(rec)

    assert date_str == _jan1_current_year(), "dob-only interment must default to Jan 1 current year"
    assert date_str != "1950-06-15", "must NOT use the birthday"
    assert date_str != "1900-01-01", "the old sentinel must be gone"
    assert not hasattr(orion_load, "_DEFAULT_DATE"), "the 1900-01-01 sentinel must be removed"


def test_no_date_at_all_defaults_to_jan1():
    assert orion_load._interment_date(_rec()) == _jan1_current_year()


def test_doi_still_wins():
    rec = _rec(doi={"year": 2001, "month": 2, "day": 3},
               dod={"year": 2000, "month": 1, "day": 1},
               dob={"year": 1950, "month": 6, "day": 15})
    assert orion_load._interment_date(rec) == "2001-02-03"


def test_dod_used_when_no_doi():
    rec = _rec(dod={"year": 2000, "month": 1, "day": 1},
               dob={"year": 1950, "month": 6, "day": 15})
    assert orion_load._interment_date(rec) == "2000-01-01"


def test_has_source_interment_date_predicate():
    assert orion_load._has_source_interment_date(_rec(doi={"year": 2001})) is True
    assert orion_load._has_source_interment_date(_rec(dod={"year": 2000})) is True
    assert orion_load._has_source_interment_date(_rec(dob={"year": 1950, "month": 6, "day": 15})) is False
    assert orion_load._has_source_interment_date(_rec()) is False


def test_project_payload_defaults_date_for_dateless_interment():
    rec = _rec(dob={"year": 1950, "month": 6, "day": 15},
               deceased_ref="src:customer:1")
    payload = orion_load.project_payload(
        "interment", rec,
        cemetery_id=1, property_type_id=7, resolve_ref=lambda r: None,
    )
    assert payload["date"] == _jan1_current_year(), "a dateless interment must default date to Jan 1 (never null)"
