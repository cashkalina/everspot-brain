"""Stage 0 — Ingest. Raw source files → normalized parquet tables + source_index.

Accepts csv / xlsx (one sheet → one table) via pandas, normalizes column names,
computes identity (``source_id``/``row_hash``) per :mod:`identity`, and writes:

    snapshots/<v>/tables/<table>.parquet      # normalized table + identity cols
    snapshots/<v>/source_index.parquet        # the delta engine's only input
    snapshots/<v>/manifest.json               # files, sheets, row counts (review artifact)

Raw bytes under ``snapshots/<v>/raw/`` are treated as immutable — we only read.

Design references:
    - operating-model §3 stage 0, §2 (identity at ingest)
    - plan §3 stage 0 (intake & normalization), §4 (review artifact = manifest.json)

everspot-brain doc that specifies the rules:
    system-wiki/system/data-migration.md  (§ intake & normalization)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

import pandas as pd

from identity import (
    KEY_STATUS_COL,
    build_source_index,
    compute_identity,
)

VERSION = "1.0.0"

_CSV_EXTS = {".csv", ".tsv"}
_EXCEL_EXTS = {".xlsx", ".xls", ".xlsm"}


@dataclass(slots=True)
class SourceTableConfig:
    """Per-table config pulled from ``project.yaml`` ``sources[]``.

    See ``schemas/project.schema.json``.
    """

    table: str
    source_key: Optional[Sequence[str]] = None
    key_status: str = "confirmed"
    key_columns: Optional[Sequence[str]] = None
    description: str = ""


def normalize_column_name(name: str) -> str:
    """Lower, trim, collapse whitespace/punctuation to single underscores."""
    text = str(name).strip().lower()
    text = re.sub(r"[^\w]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_") or "col"


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply :func:`normalize_column_name`, de-duplicating collisions."""
    seen: dict[str, int] = {}
    new_cols: list[str] = []
    for c in df.columns:
        base = normalize_column_name(c)
        if base in seen:
            seen[base] += 1
            new_cols.append(f"{base}_{seen[base]}")
        else:
            seen[base] = 0
            new_cols.append(base)
    out = df.copy()
    out.columns = new_cols
    return out


def _read_file(path: Path) -> dict[str, pd.DataFrame]:
    """Read one source file → ``{table_name: dataframe}`` (xlsx → one per sheet)."""
    ext = path.suffix.lower()
    if ext in _CSV_EXTS:
        sep = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(path, sep=sep, dtype=str, keep_default_na=True)
        return {normalize_column_name(path.stem): df}
    if ext in _EXCEL_EXTS:
        sheets = pd.read_excel(path, sheet_name=None, dtype=str)
        out: dict[str, pd.DataFrame] = {}
        for sheet_name, df in sheets.items():
            table = normalize_column_name(f"{path.stem}_{sheet_name}") if len(sheets) > 1 else normalize_column_name(path.stem)
            out[table] = df
        return out
    raise ValueError(f"unsupported source file type: {path.name} ({ext})")


@dataclass(slots=True)
class IngestResult:
    snapshot_dir: Path
    tables: dict[str, int] = field(default_factory=dict)  # table -> row count
    manifest_path: Optional[Path] = None
    source_index_path: Optional[Path] = None


