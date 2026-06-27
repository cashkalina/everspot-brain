"""Regression (L3): skipping a BLOCKING question must not silently bypass the gate.

``any_open`` counts only ``still_open``; a ``skipped`` question used to slip past the
"no open questions" gate. That lets a run proceed with a known gap when an operator
skips a BLOCKING ``missing_required`` / ``validation`` question.

Fixes:
  1. A skip REQUIRES an explicit rationale — a skip without one is rejected (the
     question stays OPEN), so skips are always a deliberate, audited act.
  2. The gate surfaces a ``skipped_blocking`` count; ``gate_clear`` is False while it
     is non-zero, so the orchestrator can refuse to proceed.
Skipping a NON-blocking question with a rationale remains allowed.
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


def _fresh(tmp_path: Path) -> tuple[Path, list[dict]]:
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
    py = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8"))
    configs = [
        SourceTableConfig(table=s["table"], source_key=s.get("source_key"),
                          key_status=s.get("key_status", "confirmed"))
        for s in py.get("sources", [])
    ]
    ingest_snapshot(project / "snapshots" / "v1", configs)
    profile_mod.profile_snapshot(project / "snapshots" / "v1")
    return project, list(py.get("sources", []))


def _inject_blocking_question(project: Path) -> str:
    """Append a synthetic BLOCKING (missing_required) open question and return its id."""
    run_dir = project / "runs" / "v1"
    records = json.loads((run_dir / "questions.json").read_text(encoding="utf-8"))
    qid = "q_missing_required__interment.cemetery_id"
    records.append({
        "id": qid, "gate": "exception", "kind": "missing_required",
        "question": "Required field `interment.cemetery_id` has no mapped source column.",
        "proposed_answer": None, "options": [], "allow_custom": True,
        "handoff": "internal", "status": "open",
        "entity": "interment", "field": "cemetery_id",
    })
    (run_dir / "questions.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    return qid


def test_skip_without_rationale_is_rejected(tmp_path):
    project, sources = _fresh(tmp_path)
    discover_mod.discover(project, "v1", sources=sources)
    qid = _inject_blocking_question(project)

    res = answer_mod.apply_answers(project, "v1", answers={qid: "skip"})
    # No rationale -> not skipped; the question stays OPEN.
    assert res.skipped == 0
    assert res.still_open >= 1
    persisted = project / "ledger" / "questions" / f"{qid}.json"
    if persisted.exists():
        rec = json.loads(persisted.read_text(encoding="utf-8"))
        assert rec.get("status") != "skipped"


def test_skipped_blocking_question_is_surfaced_in_gate(tmp_path):
    project, sources = _fresh(tmp_path)
    discover_mod.discover(project, "v1", sources=sources)
    qid = _inject_blocking_question(project)

    res = answer_mod.apply_answers(
        project, "v1",
        answers={qid: {"action": "skip", "rationale": "client confirmed field is N/A"}},
    )
    assert res.skipped == 1
    assert res.skipped_blocking == 1, "a skipped blocking question must be counted"
    assert res.gate_clear is False, "gate must not clear while a blocking question is skipped"


def test_skip_nonblocking_with_rationale_allowed(tmp_path):
    project, sources = _fresh(tmp_path)
    result = discover_mod.discover(project, "v1", sources=sources)
    # Pick an OPEN non-blocking question (unmapped / source_key / entity_merge / value_set).
    nonblocking = next(
        q for q in result.questions
        if q["status"] == "open" and q["kind"] not in ("missing_required", "validation")
    )
    res = answer_mod.apply_answers(
        project, "v1",
        answers={nonblocking["id"]: {"action": "skip", "rationale": "not needed for v1"}},
    )
    assert res.skipped == 1
    assert res.skipped_blocking == 0
