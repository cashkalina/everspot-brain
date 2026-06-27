"""Regression — LESSONS.md #5: non-atomic Orion batch caused duplicate inserts.

THE BUG: a ``batch-create`` that failed partway left orphan rows (no external_id
registered); the per-record fallback then re-inserted them → DUPLICATES (false
multi-occupancy was observed live).

THE FIX (two parts):
  1. ``config/orion.php`` ``transactions.enabled=true`` → batches are ATOMIC → a
     failed batch ROLLS BACK, so it leaves NO orphan rows.
  2. ``orion_load.OrionLoader.load_entity`` only falls back to per-record create AFTER
     the whole batch failed (``made is None``) — never mixing a partial batch with a
     retry. So when the atomic batch rolls back, each record is created exactly once
     by the fallback and registered exactly once.

This test exercises the LOADER logic with a mocked ``OrionClient`` whose
``batch_store`` raises (simulating an atomic batch that rolled back) and whose
per-record ``create`` succeeds. The assertion: every external_id is created and
registered EXACTLY ONCE — no duplicate external_id, no duplicate underlying row.

A reversion (per-record retry of a partially-applied non-atomic batch) would create
the chunk's rows twice → this fails with duplicate registrations.
"""

import pandas as pd  # noqa: F401  (kept for parity with other regression fixtures)
import pytest

import orion_load
from external_ids import ExternalIdLedger
from orion_client import OrionError


class _FakeBatchRollsBackClient:
    """Simulates Orion with ATOMIC batches that fail-and-roll-back.

    - ``batch_store`` on a model resource RAISES (the atomic batch rolled back →
      nothing was inserted, exactly like the post-fix config).
    - ``create`` succeeds, assigning a monotonically increasing id and RECORDING
      every (resource, external_id-ish) insert so the test can detect duplicates.
    - ``batch_store`` on ``external-ids`` records each registration (this is where a
      duplicate external_id would show up).
    """

    def __init__(self):
        self._next_id = 1000
        self.created_rows: list[tuple[str, dict]] = []           # (resource, payload)
        self.registered_external_ids: list[str] = []
        self.batch_store_calls: list[str] = []

    def paginate(self, resource, **kwargs):
        return iter(())  # empty tenant: no cemeteries, property-types, or external-ids

    def create(self, resource, payload):
        self._next_id += 1
        self.created_rows.append((resource, payload))
        # A1: the external_id rides inside the create payload (atomic server-side register).
        if payload.get("external_id"):
            self.registered_external_ids.append(payload["external_id"])
        return {"id": self._next_id}

    def update(self, resource, resource_id, payload):  # pragma: no cover - not exercised
        return {"id": resource_id}

    def batch_store(self, resource, rows):
        self.batch_store_calls.append(resource)
        # A1: there is no separate external-ids registration call for new records.
        assert resource != "external-ids", \
            "A1: new-record creation must not make a separate external-ids batch call"
        # A model batch: the atomic transaction rolled back → raise, insert nothing.
        raise OrionError(500, "batch rolled back", f"/{resource}/batch")


@pytest.fixture()
def loader(tmp_path):
    client = _FakeBatchRollsBackClient()
    ledger = ExternalIdLedger(tmp_path / "external_ids.json")
    ld = orion_load.OrionLoader(client, ledger, cemetery_name="Test")
    ld.cemetery_id = 1
    ld.property_type_id = 2
    return ld, client


def _customer(ext, source_id):
    return {
        "external_id": ext,
        "status": "customer",
        "first_name": "A",
        "last_name": "B",
        "_provenance": {"table": "T", "row": 1, "source_id": source_id},
        "_confidence": 1.0,
    }


def test_regression_non_atomic_batch_duplication(loader):
    ld, client = loader
    records = [_customer(f"src:customer:{i}", f"T:{i}") for i in range(3)]

    ld.load_entity("customer", records)

    # Each record was created exactly once via the per-record fallback.
    customer_inserts = [r for (res, r) in client.created_rows if res == "customers"]
    assert len(customer_inserts) == 3, "fallback must create each record exactly once"

    # No duplicate external_id was ever registered.
    assert sorted(client.registered_external_ids) == [
        "src:customer:0", "src:customer:1", "src:customer:2",
    ]
    assert len(client.registered_external_ids) == len(set(client.registered_external_ids))

    # The loader counts reflect 3 created, 0 failed (the rollback did not duplicate).
    assert ld.result.created["customer"] == 3
    assert ld.result.failed["customer"] == 0


def test_atomic_batch_success_does_not_also_run_fallback(tmp_path):
    """Mirror: when the atomic batch SUCCEEDS, the fallback must NOT also create."""

    class _FakeBatchSucceedsClient:
        def __init__(self):
            self._next_id = 0
            self.created_via_create = 0
            self.registered_external_ids: list[str] = []

        def paginate(self, resource, **kwargs):
            return iter(())

        def create(self, resource, payload):  # pragma: no cover - must NOT be hit
            self.created_via_create += 1
            self._next_id += 1
            return {"id": self._next_id}

        def update(self, resource, rid, payload):
            return {"id": rid}

        def batch_store(self, resource, rows):
            # A1: external_id rides inside the model create payload; no separate call.
            assert resource != "external-ids", \
                "A1: new-record creation must not make a separate external-ids batch call"
            out = []
            for r in rows:
                self._next_id += 1
                if r.get("external_id"):
                    self.registered_external_ids.append(r["external_id"])
                out.append({"id": self._next_id})
            return out

    client = _FakeBatchSucceedsClient()
    ledger = ExternalIdLedger(tmp_path / "external_ids.json")
    ld = orion_load.OrionLoader(client, ledger, cemetery_name="Test")
    ld.cemetery_id = 1
    ld.property_type_id = 2

    records = [_customer(f"src:customer:{i}", f"T:{i}") for i in range(3)]
    ld.load_entity("customer", records)

    assert client.created_via_create == 0, "fallback must not run when the batch succeeded"
    assert ld.result.created["customer"] == 3
    assert len(client.registered_external_ids) == len(set(client.registered_external_ids)) == 3
