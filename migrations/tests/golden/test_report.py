"""Tests (SPEC §12 / §15.2) — the runnable `report` stage (§8 stage 12).

Runs the deterministic spine on the SYNTHETIC ``acme_synth`` fixture, then validates +
synthesizes a small questionnaire + a needs_attention assemble report, then asserts that
``migrate report`` assembles a faithful ``REPORT.md`` *from the artifacts* (it must read
the numbers, never invent them) and guarantees ``needs_attention.json`` at the run root.

No client data, no network, no LLM.
"""

import json
import sys
from pathlib import Path

import pytest

GOLDEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GOLDEN))

from spine import run_spine  # noqa: E402

import report as report_mod  # noqa: E402
import validate as validate_mod  # noqa: E402


@pytest.fixture(scope="module")
def reported(tmp_path_factory):
    """Spine → validate → synthetic questions/needs_attention → report. Returns paths + text."""
    dest = tmp_path_factory.mktemp("report")
    spine = run_spine("acme_synth", dest)
    project = spine["project"]
    run_dir = project / "runs" / "v1"

    # Validation summary (the conservation table + PASS gate the report restates).
    validate_mod.validate_run(project, "v1")

    # A settled questionnaire: 2 auto-resolved + 1 answered (mirrors a real run shape).
    questions = [
        {"id": "q_value_set__color", "kind": "value_set", "status": "auto-resolved",
         "question": "Column `color` resolved cleanly.", "proposed_answer": {"R": 1}, "answer": {"R": 1}},
        {"id": "q_missing_required__customer.status", "kind": "missing_required",
         "status": "auto-resolved", "question": "Default customer.status active?",
         "proposed_answer": "active", "answer": "active"},
        {"id": "q_source_key__register", "kind": "source_key", "status": "answered",
         "question": "Which column is the key?", "proposed_answer": "acct", "answer": "acct"},
    ]
    (run_dir / "questions.json").write_text(json.dumps(questions), encoding="utf-8")

    # A small needs_attention block on the assemble report (grouped-by-kind surface).
    report_path = run_dir / "canonical" / "assemble_report.json"
    ar = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    ar["needs_attention"] = [
        {"kind": "data_quality", "table": "register", "source_id": "register:1",
         "detail": "dob out-of-range; dropped to null", "context": {}},
        {"kind": "data_quality", "table": "register", "source_id": "register:2",
         "detail": "dod out-of-range; dropped to null", "context": {}},
        {"kind": "missing_required", "table": "register", "source_id": "register:3",
         "detail": "last_name absent; defaulted to UNKNOWN", "context": {}},
    ]
    report_path.write_text(json.dumps(ar), encoding="utf-8")

    result = report_mod.build_report(project, "v1")
    return {
        "project": project,
        "run_dir": run_dir,
        "result": result,
        "text": (run_dir / "REPORT.md").read_text(encoding="utf-8"),
    }


def test_report_md_written(reported):
    assert reported["result"]["report_path"].exists()
    assert (reported["run_dir"] / "REPORT.md").exists()


def test_report_has_conservation_table(reported):
    text = reported["text"]
    assert "## Count conservation" in text
    assert "| Entity | Source rows | Canonical | Loaded | Dropped | Conserved |" in text
    # acme_synth golden: 3 customers / 3 interments / 3 properties / 1 group.
    assert "| customer | 3 | 3 |" in text
    assert "| interment | 3 | 3 |" in text
    assert "| property | 3 | 3 |" in text


def test_report_has_question_summary(reported):
    text = reported["text"]
    assert "## The questionnaire answered" in text
    assert "0 open · 2 auto-resolved · 1 answered · 0 skipped" in text


def test_report_has_validation_line(reported):
    text = reported["text"]
    assert "## Validation result" in text
    assert "PASS" in text
    # Headline verdict line restates the gate + open-question count from artifacts.
    assert "**Validation:** ✅ PASS" in text
    assert "**Open questions:** 0" in text


def test_report_shows_loaded_counts(reported):
    text = reported["text"]
    assert "## What loaded per entity" in text
    assert "| Entity | Created | Updated | Skipped | Failed |" in text


def test_report_groups_data_quality_flags(reported):
    text = reported["text"]
    assert "## Data-quality flags" in text
    assert "| data_quality | 2 |" in text
    assert "| missing_required | 1 |" in text


def test_needs_attention_json_exists_at_run_root(reported):
    na_path = reported["run_dir"] / "needs_attention.json"
    assert na_path.exists()
    payload = json.loads(na_path.read_text(encoding="utf-8"))
    assert payload["total"] == 3
    assert payload["by_kind"] == {"data_quality": 2, "missing_required": 1}
    assert set(payload["items_by_kind"]) == {"data_quality", "missing_required"}


def test_report_conservation_numbers_come_from_artifacts(reported):
    """The report must not invent counts — they match validation_summary.json exactly."""
    val = json.loads(
        (reported["run_dir"] / "validation" / "validation_summary.json").read_text(encoding="utf-8")
    )
    for row in val["count_conservation"]:
        line = f"| {row['entity']} | {row['source_rows']} | {row['canonical_records']} |"
        assert line in reported["text"]
