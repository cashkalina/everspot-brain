"""Regression/feature — resumable, checkpointed Orion load (SPEC §17).

Proves a mid-load crash is recoverable WITHOUT duplicating already-loaded waves:

  1. A mocked OrionClient raises after the ``property`` wave (simulating a crash mid-load).
  2. The first ``load()`` call propagates the error but leaves a load checkpoint recording
     ``waves_done = [property_group, property]``.
  3. A second ``load()`` call RESUMES — skips property_group + property, loads customer +
     interment, and finalizes the checkpoint as complete.
  4. No external_id is registered twice (no double-registration of an already-loaded wave).

All inputs are SYNTHETIC (a tiny canonical graph written inline); no live sandbox.
"""

from __future__ import annotations

import json

import pytest

import orion_load
import run_state


# --------------------------------------------------------------------------- #
# Synthetic canonical graph (one of each wave entity)                          #
# --------------------------------------------------------------------------- #
def _write_canonical(project):
    canonical = project / "runs" / "v1" / "canonical"
    canonical.mkdir(parents=True, exist_ok=True)
    cem = "src:cemetery:default"  # the synthetic cemetery ref the assembler stamps
    records = {
        "property_group": [{
            "external_id": "src:property_group:SEC-A", "name": "Section A",
            "cemetery_ref": cem,
            "_provenance": {"table": "T", "row": 1, "source_id": "T:pg"},
        }],
        "property": [{
            "external_id": "src:property:SEC-A-1", "property_group_ref": "src:property_group:SEC-A",
            "cemetery_ref": cem,
            "_provenance": {"table": "T", "row": 1, "source_id": "T:p1"},
        }],
        "customer": [{
            "external_id": "src:customer:1", "status": "customer",
            "first_name": "Ada", "last_name": "Lovelace",
            "_provenance": {"table": "T", "row": 1, "source_id": "T:c1"},
        }],
        "interment": [{
            "external_id": "src:interment:1", "deceased_ref": "src:customer:1",
            "property_ref": "src:property:SEC-A-1", "status": "completed",
            "doi": {"year": 1852, "month": 11, "day": 27, "estimated": False},
            "_provenance": {"table": "T", "row": 1, "source_id": "T:i1"},
        }],
    }
    for entity, recs in records.items():
        (canonical / f"{entity}.ndjson").write_text(
            "\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8"
        )
    return canonical


class _CrashAfterWaveClient:
    """Mock OrionClient that raises when a target wave's resource is first batch-created.

    A1 (atomic create+register): the external_id now travels INSIDE the create/batch model
    payload (the server registers it in the same transaction), so this mock harvests
    ``registered_external_ids`` from the create payloads — there is no separate
    ``external-ids`` batch_store call for new records. An empty tenant (paginate yields
    nothing) so the first run sees every record as NEW.
    """

    def __init__(self, crash_after_resource=None):
        self._next_id = 0
        self.crash_after_resource = crash_after_resource
        self.registered_external_ids: list[str] = []
        self.created_resources: list[str] = []

    def paginate(self, resource, **kwargs):
        return iter(())

    def create(self, resource, payload):
        self._next_id += 1
        self.created_resources.append(resource)
        if payload.get("external_id"):
            self.registered_external_ids.append(payload["external_id"])
        return {"id": self._next_id}

    def update(self, resource, rid, payload):  # pragma: no cover
        return {"id": rid}

    def post(self, path, payload):  # attribute-values/batch-upsert
        return {"summary": {"successful": 0, "failed": 0}, "data": [], "errors": []}

    def batch_store(self, resource, rows):
        # A1: no separate external-ids registration call for newly-created records.
        assert resource != "external-ids", \
            "A1: new-record creation must not make a separate external-ids batch call"
        if resource == self.crash_after_resource:
            # A non-OrionError crash (e.g. a process kill / network reset) — NOT caught by
            # the loader's per-record OrionError fallback, so it propagates out of load(),
            # leaving the checkpoint mid-load (exactly a real mid-load crash).
            raise RuntimeError("simulated crash mid-load")
        out = []
        for r in rows:
            self._next_id += 1
            self.created_resources.append(resource)
            if r.get("external_id"):
                self.registered_external_ids.append(r["external_id"])
            out.append({"id": self._next_id})
        return out


@pytest.fixture
def project(tmp_path):
    proj = tmp_path / "synth"
    (proj / "ledger").mkdir(parents=True, exist_ok=True)
    _write_canonical(proj)
    return proj


def test_load_resumes_after_crash_without_duplication(project):
    run_dir = project / "runs" / "v1"

    # --- Run 1: crash when the `customer` wave is batch-created (after property). -----
    crash_client = _CrashAfterWaveClient(crash_after_resource="customers")

    with pytest.raises(RuntimeError):
        orion_load.load(project, "v1", crash_client, cemetery_name="Synth", scoped=False)

    cp = run_state.get_load_checkpoint(run_dir)
    assert not cp.get("complete"), "a crashed load must leave an INCOMPLETE checkpoint"
    assert cp["waves_done"] == ["property_group", "property"], \
        "the two completed waves must be checkpointed"
    assert cp["current_wave"] == "customer", "the crashing wave is the current wave"

    # property_group + property external_ids were registered exactly once.
    assert sorted(crash_client.registered_external_ids) == [
        "src:property:SEC-A-1", "src:property_group:SEC-A",
    ]

    # --- Run 2: a fresh load() RESUMES — skips done waves, finishes the rest. ----------
    # The resumed client's tenant already holds the property_group + property external_ids
    # (the first run registered them); model the idempotent prefetch by returning them.
    resume_client = _CrashAfterWaveClient(crash_after_resource=None)
    already = list(crash_client.registered_external_ids)

    def _paginate(resource, **kwargs):
        if resource == "external-ids":
            return iter([
                {"system": "default", "external_id": ext, "model_id": 100 + i}
                for i, ext in enumerate(already)
            ])
        return iter(())

    resume_client.paginate = _paginate

    result = orion_load.load(project, "v1", resume_client, cemetery_name="Synth", scoped=False)

    # The resume must NOT re-create the already-loaded waves.
    assert "property_groups" not in resume_client.created_resources
    assert "properties" not in resume_client.created_resources
    # It DID load the remaining waves.
    assert result.created.get("customer", 0) == 1
    assert result.created.get("interment", 0) == 1

    # No double-registration: customer + interment registered once; the prior two not redone.
    assert sorted(resume_client.registered_external_ids) == [
        "src:customer:1", "src:interment:1",
    ]

    cp = run_state.get_load_checkpoint(run_dir)
    assert cp["complete"] is True
    assert cp["waves_done"] == ["property_group", "property", "customer", "interment"]


def test_clean_load_finalizes_checkpoint(project):
    """A non-crashing load marks the checkpoint complete with all four waves."""
    run_dir = project / "runs" / "v1"
    client = _CrashAfterWaveClient(crash_after_resource=None)
    orion_load.load(project, "v1", client, cemetery_name="Synth", scoped=False)
    cp = run_state.get_load_checkpoint(run_dir)
    assert cp["complete"] is True
    assert cp["waves_done"] == ["property_group", "property", "customer", "interment"]
    # Every external_id registered exactly once.
    assert len(client.registered_external_ids) == len(set(client.registered_external_ids)) == 4
