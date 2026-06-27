"""RUN_LOG.md + project MIGRATION_STATUS.md renderers (SPEC §8, §15).

Two human-readable, **constant-format** surfaces derived from ``run_state.json`` (+ a few
run artifacts the report already aggregates):

- ``runs/<v>/RUN_LOG.md`` — one section per phase (status · timing · key metrics · outputs)
  plus a header line (overall progress, last updated). Rendered by ``migrate status`` and
  refreshed automatically at the end of the ``report`` stage.
- ``<project>/MIGRATION_STATUS.md`` — one structured entry per snapshot run, UPSERTED by
  snapshot (re-running v1 updates its entry, never duplicates). One scannable line-block per
  run: phases completed (N/13) · final entity counts · load status · open questions ·
  validation PASS/FAIL.

Both formats are STABLE and scannable so they stay diff-friendly across runs. General only
— no client column names; entity names + phase names are general pipeline concepts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import run_state

VERSION = "1.0.0"

_STATUS_MARK = {
    "done": "✅",
    "running": "🔄",
    "failed": "❌",
    "pending": "·",
}


def _fmt_metric_value(value: Any) -> str:
    if isinstance(value, dict):
        if not value:
            return "{}"
        return ", ".join(f"{k}={v}" for k, v in value.items())
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _short(ts: Optional[str]) -> str:
    """Trim an ISO timestamp to seconds for compact display (tolerant of any string)."""
    if not ts:
        return "—"
    return str(ts).split(".")[0].replace("T", " ")


# --------------------------------------------------------------------------- #
# RUN_LOG.md                                                                   #
# --------------------------------------------------------------------------- #
def render_run_log(state: dict) -> str:
    prog = run_state.progress(state)
    lines: list[str] = []
    lines.append(f"# Run Log — {state.get('project') or '(project)'} · {state.get('snapshot') or '?'}")
    lines.append("")
    lines.append(
        f"**Progress:** {prog['done']}/{prog['total']} phases done  ·  "
        f"**Last updated:** {_short(state.get('updated_at'))}"
    )
    cp = state.get("load_checkpoint") or {}
    if cp:
        if cp.get("complete"):
            lines.append(f"**Load checkpoint:** complete · waves {cp.get('waves_done', [])}")
        else:
            lines.append(
                f"**Load checkpoint:** INCOMPLETE · done {cp.get('waves_done', [])} · "
                f"current `{cp.get('current_wave')}` · chunks {cp.get('chunks_done', 0)} "
                "(a re-run resumes here)"
            )
    lines.append("")

    phases = state.get("phases", {})
    for phase in prog["phases"]:
        ph = phases.get(phase)
        if not ph:
            lines.append(f"## {phase} — · pending")
            lines.append("")
            continue
        status = ph.get("status", "pending")
        mark = _STATUS_MARK.get(status, "·")
        lines.append(f"## {phase} — {mark} {status}")
        timing = f"started {_short(ph.get('started_at'))} · finished {_short(ph.get('finished_at'))}"
        lines.append(timing)
        metrics = ph.get("metrics") or {}
        if metrics:
            lines.append("")
            for key, value in metrics.items():
                lines.append(f"- **{key}**: {_fmt_metric_value(value)}")
        if ph.get("error"):
            lines.append("")
            lines.append(f"- **error**: {ph['error']}")
        outputs = ph.get("outputs") or []
        if outputs:
            lines.append("")
            lines.append("Outputs: " + ", ".join(f"`{o}`" for o in outputs))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_run_log(run_dir: str | Path, state: Optional[dict] = None) -> Path:
    run_dir = Path(run_dir)
    if state is None:
        state = run_state.load(run_dir)
    out = run_dir / "RUN_LOG.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_run_log(state), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Project MIGRATION_STATUS.md (one entry per snapshot, upserted)               #
# --------------------------------------------------------------------------- #
_ENTRY_HEADER_RE = re.compile(r"^## (?P<snap>\S+)\b", re.MULTILINE)


def render_status_entry(
    *,
    snapshot: str,
    state: dict,
    entity_counts: dict[str, int],
    validation_gate: str,
    open_questions: int,
    loaded: bool,
    load_status: str,
) -> str:
    prog = run_state.progress(state)
    counts = ", ".join(f"{e}={n}" for e, n in entity_counts.items()) if entity_counts else "—"
    gate_mark = {"PASS": "✅", "FAIL": "❌"}.get(validation_gate, "—")
    lines = [
        f"## {snapshot}",
        "",
        f"- **Date:** {_short(state.get('updated_at'))}",
        f"- **Phases completed:** {prog['done']}/{prog['total']}",
        f"- **Final entity counts:** {counts}",
        f"- **Load:** {load_status}",
        f"- **Open questions:** {open_questions}",
        f"- **Validation:** {gate_mark} {validation_gate}",
        "",
    ]
    return "\n".join(lines)


def upsert_migration_status(
    project_root: str | Path,
    snapshot: str,
    entry_md: str,
) -> Path:
    """UPSERT the snapshot's entry into ``<project>/MIGRATION_STATUS.md`` (no duplicates).

    Entries are ``## <snapshot>`` blocks; re-running a snapshot replaces its block in place
    (keeping document order). A brand-new snapshot is appended after the existing ones.
    """
    root = Path(project_root)
    path = root / "MIGRATION_STATUS.md"
    header = f"# Migration Status — {root.name}\n\nOne entry per snapshot run (upserted; latest state per drop).\n"

    if not path.exists():
        path.write_text(header + "\n" + entry_md.rstrip() + "\n", encoding="utf-8")
        return path

    text = path.read_text(encoding="utf-8")
    matches = list(_ENTRY_HEADER_RE.finditer(text))
    target = next((m for m in matches if m.group("snap") == snapshot), None)

    if target is None:
        new_text = text.rstrip() + "\n\n" + entry_md.rstrip() + "\n"
        path.write_text(new_text, encoding="utf-8")
        return path

    # Replace from this entry's "## <snap>" up to the next "## " (or EOF).
    start = target.start()
    next_match = next((m for m in matches if m.start() > start), None)
    end = next_match.start() if next_match else len(text)
    new_text = text[:start] + entry_md.rstrip() + "\n\n" + text[end:]
    path.write_text(new_text.rstrip() + "\n", encoding="utf-8")
    return path
