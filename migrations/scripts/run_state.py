"""Run-state checkpointing — the machine-readable per-run progress record (SPEC §8, §10, §17).

Every runnable stage writes a structured checkpoint into ``runs/<v>/run_state.json`` so a
run has a constant, auditable progress record. The §17 "resumable/checkpointed load" is
implemented at the LOAD stage: an incomplete ``load_checkpoint`` is resumed at WAVE
granularity (see :mod:`orion_load`). For the other stages this file is an auditable
status/metrics record, not an auto-skip resume engine: :func:`is_done` exposes per-phase
``status:done`` so an orchestrator (or a future ``--resume`` flag) CAN choose to skip a
completed phase, but ``migrate.py``'s stage handlers do NOT auto-skip today — re-running a
stage re-executes it (its outputs are deterministic/idempotent). Only the load stage
self-resumes from its checkpoint.

Shape (``runs/<v>/run_state.json``)::

    { "schema_version": 1,
      "project": "<slug>", "snapshot": "v1", "updated_at": "<iso>",
      "phases": {
        "<phase>": { "status": "pending|running|done|failed",
                     "started_at": ..., "finished_at": ...,
                     "metrics": {..}, "outputs": [..], "error": null } },
      "load_checkpoint": { "waves_done": [...], "current_wave": "...",
                           "complete": false } }
      # (a deprecated informational `chunks_done` may be present from older readers;
      #  it does NOT drive resume — resume is wave-level. See set_load_checkpoint.)

Design notes:
- **Dependency-light** — stdlib + json only (no pandas/yaml import here).
- **Atomic write** — tmp file + ``os.replace`` so a crash mid-write never corrupts state.
- **Deterministic "now"** — all timestamps go through :func:`_now`, overridable via
  :func:`set_now` so tests can freeze time. The venv has no time constraint; tests tolerate
  any ISO string but pin it when they assert ordering.
- **General only** — no client column names; keyed by phase + wave (general concepts).
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

VERSION = "1.0.0"
SCHEMA_VERSION = 1

STATE_FILENAME = "run_state.json"

# Canonical phase order (SPEC §8 stage flow) — drives RUN_LOG.md section ordering and the
# "N/13 phases" progress header. The runnable stages only (acquire/intake are AI/manual).
PHASE_ORDER: tuple[str, ...] = (
    "ingest",
    "delta",
    "profile",
    "map-draft",
    "discover",
    "answer",
    "validate",
    "assemble",
    "cleanse",
    "emit",
    "load",
    "reconcile",
    "report",
)

_STATUS_PENDING = "pending"
_STATUS_RUNNING = "running"
_STATUS_DONE = "done"
_STATUS_FAILED = "failed"


# --------------------------------------------------------------------------- #
# Deterministic "now" (test-injectable)                                        #
# --------------------------------------------------------------------------- #
_now_fn: Callable[[], str] = lambda: datetime.now(timezone.utc).isoformat()


def _now() -> str:
    return _now_fn()


def set_now(fn: Optional[Callable[[], str]]) -> None:
    """Override the clock (tests). Pass ``None`` to restore the real UTC clock."""
    global _now_fn
    _now_fn = fn or (lambda: datetime.now(timezone.utc).isoformat())


# --------------------------------------------------------------------------- #
# Path + IO                                                                    #
# --------------------------------------------------------------------------- #
def state_path(run_dir: str | Path) -> Path:
    return Path(run_dir) / STATE_FILENAME


def _new_state(project: str, snapshot: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "project": project,
        "snapshot": snapshot,
        "updated_at": _now(),
        "phases": {},
        "load_checkpoint": {},
    }


def load(run_dir: str | Path) -> dict:
    """Read ``run_state.json`` for a run, or an empty skeleton if it doesn't exist yet."""
    path = state_path(run_dir)
    if not path.exists():
        return _new_state(project="", snapshot=Path(run_dir).name)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return _new_state(project="", snapshot=Path(run_dir).name)
    data.setdefault("phases", {})
    data.setdefault("load_checkpoint", {})
    data.setdefault("schema_version", SCHEMA_VERSION)
    return data


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".run_state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save(run_dir: str | Path, state: dict) -> Path:
    state["updated_at"] = _now()
    path = state_path(run_dir)
    _atomic_write(path, state)
    return path


# --------------------------------------------------------------------------- #
# Phase lifecycle                                                              #
# --------------------------------------------------------------------------- #
def _phase(state: dict, phase: str) -> dict:
    return state["phases"].setdefault(
        phase,
        {
            "status": _STATUS_PENDING,
            "started_at": None,
            "finished_at": None,
            "metrics": {},
            "outputs": [],
            "error": None,
        },
    )


