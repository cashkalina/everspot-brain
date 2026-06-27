"""Unit — RUN_LOG.md + MIGRATION_STATUS.md rendering (SPEC §8/§15).

Synthetic only. Asserts the CONSTANT structure: a progress header, one section per phase,
metrics + outputs lines, and the project-status UPSERT (re-running a snapshot updates its
entry rather than duplicating).
"""

from __future__ import annotations

import pytest

import run_log
import run_state


@pytest.fixture(autouse=True)
def _frozen_clock():
    ticks = iter(f"2026-06-27T10:00:{i:02d}+00:00" for i in range(60))
    run_state.set_now(lambda: next(ticks))
    yield
    run_state.set_now(None)


def _seed(run_dir):
    run_state.start_phase(run_dir, "ingest", project="acme", snapshot="v1")
    run_state.finish_phase(run_dir, "ingest",
                           metrics={"total_rows": 100}, outputs=[run_dir / "manifest.json"])
    run_state.start_phase(run_dir, "assemble")
    run_state.finish_phase(run_dir, "assemble",
                           metrics={"entity_counts": {"customer": 90, "property": 100}})


def test_run_log_has_header_and_per_phase_sections(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    _seed(run_dir)
    path = run_log.write_run_log(run_dir)
    text = path.read_text(encoding="utf-8")

    assert path.name == "RUN_LOG.md"
    assert "# Run Log — acme · v1" in text
    assert "**Progress:** 2/13 phases done" in text
    # One section per phase in canonical order; pending phases still appear.
    assert "## ingest — ✅ done" in text
    assert "## assemble — ✅ done" in text
    assert "## delta — · pending" in text
    # Metrics + outputs are rendered for a completed phase.
    assert "**total_rows**: 100" in text
    assert "entity_counts**: customer=90, property=100" in text
    assert "`" + str(run_dir / "manifest.json") + "`" in text


def test_run_log_surfaces_incomplete_load_checkpoint(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    run_state.set_load_checkpoint(run_dir, waves_done=["property_group", "property"],
                                  current_wave="customer", chunks_done=2)
    text = run_log.render_run_log(run_state.load(run_dir))
    assert "Load checkpoint:** INCOMPLETE" in text
    assert "current `customer`" in text


def test_migration_status_upsert_does_not_duplicate(tmp_path):
    project = tmp_path / "acme"
    project.mkdir()
    run_dir = project / "runs" / "v1"
    _seed(run_dir)
    state = run_state.load(run_dir)

    def _entry(snap, counts):
        return run_log.render_status_entry(
            snapshot=snap, state=state, entity_counts=counts,
            validation_gate="PASS", open_questions=0, loaded=False,
            load_status="not yet loaded",
        )

    path = run_log.upsert_migration_status(project, "v1", _entry("v1", {"customer": 90}))
    text = path.read_text(encoding="utf-8")
    assert path.name == "MIGRATION_STATUS.md"
    assert text.count("## v1") == 1
    assert "customer=90" in text

    # Re-run v1 with new counts → entry REPLACED in place, still exactly one ## v1.
    path = run_log.upsert_migration_status(project, "v1", _entry("v1", {"customer": 95}))
    text = path.read_text(encoding="utf-8")
    assert text.count("## v1") == 1
    assert "customer=95" in text
    assert "customer=90" not in text

    # A new snapshot is appended → both entries coexist.
    path = run_log.upsert_migration_status(project, "v2", _entry("v2", {"customer": 200}))
    text = path.read_text(encoding="utf-8")
    assert text.count("## v1") == 1
    assert text.count("## v2") == 1


def test_status_entry_reports_phases_completed(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    _seed(run_dir)
    entry = run_log.render_status_entry(
        snapshot="v1", state=run_state.load(run_dir), entity_counts={"customer": 90},
        validation_gate="FAIL", open_questions=3, loaded=True,
        load_status="loaded (90 created · 0 updated · 0 failed)",
    )
    assert "Phases completed:** 2/13" in entry
    assert "Open questions:** 3" in entry
    assert "❌ FAIL" in entry
    assert "loaded (90 created" in entry
