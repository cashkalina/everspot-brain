"""Fixtures for the auto-draft + question-round tests (SPEC §8 stage 5, §9).

All inputs are SYNTHETIC (the ``acme_synth`` golden fixture) — no client data, no
network, no LLM, no live Laravel. A fresh copy of the fixture is made per test with
its SETTLED ledger removed, so map-draft / discover run from scratch.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "golden" / "fixtures"

# A minimal synthetic tenant reference snapshot so value-set resolution has options.
_REFERENCE_DATA = {
    "list_options": {
        "interment_type": [
            {"id": 11, "name": "Burial", "key": "interment-type-burial"},
            {"id": 12, "name": "Cremation", "key": "interment-type-cremation"},
        ]
    }
}


def _source_configs(project_dir: Path):
    from snapshot import SourceTableConfig

    py = yaml.safe_load((project_dir / "project.yaml").read_text(encoding="utf-8"))
    return [
        SourceTableConfig(
            table=s["table"],
            source_key=s.get("source_key"),
            key_status=s.get("key_status", "confirmed"),
        )
        for s in py.get("sources", [])
    ]


@pytest.fixture
def fresh_acme(tmp_path: Path) -> Path:
    """A fresh acme_synth project WITHOUT its settled ledger, ingested + profiled.

    Returns the project dir, ready for ``map-draft`` / ``discover``.
    """
    import profile as profile_mod
    from snapshot import ingest_snapshot

    project = tmp_path / "acme_synth"
    shutil.copytree(FIXTURES_DIR / "acme_synth", project)
    # Drop the settled ledger so the drafter works from scratch.
    (project / "ledger" / "mapping.yaml").unlink(missing_ok=True)
    (project / "ledger" / "value_sets.yaml").unlink(missing_ok=True)
    (project / "ledger").mkdir(exist_ok=True)
    (project / "ledger" / "reference_data.json").write_text(
        json.dumps(_REFERENCE_DATA), encoding="utf-8"
    )

    ingest_snapshot(project / "snapshots" / "v1", _source_configs(project))
    profile_mod.profile_snapshot(project / "snapshots" / "v1")
    return project


@pytest.fixture
def project_sources():
    def _load(project: Path):
        py = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8"))
        return list(py.get("sources", []))

    return _load
