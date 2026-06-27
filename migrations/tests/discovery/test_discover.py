"""The single question round tests (SPEC §9).

Asserts: question records conform to question.schema.json; proposed_answer is always
present; ask-policy routing (clean value-set -> auto-resolved; unresolvable -> open
value_set; missing source_key -> source_key question). All synthetic.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
import yaml

import discover as discover_mod

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "schemas" / "question.schema.json"


@pytest.fixture(scope="module")
def question_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _run_discover(project, project_sources):
    return discover_mod.discover(project, "v1", sources=project_sources(project))


def test_question_records_conform_to_schema(fresh_acme, project_sources, question_schema):
    result = _run_discover(fresh_acme, project_sources)
    assert result.questions, "discovery should produce at least one question"
    for q in result.questions:
        jsonschema.validate(q, question_schema)


def test_proposed_answer_always_present(fresh_acme, project_sources):
    result = _run_discover(fresh_acme, project_sources)
    for q in result.questions:
        assert "proposed_answer" in q, f"{q['id']} missing proposed_answer (breaks accept-all)"


def test_stable_subject_derived_ids(fresh_acme, project_sources):
    """Re-running discovery yields the SAME ids (subject-derived, not run position)."""
    r1 = _run_discover(fresh_acme, project_sources)
    r2 = _run_discover(fresh_acme, project_sources)
    assert [q["id"] for q in r1.questions] == [q["id"] for q in r2.questions]
    for q in r1.questions:
        assert q["id"].startswith("q_")


def test_clean_value_set_is_auto_resolved(fresh_acme, project_sources):
    result = _run_discover(fresh_acme, project_sources)
    vs = [q for q in result.questions if q["kind"] == "value_set"]
    assert vs, "expected a value_set question"
    # ITYPE resolved cleanly -> recorded default (auto-resolved), not asked.
    itype = next(q for q in vs if q.get("column") == "itype")
    assert itype["status"] == "auto-resolved"
    assert itype["answer"] == {"BUR": 11, "CRE": 12}


def test_unresolvable_value_set_is_open_question(fresh_acme, project_sources):
    # Poison the reference data so CRE no longer resolves.
    ref = fresh_acme / "ledger" / "reference_data.json"
    ref.write_text(json.dumps({"list_options": {"interment_type": [
        {"id": 11, "name": "Burial", "key": "interment-type-burial"},
    ]}}), encoding="utf-8")

    result = _run_discover(fresh_acme, project_sources)
    itype = next(q for q in result.questions if q.get("column") == "itype")
    assert itype["kind"] == "value_set"
    assert itype["status"] == "open"
    # The unresolved code is surfaced; resolved ones keep their real id; none invented.
    assert itype["proposed_answer"]["CRE"] is None
    assert itype["proposed_answer"]["BUR"] == 11


def test_missing_source_key_becomes_a_question(fresh_acme, project_sources):
    # Deferred source_key -> a source_key question (§9.2).
    proj_path = fresh_acme / "project.yaml"
    proj = yaml.safe_load(proj_path.read_text(encoding="utf-8"))
    for s in proj["sources"]:
        s.pop("source_key", None)
        s["key_status"] = "deferred"
    proj_path.write_text(yaml.safe_dump(proj), encoding="utf-8")

    sources = proj["sources"]
    result = discover_mod.discover(fresh_acme, "v1", sources=sources)
    src_q = [q for q in result.questions if q["kind"] == "source_key"]
    assert src_q, "a deferred source_key must surface a source_key question"
    assert src_q[0]["status"] == "open"
    # It proposes candidate key columns rather than guessing silently.
    assert src_q[0].get("options")


def test_any_open_signal_for_orchestrator_gate(fresh_acme, project_sources):
    result = _run_discover(fresh_acme, project_sources)
    # The fresh fixture leaves the entity-routing question open -> orchestrator gate trips.
    assert result.any_open == (result.open_count > 0)
    assert result.open_count >= 1
