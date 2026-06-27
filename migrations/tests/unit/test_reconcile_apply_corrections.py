"""A2 — self-healing corrections: PATCH already-loaded live records whose field VALUE
drifted from the canonical projection, idempotently.

``reconcile.apply_corrections`` reuses the field-level reconcile machinery (the SAME
loader projection oracle + tolerant ``_norm`` comparator the post-load ``--live``
reconcile uses): for each drifted field it PATCHes the live record's drifted field(s) back
to the canonical value; a second run finds nothing left to fix (a no-op). It is GENERAL —
driven off the projection diff, no client columns — and subsumes the loader's special-case
interment-status correction (status/is_manual are part of the interment projection).

All mocked: no Laravel, no network.
"""

from __future__ import annotations

import json
from pathlib import Path

import reconcile


def _write_canonical(root: Path, entity: str, records: list[dict]) -> None:
    canonical = root / "runs" / "v1" / "canonical"
    canonical.mkdir(parents=True, exist_ok=True)
    (canonical / f"{entity}.ndjson").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
    )


def _interment(ext, **over):
    rec = {
        "external_id": ext, "status": "completed", "deceased_ref": "src:customer:D",
        "doi": {"year": 1990, "month": 5, "day": 2, "estimated": False},
        "_provenance": {"table": "burials", "row": 1, "source_id": f"sid:{ext}"},
        "_confidence": 1.0,
    }
    rec.update(over)
    return rec


class _DriftClient:
    """A tenant whose interment 42 has DRIFTED from its canonical projection.

    - ``external-ids`` maps the canonical external_id to internal id 42.
    - The live interment 42 starts at a WRONG status + is_manual=False, and the PATCH
      mutates it in place (so a second run sees the corrected state → no-op).
    """

    def __init__(self, ext, *, live_status, live_is_manual, live_date, extra=None):
        self._ext = ext
        row = {"id": 42, "status": live_status, "is_manual": live_is_manual,
               "date": live_date, "deceased_id": None,
               "interment_space_id": None, "interment_type_id": None,
               "cemetery_id": 1,
               # Partial-date columns the projection expands doi into — seeded to the
               # canonical values so they are not spurious drift (the matching baseline).
               "doi_year": 1990, "doi_month": 5, "doi_day": 2, "doi_estimated": False}
        if extra:
            row.update(extra)
        self.live = {42: row}
        self.updates: list[tuple[str, int, dict]] = []

    def paginate(self, resource, **kwargs):
        if resource == "external-ids":
            return iter([{"system": "default", "external_id": self._ext,
                          "model_type": "Modules\\Interment\\Models\\Interment",
                          "model_id": 42}])
        if resource == "interments":
            return iter([dict(v) for v in self.live.values()])
        return iter(())

    def update(self, resource, rid, payload):
        self.updates.append((resource, rid, payload))
        # Mutate the live row in place so the next run sees the corrected values.
        self.live[rid].update(payload)
        return {"id": rid, **payload}

    def post(self, path, payload):  # pragma: no cover - no property location here
        return {"summary": {"successful": 0, "failed": 0}}


def test_drifted_live_row_is_patched_to_canonical(tmp_path):
    ext = "src:interment:1"
    _write_canonical(tmp_path, "interment", [_interment(ext)])
    # Live row drifted: wrong status, not manual, date wrong.
    client = _DriftClient(ext, live_status="awaiting-scheduling", live_is_manual=False,
                          live_date="1899-01-01")

    summary = reconcile.apply_corrections(tmp_path, "v1", client, entities=["interment"])

    # Exactly one PATCH, carrying the drifted fields corrected to the canonical projection.
    assert len(client.updates) == 1
    _resource, rid, payload = client.updates[0]
    assert rid == 42
    assert payload["status"] == "completed"
    assert payload["is_manual"] is True
    assert payload["date"] == "1990-05-02"
    # Fields already matching are NOT in the drift PATCH.
    assert "cemetery_id" not in payload  # prerequisite constant, never "drift"
    ent = summary["entities"]["interment"]
    assert ent["records_patched"] == 1
    assert ent["fields_patched"] >= 3