def start_phase(run_dir: str | Path, phase: str, *, project: str = "", snapshot: str = "") -> dict:
    """Mark a phase ``running`` (records ``started_at``); creates the state file if absent."""
    state = load(run_dir)
    if project and not state.get("project"):
        state["project"] = project
    if snapshot and not state.get("snapshot"):
        state["snapshot"] = snapshot
    ph = _phase(state, phase)
    ph["status"] = _STATUS_RUNNING
    ph["started_at"] = _now()
    ph["finished_at"] = None
    ph["error"] = None
    save(run_dir, state)
    return state


def finish_phase(
    run_dir: str | Path,
    phase: str,
    metrics: Optional[dict] = None,
    outputs: Optional[list] = None,
) -> dict:
    """Mark a phase ``done`` with its real metrics + output artifact paths."""
    state = load(run_dir)
    ph = _phase(state, phase)
    ph["status"] = _STATUS_DONE
    ph["finished_at"] = _now()
    ph["error"] = None
    if metrics is not None:
        ph["metrics"] = metrics
    if outputs is not None:
        ph["outputs"] = [str(o) for o in outputs]
    save(run_dir, state)
    return state


def fail_phase(run_dir: str | Path, phase: str, error: str) -> dict:
    """Mark a phase ``failed`` with the error string (so a resume knows to retry it)."""
    state = load(run_dir)
    ph = _phase(state, phase)
    ph["status"] = _STATUS_FAILED
    ph["finished_at"] = _now()
    ph["error"] = str(error)[:2000]
    save(run_dir, state)
    return state


def is_done(run_dir: str | Path, phase: str) -> bool:
    """True iff ``phase`` has completed successfully (``status:done``).

    Available for an orchestrator / a future ``--resume`` flag to skip a finished phase;
    note that ``migrate.py``'s stage handlers do NOT call this to auto-skip today (only the
    load stage self-resumes from its own checkpoint). It is purely a status predicate.
    """
    state = load(run_dir)
    return state["phases"].get(phase, {}).get("status") == _STATUS_DONE


def phase_status(run_dir: str | Path, phase: str) -> str:
    state = load(run_dir)
    return state["phases"].get(phase, {}).get("status", _STATUS_PENDING)


# --------------------------------------------------------------------------- #
# Load checkpoint (the §17 resumable load)                                     #
# --------------------------------------------------------------------------- #
def set_load_checkpoint(
    run_dir: str | Path,
    *,
    waves_done: Optional[list] = None,
    current_wave: Optional[str] = None,
    chunks_done: Optional[int] = None,
    complete: Optional[bool] = None,
) -> dict:
    """Record load progress (WAVE-by-wave) for crash-recovery resume.

    Resume is WAVE-LEVEL: each wave is recorded as it completes (``waves_done``) and the
    one in flight is named (``current_wave``). A re-run skips completed waves and re-runs
    the interrupted one in full — safe because the load is idempotent (upsert-by-external_id
    + orphan repair). Only the supplied fields are updated, so a progress write doesn't
    clobber the accumulated ``waves_done``. ``complete=True`` finalizes (clears
    ``current_wave``).

    ``chunks_done`` is DEPRECATED and does NOT drive resume — it is retained only as an
    informational counter for back-compat with existing display/state readers. The loader
    no longer writes it (mid-wave chunk resume was never wired; the honest contract is
    wave-level). Do not rely on it for resume decisions.
    """
    state = load(run_dir)
    cp = state.setdefault("load_checkpoint", {})
    if waves_done is not None:
        cp["waves_done"] = list(waves_done)
    if current_wave is not None:
        cp["current_wave"] = current_wave
    if chunks_done is not None:
        cp["chunks_done"] = int(chunks_done)
    if complete is not None:
        cp["complete"] = bool(complete)
        if complete:
            cp["current_wave"] = None
    save(run_dir, state)
    return state


def get_load_checkpoint(run_dir: str | Path) -> dict:
    """Return the load checkpoint (``{}`` if none yet)."""
    return load(run_dir).get("load_checkpoint", {}) or {}


def clear_load_checkpoint(run_dir: str | Path) -> dict:
    state = load(run_dir)
    state["load_checkpoint"] = {}
    save(run_dir, state)
    return state


# --------------------------------------------------------------------------- #
# Progress summary (for RUN_LOG.md / MIGRATION_STATUS.md / CLI)               #
# --------------------------------------------------------------------------- #
def progress(state: dict) -> dict:
    """Compute ``{done, total, phases:[...]}`` over the canonical phase order.

    ``total`` counts only the phases that exist in PHASE_ORDER; ``done`` counts those whose
    status is ``done``. Phases recorded but not in the canonical order are appended after.
    """
    phases = state.get("phases", {})
    done = sum(1 for p in PHASE_ORDER if phases.get(p, {}).get("status") == _STATUS_DONE)
    ordered = [p for p in PHASE_ORDER]
    ordered += [p for p in phases if p not in PHASE_ORDER]
    return {
        "done": done,
        "total": len(PHASE_ORDER),
        "phases": ordered,
    }
