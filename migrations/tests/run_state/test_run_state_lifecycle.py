"""Unit — run_state.py lifecycle (SPEC §8/§10/§17).

Synthetic only: a bare tmp run dir, no project, no network. Exercises the phase
lifecycle (start/finish/fail/is_done), the load checkpoint, atomic write, deterministic
clock injection, and the progress summary.
"""

from __future__ import annotations

import json

import pytest

import run_state


@pytest.fixture(autouse=True)
def _frozen_clock():
    """Pin the clock so ordering/timestamps are deterministic; restore after."""
    ticks = iter(f"2026-06-27T00:00:{i:02d}+00:00" for i in range(60))
    run_state.set_now(lambda: next(ticks))
    yield
    run_state.set_now(None)


def test_start_finish_lifecycle(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    run_state.start_phase(run_dir, "ingest", project="acme", snapshot="v1")
    assert run_state.phase_status(run_dir, "ingest") == "running"
    assert not run_state.is_done(run_dir, "ingest")

    run_state.finish_phase(run_dir, "ingest",
                           metrics={"total_rows": 42}, outputs=[run_dir / "manifest.json"])
    assert run_state.is_done(run_dir, "ingest")

    state = run_state.load(run_dir)
    assert state["project"] == "acme"
    assert state["snapshot"] == "v1"
    ph = state["phases"]["ingest"]
    assert ph["status"] == "done"
    assert ph["metrics"]["total_rows"] == 42
    assert ph["outputs"] == [str(run_dir / "manifest.json")]
    assert ph["started_at"] and ph["finished_at"]
    assert ph["error"] is None


def test_fail_phase_records_error_and_not_done(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    run_state.start_phase(run_dir, "assemble")
    run_state.fail_phase(run_dir, "assemble", "ValueError: bad ref")
    assert not run_state.is_done(run_dir, "assemble")
    state = run_state.load(run_dir)
    assert state["phases"]["assemble"]["status"] == "failed"
    assert "bad ref" in state["phases"]["assemble"]["error"]


def test_load_returns_skeleton_when_missing(tmp_path):
    state = run_state.load(tmp_path / "runs" / "nope")
    assert state["phases"] == {}
    assert state["load_checkpoint"] == {}


def test_atomic_write_produces_valid_json(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    run_state.start_phase(run_dir, "ingest")
    path = run_state.state_path(run_dir)
    # File parses + no leftover tmp files.
    json.loads(path.read_text(encoding="utf-8"))
    leftovers = list(run_dir.glob(".run_state-*.tmp"))
    assert leftovers == []


def test_load_checkpoint_partial_updates(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    run_state.set_load_checkpoint(run_dir, waves_done=["property_group"], current_wave="property")
    run_state.set_load_checkpoint(run_dir, chunks_done=3)  # must NOT clobber waves_done
    cp = run_state.get_load_checkpoint(run_dir)
    assert cp["waves_done"] == ["property_group"]
    assert cp["current_wave"] == "property"
    assert cp["chunks_done"] == 3
    assert not cp.get("complete")

    run_state.set_load_checkpoint(run_dir, waves_done=["property_group", "property"], complete=True)
    cp = run_state.get_load_checkpoint(run_dir)
    assert cp["complete"] is True
    assert cp["current_wave"] is None  # finalize clears the current wave


def test_progress_counts_done_over_canonical_order(tmp_path):
    run_dir = tmp_path / "runs" / "v1"
    run_state.start_phase(run_dir, "ingest")
    run_state.finish_phase(run_dir, "ingest", metrics={})
    run_state.start_phase(run_dir, "assemble")
    run_state.finish_phase(run_dir, "assemble", metrics={})
    state = run_state.load(run_dir)
    prog = run_state.progress(state)
    assert prog["done"] == 2
    assert prog["total"] == len(run_state.PHASE_ORDER)
    assert prog["phases"][:2] == ["ingest", "delta"]  # canonical order, not insertion order
