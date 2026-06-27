"""Regression — M3 / C3: interment.date must NEVER be fabricated.

THE ORIGINAL M3 BUG: ``_required_date`` walked ``("doi","dod","dob")``, so an interment
with only a date-of-birth got the decedent's BIRTHDAY stamped as the burial date.

THE M3 FIX: drop ``dob`` from the chain — use doi/dod only.

THE C3 CHANGE (new user decision): a date is NEVER fabricated. ``interments.date`` is now
NULLABLE, so the composer returns the real doi/dod when available, else ``None`` — the
old ``1900-01-01`` sentinel is gone. A dob-only interment must therefore yield ``None``
(NOT the birthday, NOT a sentinel); a record with no usable date yields ``None``; and a
real doi/dod still composes the actual date.
"""

import orion_load


def _rec(**dates):
    return {"external_id": "src:interment:1", **dates}


def test_dob_only_interment_yields_null_not_birthday_and_not_sentinel():
    rec = _rec(dob={"year": 1950, "month": 6, "day": 15})
    date_str = orion_load._interment_date(rec)

    assert date_str is None, "dob-only interment must yield null, not a date"
    assert date_str != "1950-06-15", "must NOT use the birthday"
    # The sentinel is gone entirely.
    assert not hasattr(orion_load, "_DEFAULT_DATE"), "the 1900-01-01 sentinel must be removed"


def test_no_date_at_all_yields_null():
    date_str = orion_load._interment_date(_rec())
    assert date_str is None


def test_doi_still_wins():
    rec = _rec(doi={"year": 2001, "month": 2, "day": 3},
               dod={"year": 2000, "month": 1, "day": 1},
               dob={"year": 1950, "month": 6, "day": 15})
    assert orion_load._interment_date(rec) == "2001-02-03"


def test_dod_used_when_no_doi():
    rec = _rec(dod={"year": 2000, "month": 1, "day": 1},
               dob={"year": 1950, "month": 6, "day": 15})
    assert orion_load._interment_date(rec) == "2000-01-01"


def test_project_payload_sends_null_date_for_dateless_interment():
    rec = _rec(dob={"year": 1950, "month": 6, "day": 15},
               deceased_ref="src:customer:1")
    payload = orion_load.project_payload(
        "interment", rec,
        cemetery_id=1, property_type_id=7, resolve_ref=lambda r: None,
    )
    assert payload["date"] is None, "a dateless interment must send date: null (not a sentinel)"
