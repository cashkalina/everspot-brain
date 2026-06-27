"""Unit tests for the interment status write path (migration-safe `completed`).

A migrated historical interment must land in the status the canonical record carries
(``completed``) rather than the app's operational default (``awaiting-scheduling``).
Everspot's Interment model imposes a state machine: the auto stage-progression listener
demotes a POSTed ``completed`` unless the interment is flagged with the platform's
``is_manual`` field ("Manual / Enable to enter historical interment"). For a manual
interment the relaxed manual validation makes ``completed`` a valid terminal state (no
scheduled event/space required), so it is never demoted. The loader therefore projects
every migrated interment with ``is_manual=True``.

``is_manual`` is a REAL column, so — unlike the retired write-only ``migration_mode``
flag — it is part of the pure projection (``project_payload``, the reconcile oracle) and
IS reconciled against the live row.

These tests drive ``OrionLoader`` / its pure projection against a MOCK ``OrionClient``
(no Laravel, no network) and assert:

  * ``project_payload`` keeps the interment's provided ``status`` and carries
    ``is_manual=True``;
  * an already-loaded interment whose live status/is_manual is wrong is PATCHed to the
    projected state — and a re-run, where the live row already matches, is a no-op.
"""

from __future__ import annotations

import orion_load


def _interment(ext, status="completed", deceased_ref="src:customer:D"):
    return {
        "external_id": ext,
        "status": status,
        "deceased_ref": deceased_ref,
        "doi": {"year": 1990, "month": 5, "day": 2, "estimated": False},
        "_provenance": {"table": "burials", "row": 1, "source_id": f"sid:{ext}"},
        "_confidence": 1.0,
    }


def test_project_payload_keeps_status_and_marks_manual():
    payload = orion_load.project_payload(
        "interment", _interment("src:interment:1"),
        cemetery_id=1, property_type_id=7, resolve_ref=lambda r: None,
    )
    assert payload["status"] == "completed"
    # A migrated interment is a historical/manual interment.
    assert payload["is_manual"] is True


def test_project_payload_defaults_status_to_completed_when_absent():
    rec = _interment("src:interment:1")
    rec.pop("status")
    payload = orion_load.project_payload(
        "interment", rec,
        cemetery_id=1, property_type_id=7, resolve_ref=lambda r: None,
    )
    assert payload["status"] == "completed"
    assert payload["is_manual"] is True


class _StatusClient:
    """Minimal mock that records interment writes and serves a configurable live row."""

    def __init__(self, *, live_interments=None):
        self._next_id = 500
        # internal_id -> (live status, live is_manual), for the correction read-back.
        self.live_interments = live_interments or {}
        self.created: list[tuple[str, dict]] = []
        self.updated: list[tuple[str, int, dict]] = []

    def paginate(self, resource, *, filters=None, scopes=None, page_size=100):
        if resource == "cemeteries":
            return iter([{"id": 1, "name": "Test Cemetery"}])
        if resource == "property-types":
            return iter([{"id": 7, "name": "Lot"}])
        if resource == "external-ids":
            return iter([])
        if resource == "interments":
            return iter([
                {"id": i, "status": s, "is_manual": m}
                for i, (s, m) in self.live_interments.items()
            ])
        return iter([])

    def create(self, resource, payload):
        self.created.append((resource, payload))
        self._next_id += 1
        return {"id": self._next_id, **payload}

    def batch_store(self, resource, rows):
        out = []
        for r in rows:
            self._next_id += 1
            out.append({"id": self._next_id, **r})
            self.created.append((resource, r))
        return out

    def update(self, resource, resource_id, payload):
        self.updated.append((resource, resource_id, payload))
        return {"id": resource_id, **payload}


class _FakeLedger:
    def everspot_id(self, ref):
        return None

    def attach_everspot_ids(self, mapping):
        pass

    def save(self):
        pass


def _loader(client):
    loader = orion_load.OrionLoader(client, _FakeLedger(), cemetery_name="Test Cemetery")
    loader.ensure_prerequisites()
    loader.prefetch_existing_external_ids()
    return loader


def test_write_payload_marks_interment_manual():
    client = _StatusClient()
    loader = _loader(client)
    payload = loader._payload("interment", _interment("src:interment:1"))
    assert payload["is_manual"] is True
    assert payload["status"] == "completed"


def test_present_interment_with_wrong_live_status_is_corrected():
    # Already loaded (external_id present) with the WRONG live status — the bug case.
    ext = "src:interment:1"
    client = _StatusClient(live_interments={42: ("awaiting-scheduling", False)})
    loader = _loader(client)
    loader.existing[ext] = 42

    loader.load_entity("interment", [_interment(ext)])

    # One corrective PATCH carrying the projected status + is_manual.
    assert len(client.updated) == 1
    resource, rid, payload = client.updated[0]
    assert resource == "interments" and rid == 42
    assert payload["status"] == "completed"
    assert payload["is_manual"] is True
    assert loader.result.updated["interment"] == 1
    assert loader.result.skipped["interment"] == 0


def test_present_interment_correct_status_but_not_manual_is_corrected():
    # Loaded before is_manual was applied: live status already `completed` but is_manual
    # is false → still PATCHed so the manual flag (and durable completed) is applied.
    ext = "src:interment:1"
    client = _StatusClient(live_interments={42: ("completed", False)})
    loader = _loader(client)
    loader.existing[ext] = 42

    loader.load_entity("interment", [_interment(ext)])

    assert len(client.updated) == 1
    _resource, _rid, payload = client.updated[0]
    assert payload["is_manual"] is True
    assert loader.result.updated["interment"] == 1
    assert loader.result.skipped["interment"] == 0


def test_present_interment_already_correct_is_left_untouched():
    # Idempotent re-run: live status + is_manual already match → no PATCH, counted skipped.
    ext = "src:interment:1"
    client = _StatusClient(live_interments={42: ("completed", True)})
    loader = _loader(client)
    loader.existing[ext] = 42

    loader.load_entity("interment", [_interment(ext)])

    assert client.updated == []
    assert loader.result.updated["interment"] == 0
    assert loader.result.skipped["interment"] == 1
