"""Stage Delta — classify v2 vs. the prior snapshot (the incremental engine's core).

Joins the current ``source_index.parquet`` to the prior one on ``source_id`` and
classifies every record (operating-model §5.1):

    UNCHANGED  source_id in both, row_hash equal      → zero work; reuse cached output
    CHANGED    source_id in both, row_hash differs     → re-cleanse/assemble that record only
    NEW        source_id only in current               → full pipeline; mint a new external_id
    REMOVED    source_id only in prior                 → never auto-delete; report for judgment

It also detects ``new_columns`` (per table) so Map only re-runs when the schema
actually grew. Output:

    snapshots/<v>/delta.json          # machine artifact (drives scoped cleanse/emit)
    snapshots/<v>/delta_review.md     # the operator reads this first (§5.1)

everspot-brain doc that specifies the rules:
    system-wiki/system/data-migration.md  (§ v1→v2 delta engine)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

VERSION = "1.0.0"

NEW = "NEW"
CHANGED = "CHANGED"
UNCHANGED = "UNCHANGED"
REMOVED = "REMOVED"


@dataclass(slots=True)
class TableDelta:
    table: str
    new: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    new_columns: list[str] = field(default_factory=list)
    removed_columns: list[str] = field(default_factory=list)

    @property
    def counts(self) -> dict[str, int]:
        return {
            NEW: len(self.new),
            CHANGED: len(self.changed),
            UNCHANGED: len(self.unchanged),
            REMOVED: len(self.removed),
        }

    @property
    def needs_attention(self) -> bool:
        """True if Map/Gate-1 may need re-running for this table."""
        return bool(self.new_columns) or bool(self.new) or bool(self.changed)


@dataclass(slots=True)
class DeltaReport:
    current_snapshot: str
    prior_snapshot: Optional[str]
    computed_at: str
    tables: dict[str, TableDelta] = field(default_factory=dict)

    def scoped_source_ids(self) -> list[str]:
        """The CHANGED + NEW set — what cleanse/assemble/emit operate on."""
        ids: list[str] = []
        for td in self.tables.values():
            ids.extend(td.new)
            ids.extend(td.changed)
        return ids

    def to_dict(self) -> dict:
        return {
            "current_snapshot": self.current_snapshot,
            "prior_snapshot": self.prior_snapshot,
            "computed_at": self.computed_at,
            "delta_tool_version": VERSION,
            "tables": {name: asdict(td) for name, td in self.tables.items()},
            "totals": _sum_counts(self.tables.values()),
        }


def _sum_counts(tables) -> dict[str, int]:
    totals = {NEW: 0, CHANGED: 0, UNCHANGED: 0, REMOVED: 0}
    for td in tables:
        for k, v in td.counts.items():
            totals[k] += v
    return totals


def _load_index(path: str | Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if "table" not in df.columns:
        df = df.assign(table="_default")
    return df


def _columns_for_table(idx: pd.DataFrame, table: str) -> set[str]:
    """Raw value columns present for a table (excludes the identity columns)."""
    rows = idx[idx["table"] == table]
    reserved = {"table", "source_id", "row_hash"}
    cols = {c for c in rows.columns if c not in reserved}
    # Drop all-null columns (a table that lacked the column shows NaN under concat).
    return {c for c in cols if rows[c].notna().any()}


def compute_delta(
    current_index_path: str | Path,
    prior_index_path: Optional[str | Path],
    *,
    current_snapshot: str = "v?",
    prior_snapshot: Optional[str] = None,
) -> DeltaReport:
    """Classify the current snapshot against the prior one.

    When ``prior_index_path`` is ``None`` (first drop, v1) every record is NEW.
    """
    cur = _load_index(current_index_path)
    report = DeltaReport(
        current_snapshot=current_snapshot,
        prior_snapshot=prior_snapshot,
        computed_at=datetime.now(timezone.utc).isoformat(),
    )

    if prior_index_path is None:
        for table in sorted(cur["table"].unique()):
            rows = cur[cur["table"] == table]
            report.tables[table] = TableDelta(
                table=table,
                new=rows["source_id"].tolist(),
                new_columns=sorted(_columns_for_table(cur, table)),
            )
        return report

    prior = _load_index(prior_index_path)
    all_tables = sorted(set(cur["table"]).union(set(prior["table"])))

    for table in all_tables:
        cur_t = cur[cur["table"] == table][["source_id", "row_hash"]]
        prior_t = prior[prior["table"] == table][["source_id", "row_hash"]]

        cur_map = dict(zip(cur_t["source_id"], cur_t["row_hash"]))
        prior_map = dict(zip(prior_t["source_id"], prior_t["row_hash"]))

        td = TableDelta(table=table)
        for sid, h in cur_map.items():
            if sid not in prior_map:
                td.new.append(sid)
            elif prior_map[sid] != h:
                td.changed.append(sid)
            else:
                td.unchanged.append(sid)
        for sid in prior_map:
            if sid not in cur_map:
                td.removed.append(sid)

        cur_cols = _columns_for_table(cur, table)
        prior_cols = _columns_for_table(prior, table)
        td.new_columns = sorted(cur_cols - prior_cols)
        td.removed_columns = sorted(prior_cols - cur_cols)

        report.tables[table] = td

    return report


def write_delta(report: DeltaReport, snapshot_dir: str | Path) -> tuple[Path, Path]:
    """Write ``delta.json`` + ``delta_review.md``; return both paths."""
    snap = Path(snapshot_dir)
    snap.mkdir(parents=True, exist_ok=True)

    json_path = snap / "delta.json"
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    md_path = snap / "delta_review.md"
    md_path.write_text(render_delta_review(report), encoding="utf-8")
    return json_path, md_path


def render_delta_review(report: DeltaReport) -> str:
    """The human-readable summary the operator reads first (operating-model §5.1)."""
    totals = _sum_counts(report.tables.values())
    lines: list[str] = []
    lines.append(f"# Delta review — {report.current_snapshot}")
    lines.append("")
    prior = report.prior_snapshot or "(none — first drop)"
    lines.append(f"Compared against: **{prior}**  ·  computed {report.computed_at}")
    lines.append("")
    lines.append(
        f"**Totals:** {totals[NEW]} new · {totals[CHANGED]} changed · "
        f"{totals[UNCHANGED]} unchanged · {totals[REMOVED]} removed."
    )
    lines.append("")

    attention = [td for td in report.tables.values() if td.new_columns or td.removed_columns]
    if attention:
        lines.append("## ⚠ Schema changes (may require re-running Map / Gate 1)")
        lines.append("")
        for td in attention:
            if td.new_columns:
                lines.append(f"- **{td.table}**: new column(s) → `{'`, `'.join(td.new_columns)}`")
            if td.removed_columns:
                lines.append(f"- **{td.table}**: removed column(s) → `{'`, `'.join(td.removed_columns)}`")
        lines.append("")

    lines.append("## Per-table classification")
    lines.append("")
    lines.append("| Table | New | Changed | Unchanged | Removed |")
    lines.append("|---|---:|---:|---:|---:|")
    for name in sorted(report.tables):
        c = report.tables[name].counts
        lines.append(f"| {name} | {c[NEW]} | {c[CHANGED]} | {c[UNCHANGED]} | {c[REMOVED]} |")
    lines.append("")

    removed_tables = [(td.table, td.removed) for td in report.tables.values() if td.removed]
    if removed_tables:
        lines.append("## Disappeared records (operator judgment — never auto-deleted)")
        lines.append("")
        lines.append("These `source_id`s were in the prior drop but not this one. Real deletion?")
        lines.append("Export filter? Re-keyed record? Decide per record — Everspot is never auto-deleted.")
        lines.append("")
        for table, removed in removed_tables:
            preview = ", ".join(removed[:10])
            more = f" … (+{len(removed) - 10} more)" if len(removed) > 10 else ""
            lines.append(f"- **{table}** ({len(removed)}): {preview}{more}")
        lines.append("")

    scoped = len(report.scoped_source_ids())
    lines.append(
        f"> Cleanse/assemble/emit will be **scoped to {scoped} records** (changed + new). "
        "Unchanged records reuse cached output and existing external_ids."
    )
    lines.append("")
    return "\n".join(lines)
