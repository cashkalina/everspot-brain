"""Regression — H3: the load resume contract must be HONEST (wave-level, not mid-wave).

THE BUG: ``_chunks_done``/``chunk_cb`` only ever incremented in the batch-FAILURE
branch (the happy path skipped it), and ``load()`` resume keyed solely off
``waves_done`` — ``chunks_done`` was written but never consulted. So the loader offered
WAVE-LEVEL resume + idempotent upsert, NOT the mid-wave resume the comments/LIBRARY.md
claimed.

THE FIX: make the contract honest. The chunks_done/chunk_cb machinery is REMOVED; resume
is wave-level (safe now that H2 made a wave re-POST idempotent). This test pins the honest
contract: (1) the chunk machinery is gone from the loader and run_state, and (2) a
mid-wave crash resumes at wave granularity without duplicating already-loaded waves.
"""

import json

import orion_load
import run_state
from external_ids import ExternalIdLedger


def test_chunk_machinery_removed_from_loader():
    """The dishonest mid-wave chunk-callback machinery is gone from the loader."""
    loader_init_params = orion_load.OrionLoader.__init__.__code__.co_varnames
    assert "chunk_cb" not in loader_init_params, "chunk_cb must be removed from the loader"
    # The loader no longer carries chunk-progress state.
    import inspect
    src = inspect.getsource(orion_load)
    assert "_chunks_done" not in src, "loader must not track _chunks_done"
    assert "self.chunk_cb" not in src, "loader must not hold a chunk_cb"


def test_load_never_writes_chunks_done_into_checkpoint(tmp_path):
    """The honest wave-level load() must NOT write a (dishonest) chunks_done counter.

    chunks_done is retained ONLY as a deprecated, informational back-compat field on
    set_load_checkpoint; the load path must never advance it (it never drove resume).
    """

    class _Client:
        def __init__(self):
            self._n = 10

        def paginate(self, resource, **kwargs):
            if resource == "cemeteries":
                return iter([{"id": 1, "name": "Test"}])
            if resource == "property-types":
                return iter([{"id": 2, "name": "Lot"}])
            return iter(())

        def create(self, resource, payload):
            self._n += 1
            return {"id": self._n, **payload}

        def update(self, resource, rid, payload):
            return {"id": rid, **payload}

        def batch_store(self, resource, rows):
            if resource == "external-ids":
                return list(rows)
            out = []
            for p in rows:
                self._n += 1
                out.append({"id": self._n, **p})
            return out

    root = tmp_path / "proj"
    canonical = root / "runs" / "v1" / "canonical"
    canonical.mkdir(parents=True)
    (canonical / "property_group.ndjson").write_text(
        json.dumps({"external_id": "src:pg:1", "name": "Sec A",
                    "cemetery_ref": "src:cemetery:default",
                    "_provenance": {"source_id": "PG:1"}}) + "\n",
        encoding="utf-8",
    )
    (root / "ledger").mkdir(parents=True)

    orion_load.load(root, "v1", _Client(), cemetery_name="Test", scoped=False)

    cp = run_state.get_load_checkpoint(root / "runs" / "v1")
    assert "chunks_done" not in cp, "the load path must not write chunks_done (wave-level only)"


def test_wave_level_resume_does_not_reload_completed_waves(tmp_path):
    """A checkpoint with a completed wave skips that wave on resume (no duplicate work)."""

    class _RecordingClient:
        def __init__(self):
            self._next_id = 100
            self.created: list[tuple[str, dict]] = []
            self.registered: list[str] = []

        def paginate(self, resource, **kwargs):
            if resource == "cemeteries":
                return iter([{"id": 1, "name": "Test"}])
            if resource == "property-types":
                return iter([{"id": 2, "name": "Lot"}])
            return iter(())

        def create(self, resource, payload):
            self._next_id += 1
            self.created.append((resource, payload))
            return {"id": self._next_id, **payload}

        def update(self, resource, rid, payload):
            return {"id": rid, **payload}

        def batch_store(self, resource, rows):
            if resource == "external-ids":
                self.registered.extend(r["external_id"] for r in rows)
                return list(rows)
            out = []
            for p in rows:
                self._next_id += 1
                self.created.append((resource, p))
                out.append({"id": self._next_id, **p})
            return out

    # Lay down a project with a property_group canonical record + a checkpoint that says
    # property_group is already done (a prior run crashed after that wave).
    root = tmp_path / "proj"
    run_dir = root / "runs" / "v1"
    canonical = run_dir / "canonical"
    canonical.mkdir(parents=True)
    (canonical / "property_group.ndjson").write_text(
        json.dumps({"external_id": "src:pg:1", "name": "Sec A",
                    "cemetery_ref": "src:cemetery:default",
                    "_provenance": {"source_id": "PG:1"}}) + "\n",
        encoding="utf-8",
    )
    (root / "ledger").mkdir(parents=True)

    run_state.set_load_checkpoint(run_dir, waves_done=["property_group"], complete=False)

    client = _RecordingClient()
    orion_load.load(root, "v1", client, cemetery_name="Test", scoped=False)

    # property_group was marked done in the checkpoint → it must NOT be re-created.
    pg_creates = [p for (res, p) in client.created if res == "property-groups"]
    assert pg_creates == [], "a completed wave must be skipped on resume (wave-level resume)"
