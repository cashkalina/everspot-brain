"""Source identity + change-detection primitives (the foundation for incremental runs).

For every source row we derive two values at ingest:

- ``source_id`` = ``"<table>:<source_key>"`` — permanently bound to the record in
  the client's system. The ``external_id`` we mint is derived from it, which is
  what makes v2 *update* rather than *duplicate* (operating-model §2).
- ``row_hash`` = a stable hash of the row's *normalized* raw cell values. Detects
  whether a record changed between drops (operating-model §2, §5.1).

Key handling (operating-model §2):
    confirmed  — trust the declared ``source_key`` column(s).
    deferred   — no key declared yet; we still need *something*, so we behave like
                 ``hashed`` over all columns but flag ``key_status=deferred`` so the
                 operator is forced to answer "which column identifies an X?" at Gate 1.
    hashed     — no stable client key; derive ``source_key`` from a deterministic
                 hash of the identifying columns, and flag the row fragile.

everspot-brain doc that specifies the rules:
    system-wiki/system/data-migration.md  (§ identity & change detection)
"""

from __future__ import annotations

import hashlib
from typing import Iterable, Optional, Sequence

import pandas as pd

VERSION = "1.0.0"

SOURCE_ID_COL = "source_id"
ROW_HASH_COL = "row_hash"
KEY_STATUS_COL = "key_status"
FRAGILE_COL = "identity_fragile"

_NULL_SENTINEL = "__NULL__"
"""Stable rendering of a missing value so NaN/None/"" never silently differ.

Must stay **printable and xlsx/URL/log-safe**: it is rendered literally into the
human-meaningful ``source_id`` key segment (and therefore into the minted
``external_id``), which is written to wave Excel, logged, and used in the post-load
ID harvest. A raw control-byte sentinel (the original ``\\x00NULL\\x00``) crashed the
Excel emitter and left non-printable bytes in external_ids. Collision with a real
cell literally equal to ``__NULL__`` is acceptably remote (and such a value would be
a data error in its own right)."""


