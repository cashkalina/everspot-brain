"""Tests (SPEC §12) — field-level (VALUE) post-load reconcile (§8 stage 12, §15.3 lens 4).

`migrate reconcile --live` now proves not only that records are PRESENT live (count
conservation by external_id) but that their VALUES match. Each canonical record is
projected the SAME way the loader writes it (``orion_load.project_payload``, the oracle)
and diffed field-by-field against the live row; property location custom fields are
compared against live attribute-values. These tests drive ``reconcile.reconcile_live``
against a FAKE OrionClient whose ``paginate`` returns crafted live rows, and assert:

  * a CLEAN case (live matches the canonical projection) → 0 mismatches;
  * a MISMATCH case (a wrong interment_type_id, a partial-date day off, a truncated name,
    a wrong location attribute) → each mismatch is detected, attributed to the right
    field, counted in the per-field tally, present in the sample, and the run stays
    WARN (count conservation still PASSES — value drift never blocks);
  * a MISSING-LIVE case (a canonical record absent live) → counted as
    records_missing_live (the count lens, unchanged);
  * report.py renders the field_level block.

No client data, no network, no LLM.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

GOLDEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GOLDEN))

import reconcile as reconcile_mod  # noqa: E402
import report as report_mod  # noqa: E402

_PROPERTY_MT = "Modules\\Property\\Models\\Property"
_GROUP_MT = "Modules\\Property\\Models\\PropertyGroup"
_CUSTOMER_MT = "Modules\\Customer\\Models\\Customer"
_INTERMENT_MT = "Modules\\Interment\\Models\\Interment"


# --------------------------------------------------------------------------- #
# Crafted canonical set + the matching "live" tenant (the oracle baseline)     #
# --------------------------------------------------------------------------- #
def _canonical() -> dict[str, list[dict]]:
    return {
        "property_group": [{
            "external_id": "src:property_group:G1", "name": "Sec A",
            "cemetery_ref": "src:cemetery:default",
            "_provenance": {"table": "t", "row": 1, "source_id": "g1"}, "_confidence": 1.0,
        }],
        "property": [{
            "external_id": "src:property:P1", "property_group_ref": "src:property_group:G1",
            "cemetery_ref": "src:cemetery:default", "section": "A", "lot": "1", "space": "46",
            "_provenance": {"table": "t", "row": 1, "source_id": "p1"}, "_confidence": 1.0,
        }],
        "customer": [{
            "external_id": "src:customer:C1", "status": "customer",
            "first_name": "JOHN", "last_name": "SMITH",
            "_provenance": {"table": "t", "row": 1, "source_id": "c1"}, "_confidence": 1.0,
        }],
        "interment": [{
            "external_id": "src:interment:I1", "status": "completed",
            "deceased_ref": "src:customer:C1", "property_ref": "src:property:P1",
            "interment_type_id": 11,
            "dob": {"year": 1923, "month": 4, "day": 12, "estimated": False},
            "dod": {"year": 1981, "month": 11, "day": 2, "estimated": False},
            "_provenance": {"table": "t", "row": 1, "source_id": "i1"}, "_confidence": 1.0,
        }],
    }


# internal ids assigned to each external_id in the fake tenant
_IDS = {
    "src:property_group:G1": 10,
    "src:property:P1": 20,
    "src:customer:C1": 30,
    "src:interment:I1": 40,
}
_MT = {
    "src:property_group:G1": _GROUP_MT,
    "src:property:P1": _PROPERTY_MT,
    "src:customer:C1": _CUSTOMER_MT,
    "src:interment:I1": _INTERMENT_MT,
}


class FakeClient:
    """Returns crafted live rows per resource. Tweak ``overrides`` to inject drift,
    or ``drop`` a set of external_ids to simulate them missing live."""

    def __init__(self, *, overrides: dict | None = None, drop: set[str] | None = None,
                 location: dict | None = None):
        self.overrides = overrides or {}
        self.drop = drop or set()
        # property internal id → {key: raw_value} live location attribute-values
        self.location = location if location is not None else {20: {"section": "A", "lot": "1", "space": "46"}}

    def _live_row(self, entity: str, ext: str) -> dict:
        base_by_entity = {
            "property_group": {"id": _IDS[ext], "name": "Sec A", "cemetery_id": 1},
            "property": {"id": _IDS[ext], "property_type_id": 7, "property_group_id": 10, "cemetery_id": 1},
            "customer": {"id": _IDS[ext], "status": "customer", "first_name": "JOHN",
                         "middle_name": None, "last_name": "SMITH", "suffix_id": None},
            "interment": {
                "id": _IDS[ext], "deceased_id": 30, "interment_space_id": 20, "cemetery_id": 1,
                "status": "completed", "is_manual": True, "date": "1981-11-02", "interment_type_id": 11,
                "dob_year": 1923, "dob_month": 4, "dob_day": 12, "dob_estimated": False,
                "dod_year": 1981, "dod_month": 11, "dod_day": 2, "dod_estimated": False,
                "doi_year": None, "doi_month": None, "doi_day": None, "doi_estimated": False,
            },
        }
        row = dict(base_by_entity[entity])
        row.update(self.overrides.get(ext, {}))
        return row

    def paginate(self, resource, *, filters=None, scopes=None, page_size=100):
        if resource == "external-ids":
            return iter([
                {"external_id": ext, "model_id": _IDS[ext], "model_type": _MT[ext], "system": "default"}
                for ext in _IDS if ext not in self.drop
            ])
        ent_for_resource = {
            "property-groups": "property_group", "properties": "property",
            "customers": "customer", "interments": "interment",
        }
        if resource in ent_for_resource:
            entity = ent_for_resource[resource]
            want_mt = {"property_group": _GROUP_MT, "property": _PROPERTY_MT,
                       "customer": _CUSTOMER_MT, "interment": _INTERMENT_MT}[entity]
            return iter([
                self._live_row(entity, ext) for ext in _IDS
                if _MT[ext] == want_mt and ext not in self.drop
            ])
        if resource == "attribute-values":
            rows = []
            for pid, kv in self.location.items():
                for key, val in kv.items():
                    rows.append({"attributable_type": _PROPERTY_MT, "attributable_id": pid,
                                 "key": key, "raw_value": val})
            return iter(rows)
        return iter([])


def _write_canonical(root: Path, data: dict) -> None:
    cdir = root / "runs" / "v1" / "canonical"
    cdir.mkdir(parents=True, exist_ok=True)
    for entity, recs in data.items():
        (cdir / f"{entity}.ndjson").write_text(
            "\n".join(json.dumps(r) for r in recs), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Clean case                                                                   #
# --------------------------------------------------------------------------- #
def test_clean_case_zero_mismatches(tmp_path):
    _write_canonical(tmp_path, _canonical())
    results, detail = reconcile_mod.reconcile_live(tmp_path, "v1", FakeClient())

    assert all(r.passed for r in results)  # count conservation passes
    fl = detail["field_level"]
    assert fl["severity"] == "warn"
    assert fl["mismatches_total"] == 0
    assert fl["per_field"] == {}
    assert fl["sample"] == []
    # every entity compared, none missing live
    for entity in ("property_group", "property", "customer", "interment"):
        assert fl["entities"][entity]["records_compared"] == 1
        assert fl["entities"][entity]["records_missing_live"] == 0
        assert fl["entities"][entity]["fields_compared"] > 0


# --------------------------------------------------------------------------- #
# Mismatch case — value drift on three fields + a location attr                #
# --------------------------------------------------------------------------- #
def test_mismatch_case_detects_each_field_warn_only(tmp_path):
    _write_canonical(tmp_path, _canonical())
    client = FakeClient(
        overrides={
            # wrong interment_type_id (value-set drift) + a partial-date day off
            "src:interment:I1": {"interment_type_id": 99, "dob_day": 13},
            # truncated last name
            "src:customer:C1": {"last_name": "SMIT"},
        },
        # wrong live location attribute (space drifted)
        location={20: {"section": "A", "lot": "1", "space": "99"}},
    )
    results, detail = reconcile_mod.reconcile_live(tmp_path, "v1", client)

    # WARN-only: count conservation still passes despite value drift.
    assert all(r.passed for r in results)
    assert all(d["conserved"] for d in detail["entities"].values())

    fl = detail["field_level"]
    assert fl["severity"] == "warn"
    assert fl["mismatches_total"] == 4

    # each mismatch attributed to the right field in the per-field tally
    assert fl["per_field"]["interment"]["interment_type_id"] == 1
    assert fl["per_field"]["interment"]["dob_day"] == 1
    assert fl["per_field"]["customer"]["last_name"] == 1
    assert fl["per_field"]["property"]["attr:space"] == 1

    # each mismatch present in the sample with expected + live values
    by_field = {(s["entity"], s["field"]): s for s in fl["sample"]}
    assert by_field[("interment", "interment_type_id")]["expected"] == 11
    assert by_field[("interment", "interment_type_id")]["live"] == 99
    assert by_field[("interment", "dob_day")]["expected"] == 12
    assert by_field[("interment", "dob_day")]["live"] == 13
    assert by_field[("customer", "last_name")]["expected"] == "SMITH"
    assert by_field[("customer", "last_name")]["live"] == "SMIT"
    assert by_field[("property", "attr:space")]["expected"] == "46"
    assert by_field[("property", "attr:space")]["live"] == "99"


def test_systematic_drift_surfaces_in_per_field_tally(tmp_path):
    """The per-field tally is what catches a SYSTEMATIC error across many rows."""
    data = _canonical()
    # add two more interments with the same projected interment_type_id
    for i in (2, 3):
        rec = dict(data["interment"][0])
        rec["external_id"] = f"src:interment:I{i}"
        rec["deceased_ref"] = "src:customer:C1"
        rec["property_ref"] = "src:property:P1"
        rec["_provenance"] = {"table": "t", "row": i, "source_id": f"i{i}"}
        data["interment"].append(rec)
    _IDS[f"src:interment:I2"] = 41
    _IDS[f"src:interment:I3"] = 42
    _MT[f"src:interment:I2"] = _INTERMENT_MT
    _MT[f"src:interment:I3"] = _INTERMENT_MT
    try:
        _write_canonical(tmp_path, data)
        client = FakeClient(overrides={
            ext: {"interment_type_id": 0} for ext in
            ("src:interment:I1", "src:interment:I2", "src:interment:I3")
        })
        _results, detail = reconcile_mod.reconcile_live(tmp_path, "v1", client)
        fl = detail["field_level"]
        # same field drifts on all 3 rows → tally of 3 (the systematic signal)
        assert fl["per_field"]["interment"]["interment_type_id"] == 3
    finally:
        for k in ("src:interment:I2", "src:interment:I3"):
            _IDS.pop(k, None)
            _MT.pop(k, None)


# --------------------------------------------------------------------------- #
# Missing-live case — the count lens (unchanged)                              #
# --------------------------------------------------------------------------- #
def test_missing_live_counted_in_records_missing_live(tmp_path):
    _write_canonical(tmp_path, _canonical())
    client = FakeClient(drop={"src:interment:I1"})
    results, detail = reconcile_mod.reconcile_live(tmp_path, "v1", client)

    # count lens flags the interment as not conserved (present 0 of 1)
    assert detail["entities"]["interment"]["conserved"] is False
    assert detail["entities"]["interment"]["live_present"] == 0
    # field lens skips it as missing-live, not as a value mismatch
    fl = detail["field_level"]
    assert fl["entities"]["interment"]["records_missing_live"] == 1
    assert fl["entities"]["interment"]["records_compared"] == 0
    assert fl["entities"]["interment"]["mismatches_total"] == 0


# --------------------------------------------------------------------------- #
# report.py renders the field_level block                                      #
# --------------------------------------------------------------------------- #
def test_report_renders_field_level_block(tmp_path):
    _write_canonical(tmp_path, _canonical())
    client = FakeClient(overrides={"src:customer:C1": {"last_name": "SMIT"}})
    results, detail = reconcile_mod.reconcile_live(tmp_path, "v1", client)
    reconcile_mod.write_reconcile_stage(tmp_path, "v1", results, detail)

    res = report_mod.build_report(tmp_path, "v1")
    text = (res["report_path"]).read_text()
    assert "Field-level (values)" in text
    assert "field mismatch(es) (warn)" in text
    assert "Per-field mismatch tally" in text
    assert "last_name" in text


def test_norm_folds_representation_not_meaning():
    """_norm folds out wire-representation differences but still catches real drift."""
    n = reconcile_mod._norm
    # None ≡ empty
    assert n(None) == n("")
    # bool ≡ Laravel tinyint over the wire
    assert n(False) == n(0) == n("0")
    assert n(True) == n(1) == n("1")
    # numeric id int ≡ string
    assert n(11) == n("11")
    # date-only ≡ API full ISO datetime at midnight
    assert n("1950-07-31") == n("1950-07-31T00:00:00.000000Z")
    # real drift is NOT folded
    assert n(11) != n(99)
    assert n("completed") != n("awaiting-scheduling")
    assert n("SMITH") != n("SMIT")


def test_reconciliation_md_renders_field_level(tmp_path):
    _write_canonical(tmp_path, _canonical())
    client = FakeClient(overrides={"src:customer:C1": {"last_name": "SMIT"}})
    results, detail = reconcile_mod.reconcile_live(tmp_path, "v1", client)
    md, js = reconcile_mod.write_reconcile_stage(tmp_path, "v1", results, detail)
    text = md.read_text()
    assert "Field-level reconcile (values)" in text
    assert "warn" in text.lower()
    payload = json.loads(js.read_text())
    assert payload["field_level"]["mismatches_total"] == 1
