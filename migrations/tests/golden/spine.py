"""Golden-fixture spine runner — shared by the golden + conformance tests.

Copies a SYNTHETIC fixture project to a temp dir and runs the deterministic spine
(ingest → assemble → emit → dry-load) so a test can compare the produced artifacts
against the committed golden. All inputs are synthetic; no client data, no network,
no LLM, no live Laravel.

The dry-load uses :class:`RecordingDryClient` (a fake OrionClient) — it never touches
a real tenant; it records the planned create payloads + external-id registrations so
the "dry plan" can be frozen as golden.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

import assemble
import emit_excel
import orion_load
from snapshot import SourceTableConfig, ingest_snapshot

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class RecordingDryClient:
    """A fake OrionClient that records the planned writes (a dry load plan).

    Empty tenant (``paginate`` yields nothing) so every record is planned as a
    create. Atomic batch_store succeeds and assigns deterministic sequential ids.

    A1 (atomic create+register): the external_id now rides INSIDE the create/batch model
    payload (the server registers it in the same transaction), so the dry plan harvests
    ``registered`` from the create payloads — there is NO separate ``external-ids`` batch
    call for newly-created records. ``_ENTITY_MODEL_TYPE`` maps the Orion resource to its
    polymorphic model_type FQCN so the recorded (model_type, external_id) shape is
    unchanged from before.
    """

    _ENTITY_MODEL_TYPE = {
        "property-groups": "Modules\\Property\\Models\\PropertyGroup",
        "properties": "Modules\\Property\\Models\\Property",
        "customers": "Modules\\Customer\\Models\\Customer",
        "interments": "Modules\\Interment\\Models\\Interment",
    }

    def __init__(self) -> None:
        self._next_id = 0
        self.created: list[tuple[str, dict]] = []           # (resource, payload)
        self.registered: list[tuple[str, str]] = []          # (model_type, external_id)

    def paginate(self, resource: str, **kwargs: Any):
        return iter(())

    def _record_external_id(self, resource: str, payload: dict) -> None:
        ext = payload.get("external_id")
        if ext:
            self.registered.append((self._ENTITY_MODEL_TYPE.get(resource, ""), ext))

    def create(self, resource: str, payload: dict) -> dict:
        self._next_id += 1
        self.created.append((resource, payload))
        self._record_external_id(resource, payload)
        return {"id": self._next_id}

    def update(self, resource: str, resource_id, payload: dict) -> dict:  # pragma: no cover
        return {"id": resource_id}

    def batch_store(self, resource: str, rows):
        assert resource != "external-ids", \
            "A1: new-record creation must not make a separate external-ids batch call"
        out = []
        for r in rows:
            self._next_id += 1
            self.created.append((resource, r))
            self._record_external_id(resource, r)
            out.append({"id": self._next_id})
        return out


def _source_configs(project_dir: Path) -> list[SourceTableConfig]:
    py = yaml.safe_load((project_dir / "project.yaml").read_text(encoding="utf-8"))
    return [
        SourceTableConfig(
            table=s["table"],
            source_key=s.get("source_key"),
            key_status=s.get("key_status", "confirmed"),
        )
        for s in py.get("sources", [])
    ]


def run_spine(fixture: str, dest: Path, snapshot: str = "v1") -> dict[str, Any]:
    """Run ingest → assemble → emit → dry-load for ``fixture`` into ``dest``.

    Returns a dict of artifacts + the assemble/dry-load results.
    """
    src = FIXTURES_DIR / fixture
    project = dest / fixture
    shutil.copytree(src, project)

    ingest_snapshot(project / "snapshots" / snapshot, _source_configs(project))

    assemble_result = assemble.assemble(project, snapshot, use_cache=False, scoped=False)

    canonical_dir = project / "runs" / snapshot / "canonical"
    emit_dir = project / "runs" / snapshot / "emit"
    emit_files = emit_excel.emit(canonical_dir, emit_dir)

    dry_client = RecordingDryClient()
    load_result = orion_load.load(
        project, snapshot, dry_client,
        cemetery_name="Acme Synthetic", scoped=False,
    )

    return {
        "project": project,
        "canonical_dir": canonical_dir,
        "emit_dir": emit_dir,
        "emit_files": emit_files,
        "assemble_result": assemble_result,
        "load_result": load_result,
        "dry_client": dry_client,
    }