def _normalize_scalar(value: object) -> str:
    """Render one cell to a stable, comparison-safe string.

    Whitespace-trimmed, NaN/None unified, numeric-int floats collapsed
    (``2.0`` -> ``"2"``) so spreadsheet float coercion doesn't churn the hash.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return _NULL_SENTINEL
    try:
        if pd.isna(value):  # pandas NA / NaT
            return _NULL_SENTINEL
    except (TypeError, ValueError):
        pass

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    text = str(value).strip()
    return text if text != "" else _NULL_SENTINEL


def _hash_values(values: Iterable[str]) -> str:
    """sha256 over null-delimited normalized values (order-significant)."""
    digest = hashlib.sha256()
    for v in values:
        digest.update(v.encode("utf-8"))
        digest.update(b"\x1f")  # unit separator between fields
    return digest.hexdigest()


def _row_hash(row: pd.Series, columns: Sequence[str]) -> str:
    """Hash a row over the given columns, with column *names* sorted for stability.

    Sorting keys means column reordering between drops doesn't change the hash;
    each value is paired with its (normalized) column name so a value moving
    between columns *does* change it.
    """
    parts: list[str] = []
    for col in sorted(columns):
        parts.append(col.strip().lower())
        parts.append(_normalize_scalar(row.get(col)))
    return _hash_values(parts)


def _composite_key(row: pd.Series, key_cols: Sequence[str]) -> str:
    """Build the human-meaningful key segment of a ``source_id`` from key columns."""
    rendered = [_normalize_scalar(row.get(c)) for c in key_cols]
    if len(rendered) == 1:
        return rendered[0]
    # Composite: join with a pipe; if any component is missing we still produce a
    # value but the caller flags the row fragile.
    return "|".join(rendered)


def _hashed_key(row: pd.Series, key_cols: Sequence[str]) -> str:
    """Deterministic short key for keyless tables (hash of identifying columns)."""
    full = _row_hash(row, key_cols)
    return f"h:{full[:16]}"


def compute_identity(
    df: pd.DataFrame,
    source_key_cols: Optional[Sequence[str]],
    table: str,
    *,
    key_status: str = "confirmed",
    hash_columns: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Add ``source_id``, ``row_hash``, ``key_status`` and ``identity_fragile`` columns.

    Args:
        df: The normalized source table.
        source_key_cols: Declared key column(s). Ignored when ``key_status`` is
            ``"hashed"`` or ``"deferred"``.
        table: Normalized table name (the ``<table>`` half of ``source_id``).
        key_status: ``confirmed`` | ``deferred`` | ``hashed`` (see module docstring).
        hash_columns: For ``hashed``/``deferred``, the identifying columns to hash.
            Defaults to all columns.

    Returns:
        A copy of ``df`` with the identity columns appended.

    Raises:
        ValueError: For ``confirmed`` status with missing/absent key columns.
    """
    out = df.copy()
    all_cols = list(df.columns)
    status = key_status.lower()

    if status == "confirmed":
        if not source_key_cols:
            raise ValueError(
                f"table '{table}' has key_status=confirmed but no source_key columns. "
                "Declare the key in project.yaml or set key_status to deferred/hashed."
            )
        missing = [c for c in source_key_cols if c not in df.columns]
        if missing:
            raise ValueError(f"table '{table}' source_key columns not found: {missing}")
        key_cols = list(source_key_cols)
        # A confirmed key with a blank component is fragile for that row only.
        fragile = (
            df[key_cols].apply(lambda r: any(_normalize_scalar(v) == _NULL_SENTINEL for v in r), axis=1)
            if key_cols
            else pd.Series(False, index=df.index)
        )
        keys = df.apply(lambda r: _composite_key(r, key_cols), axis=1)

    elif status in ("hashed", "deferred"):
        key_cols = list(hash_columns) if hash_columns else all_cols
        missing = [c for c in key_cols if c not in df.columns]
        if missing:
            raise ValueError(f"table '{table}' hash columns not found: {missing}")
        keys = df.apply(lambda r: _hashed_key(r, key_cols), axis=1)
        # Whole table is fragile: identity is derived, not client-anchored.
        fragile = pd.Series(True, index=df.index)

    else:
        raise ValueError(f"unknown key_status '{key_status}' for table '{table}'")

    out[SOURCE_ID_COL] = keys.map(lambda k: f"{table}:{k}")
    out[ROW_HASH_COL] = df.apply(lambda r: _row_hash(r, all_cols), axis=1)
    out[KEY_STATUS_COL] = status
    out[FRAGILE_COL] = fragile.astype(bool)

    _warn_on_duplicate_ids(out, table)
    return out


def _warn_on_duplicate_ids(df: pd.DataFrame, table: str) -> None:
    """Duplicate ``source_id``s mean the declared key isn't actually unique."""
    dupes = df[SOURCE_ID_COL].duplicated(keep=False)
    if dupes.any():
        n = int(dupes.sum())
        sample = df.loc[dupes, SOURCE_ID_COL].head(5).tolist()
        # Non-fatal: the operator must confirm the real key (Gate-1 question),
        # but we surface it loudly here so it is never silent.
        print(
            f"[identity] WARNING table '{table}': {n} rows share a source_id "
            f"(key not unique). Examples: {sample}. "
            "Raise a Gate-1 'which column uniquely identifies an X?' question."
        )


def build_source_index(df_with_identity: pd.DataFrame) -> pd.DataFrame:
    """Project to the ``source_index`` columns the delta engine compares on.

    Keeps the raw cells too (everything except the derived helper columns) so the
    delta engine can show *what* changed without re-reading the table parquet.
    """
    helper = {KEY_STATUS_COL, FRAGILE_COL}
    raw_cols = [c for c in df_with_identity.columns if c not in {SOURCE_ID_COL, ROW_HASH_COL} | helper]
    cols = [SOURCE_ID_COL, ROW_HASH_COL, *raw_cols]
    return df_with_identity[cols].copy()