def ingest_snapshot(
    snapshot_dir: str | Path,
    source_configs: Optional[Sequence[SourceTableConfig]] = None,
    *,
    raw_subdir: str = "raw",
) -> IngestResult:
    """Ingest every raw file in ``<snapshot_dir>/<raw_subdir>/`` into the snapshot.

    Args:
        snapshot_dir: e.g. ``.../snapshots/v1``.
        source_configs: Per-table key declarations. Tables with no matching config
            fall back to ``key_status="deferred"`` (forces a Gate-1 key question).
        raw_subdir: Subdir holding the immutable raw drop.

    Returns:
        :class:`IngestResult` with row counts and written artifact paths.
    """
    snap = Path(snapshot_dir)
    raw_dir = snap / raw_subdir
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"raw drop dir not found: {raw_dir}")

    tables_dir = snap / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    # Match declared tables to ingested tables under the SAME normalization the
    # table name itself receives (filename/sheet → normalize_column_name). Without
    # this, a natural declaration like `table: CM_CONTACTS` for CM_CONTACTS.csv
    # silently misses (ingested name is `cm_contacts`), the source_key is dropped,
    # and identity falls back to hash-based `deferred` — defeating stable external_ids.
    config_by_table = {normalize_column_name(c.table): c for c in (source_configs or [])}

    manifest_files: list[dict[str, Any]] = []
    index_frames: list[pd.DataFrame] = []
    result = IngestResult(snapshot_dir=snap)

    raw_files = sorted(p for p in raw_dir.iterdir() if p.is_file() and not p.name.startswith("."))
    for path in raw_files:
        try:
            frames = _read_file(path)
        except ValueError as exc:
            manifest_files.append({"file": path.name, "skipped": True, "reason": str(exc)})
            continue

        file_entry: dict[str, Any] = {"file": path.name, "bytes": path.stat().st_size, "tables": []}
        for table, raw_df in frames.items():
            df = _normalize_columns(raw_df)
            cfg = config_by_table.get(table)

            if cfg is None:
                # No declaration → defer the key (Gate-1 question), don't guess.
                identity_df = compute_identity(df, None, table, key_status="deferred")
            else:
                # Declared key/hash columns use the source's natural casing; the
                # ingested columns are normalized — normalize the declared names
                # the same way so a confirmed key like CONTACT_ID resolves to the
                # `contact_id` column instead of raising "source_key not found".
                identity_df = compute_identity(
                    df,
                    [normalize_column_name(c) for c in cfg.source_key] if cfg.source_key else None,
                    table,
                    key_status=cfg.key_status,
                    hash_columns=(
                        [normalize_column_name(c) for c in cfg.key_columns] if cfg.key_columns else None
                    ),
                )

            out_path = tables_dir / f"{table}.parquet"
            identity_df.to_parquet(out_path, index=False)

            idx = build_source_index(identity_df)
            idx.insert(0, "table", table)
            index_frames.append(idx)

            result.tables[table] = len(df)
            file_entry["tables"].append(
                {
                    "table": table,
                    "rows": int(len(df)),
                    "columns": list(df.columns),
                    "key_status": str(identity_df[KEY_STATUS_COL].iloc[0]) if len(identity_df) else "unknown",
                }
            )
        manifest_files.append(file_entry)

    # A declared source table that matched no ingested table is almost always an
    # operator error (filename typo, a missing drop, or a stale declaration). Such
    # a table would otherwise pass unnoticed — its declared key never applies and
    # any actually-ingested table without a declaration silently defers — so flag
    # it loudly here rather than letting it slip through.
    unmatched = sorted(set(config_by_table) - set(result.tables))
    if unmatched:
        print(
            f"  ⚠ declared source table(s) matched no ingested file: {unmatched} "
            f"(ingested: {sorted(result.tables)}). Check project.yaml `sources[].table` "
            "against the raw filenames.",
            file=sys.stderr,
        )

    # The unified source_index across all tables — the delta engine's sole input.
    if index_frames:
        source_index = pd.concat(index_frames, ignore_index=True)
    else:
        source_index = pd.DataFrame(columns=["table", "source_id", "row_hash"])
    index_path = snap / "source_index.parquet"
    source_index.to_parquet(index_path, index=False)
    result.source_index_path = index_path

    manifest = {
        "snapshot": snap.name,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_tool_version": VERSION,
        "files": manifest_files,
        "table_row_counts": result.tables,
        "total_rows": int(sum(result.tables.values())),
        "total_tables": len(result.tables),
        "unmatched_source_declarations": unmatched,
    }
    manifest_path = snap / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    result.manifest_path = manifest_path
    return result