def test_second_run_is_a_noop(tmp_path):
    ext = "src:interment:1"
    _write_canonical(tmp_path, "interment", [_interment(ext)])
    client = _DriftClient(ext, live_status="awaiting-scheduling", live_is_manual=False,
                          live_date="1899-01-01")

    reconcile.apply_corrections(tmp_path, "v1", client, entities=["interment"])
    first_run_updates = len(client.updates)
    assert first_run_updates == 1

    # Second run: the live row now matches the canonical projection → nothing to fix.
    summary2 = reconcile.apply_corrections(tmp_path, "v1", client, entities=["interment"])
    assert len(client.updates) == first_run_updates, "a second run must PATCH nothing"
    assert summary2["entities"]["interment"]["records_patched"] == 0


def test_already_matching_row_is_not_patched(tmp_path):
    ext = "src:interment:1"
    _write_canonical(tmp_path, "interment", [_interment(ext)])
    # Live row already in the projected state.
    client = _DriftClient(ext, live_status="completed", live_is_manual=True,
                          live_date="1990-05-02")

    summary = reconcile.apply_corrections(tmp_path, "v1", client, entities=["interment"])
    assert client.updates == []
    assert summary["entities"]["interment"]["records_patched"] == 0


class _PropertyDriftClient:
    """A tenant whose property 77's location custom field (section) has drifted."""

    def __init__(self, ext, *, live_section):
        self._ext = ext
        self.live = {77: {"id": 77, "property_type_id": 2, "property_group_id": None,
                          "cemetery_id": 1}}
        self._live_section = live_section
        self.upserts: list[dict] = []
        self.updates: list[tuple[str, int, dict]] = []

    def paginate(self, resource, **kwargs):
        if resource == "external-ids":
            return iter([{"system": "default", "external_id": self._ext,
                          "model_type": "Modules\\Property\\Models\\Property",
                          "model_id": 77}])
        if resource == "properties":
            return iter([dict(v) for v in self.live.values()])
        if resource == "attribute-values":
            if self._live_section is None:
                return iter(())
            return iter([{"attributable_type": "Modules\\Property\\Models\\Property",
                          "attributable_id": 77, "key": "section",
                          "raw_value": self._live_section}])
        return iter(())

    def update(self, resource, rid, payload):  # pragma: no cover - column path not drifting
        self.updates.append((resource, rid, payload))
        return {"id": rid, **payload}

    def post(self, path, payload):
        self.upserts.append(payload)
        n = sum(len(e["attributes"]) for e in payload["entities"])
        return {"summary": {"successful": n, "failed": 0}}


def test_drifted_property_location_is_upserted(tmp_path):
    ext = "src:property:1"
    _write_canonical(tmp_path, "property", [{
        "external_id": ext, "property_group_ref": None, "section": "A",
        "_provenance": {"table": "graves", "row": 1, "source_id": "g:1"},
        "_confidence": 1.0,
    }])
    # Live section drifted from canonical "A".
    client = _PropertyDriftClient(ext, live_section="WRONG")

    summary = reconcile.apply_corrections(tmp_path, "v1", client, entities=["property"])

    assert len(client.upserts) == 1, "drifted location must be upserted via the batch endpoint"
    entity = client.upserts[0]["entities"][0]
    assert entity["attributable_id"] == 77
    assert {"key": "section", "value": "A"} in entity["attributes"]
    assert summary["location"]["properties_to_upsert"] == 1
    assert summary["location"]["upserted"] == 1

    # Idempotent: with the live section now "A", a second run upserts nothing.
    client2 = _PropertyDriftClient(ext, live_section="A")
    summary2 = reconcile.apply_corrections(tmp_path, "v1", client2, entities=["property"])
    assert client2.upserts == []
    assert summary2["location"]["properties_to_upsert"] == 0


def test_dry_run_plans_but_does_not_patch(tmp_path):
    ext = "src:interment:1"
    _write_canonical(tmp_path, "interment", [_interment(ext)])
    client = _DriftClient(ext, live_status="awaiting-scheduling", live_is_manual=False,
                          live_date="1899-01-01")

    summary = reconcile.apply_corrections(tmp_path, "v1", client, entities=["interment"],
                                          dry_run=True)
    assert client.updates == [], "dry_run must not issue any PATCH"
    assert summary["dry_run"] is True
    # The plan still reports what WOULD be corrected.
    assert summary["entities"]["interment"]["records_patched"] == 1
