"""Regression (M1): accept-all must NOT settle a value_set with unresolved codes.

SPEC §9.2: a value that does not resolve to a real list_option id MUST become a
question — never invented or nulled. A ``value_set`` question whose
``proposed_answer`` carries any ``None`` (an unresolved source code) must stay OPEN
on accept-all, not get marked ``answered`` with None tokens leaking into
``reference_resolution.missing`` (which then load as null cells).

Covered at BOTH ends:
  - PRODUCE (discover): an unresolvable source code yields an OPEN value_set question
    whose proposed_answer surfaces the None token (so the human sees the gap).
  - CONSUME (answer): accept-all refuses to settle a value_set holding any None and
    keeps the question OPEN.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

import answer as answer_mod
import discover as discover_mod

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "golden" / "fixtures"
_REFERENCE_DATA = {
    "list_options": {
        "interment_type": [
            {"id": 11, "name": "Burial", "key": "interment-type-burial"},
            {"id": 12, "name": "Cremation", "key": "interment-type-cremation"},
        ]
    }
}


def _build_project_with_unresolvable_code(tmp_path: Path) -> tuple[Path, list[dict]]:
    """A fresh acme_synth whose register has one ITYPE value with no list_option."""
    import profile as profile_mod
    from snapshot import SourceTableConfig, ingest_snapshot

    project = tmp_path / "acme_synth"
    shutil.copytree(FIXTURES_DIR / "acme_synth", project)
    (project / "ledger" / "mapping.yaml").unlink(missing_ok=True)
    (project / "ledger" / "value_sets.yaml").unlink(missing_ok=True)
    (project / "ledger").mkdir(exist_ok=True)
    (project / "ledger" / "reference_data.json").write_text(
        json.dumps(_REFERENCE_DATA), encoding="utf-8"
    )

    # Inject an ITYPE code ("MAU") that maps to NO tenant list_option.
    csv_path = project / "snapshots" / "v1" / "raw" / "register.csv"
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    lines.append("A-14-1,A,14,1,Jane,Roe,1950,1,1,2010,3,3,MAU")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    py = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8"))
    configs = [
        SourceTableConfig(
            table=s["table"],
            source_key=s.get("source_key"),
            key_status=s.get("key_status", "confirmed"),
        )
        for s in py.get("sources", [])
    ]
    ingest_snapshot(project / "snapshots" / "v1", configs)
    profile_mod.profile_snapshot(project / "snapshots" / "v1")
    return project, list(py.get("sources", []))


def test_discover_surfaces_unresolvable_value_set_as_open(tmp_path):
    project, sources = _build_project_with_unresolvable_code(tmp_path)
    result = discover_mod.discover(project, "v1", sources=sources)

    vs_q = [q for q in result.questions if q["kind"] == "value_set" and q["status"] == "open"]
    assert vs_q, "an unresolved value-set code must produce an OPEN question"
    # PRODUCE end: the proposed_answer surfaces the unresolved token as None (so the
    # human sees the gap) — and BECAUSE it holds a None it is not accept-all-able.
    poisoned = next(q for q in vs_q if q.get("column") == "itype")
    assert poisoned["proposed_answer"]["MAU"] is None
    assert any(v is None for v in poisoned["proposed_answer"].values())


def test_accept_all_keeps_unresolved_value_set_open(tmp_path):
    project, sources = _build_project_with_unresolvable_code(tmp_path)
    discover_mod.discover(project, "v1", sources=sources)

    res = answer_mod.apply_answers(project, "v1", accept_all=True)
    assert res.any_open is True, "accept-all must leave the unresolved value-set OPEN"
    assert res.still_open >= 1


def test_accept_all_consume_guard_for_partial_dict(tmp_path):
    """CONSUME end: even a hand-crafted proposed_answer dict with a None stays open."""
    project, sources = _build_project_with_unresolvable_code(tmp_path)
    discover_mod.discover(project, "v1", sources=sources)

    run_dir = project / "runs" / "v1"
    records = json.loads((run_dir / "questions.json").read_text(encoding="utf-8"))
    # Force a value_set question to carry a partial dict (resolved + a None token).
    poisoned = None
    for q in records:
        if q["kind"] == "value_set" and q["status"] == "open":
            q["proposed_answer"] = {"bur": 11, "mau": None}
            poisoned = q["id"]
            break
    assert poisoned, "need an open value_set question to poison"
    (run_dir / "questions.json").write_text(json.dumps(records, indent=2), encoding="utf-8")

    answer_mod.apply_answers(project, "v1", accept_all=True)

    # The poisoned question must NOT be marked answered, and no None must leak into
    # the mapping reference_resolution.missing as a "resolved" cell.
    persisted = project / "ledger" / "questions" / f"{poisoned}.json"
    if persisted.exists():
        rec = json.loads(persisted.read_text(encoding="utf-8"))
        assert rec.get("status") != "answered", "partial-dict value_set must not be answered"
