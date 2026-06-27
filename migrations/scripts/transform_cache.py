"""The value-level (Tier-3) transform cache — never parse the same string twice.

This is the third, independent memoization tier (operating-model §5.3). Tiers 1–2
(`source_id + row_hash`, and `source_id + column + version` in :mod:`ledger`) are
*row/cell* caches — they decide which records to touch. They have a limit: if some
*other* cell in a row changes, the whole row is CHANGED and every cell re-processes,
even though (say) the name string itself did not change.

This tier closes that gap. It is keyed on the **input value**, not the record::

    key = sha256(transform, transform_version, normalized_input, context_signature)

so the same exact string is parsed at most once per transform version — across rows
**and** across drops. That is what guarantees no second LLM call even when other
cells in the row change, and it also dedups *within* a drop (50 ``"John M. Smith,
Jr."`` → one parse, 49 hits).

Authority tiers (operating-model §5.3):
    - **human-pinned** rules WIN and are **version-independent** — improving the
      parser never discards a human's "this string → this parse". Looked up first,
      ignoring ``transform_version``.
    - **deterministic** entries are cached for cross-row dedup, version-scoped.
    - **llm** entries are cached version-scoped **only** above
      :data:`LLM_CACHE_CONFIDENCE_FLOOR`; below the floor they are not stored as
      authoritative (a lookup returns ``None`` so the cell re-resolves / is reviewed).

Storage (operating-model §5.3):
    - ``ledger/parse_rules.yaml``    = human-readable, diff-able **source of truth**
                                       for pinned rules (seeded into / exported from
                                       the sqlite cache).
    - ``ledger/transform_cache.sqlite`` = the fast derived cache (stdlib ``sqlite3``).

Invalidation / poisoning guard (SPEC §5.3):
    - a transform version bump lazily recomputes only strings re-encountered under
      the new version (:func:`invalidate` flushes derived, non-pinned entries);
    - :func:`review_sample` surfaces a sample of llm-derived entries for review;
    - a human correction :func:`pin`s (and overwrites) an authoritative entry;
    - a systematic error is flushed by bumping the version.

Spec & knowledge that specify the rules:
    SPEC.md §5.3                          (the full three-tier spec)
    knowledge/topics/name-parsing.md      (the transform cache / parse memory)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

try:
    import yaml
except ImportError:  # pragma: no cover - pyyaml is a hard dep; JSONL sidecar fallback otherwise
    yaml = None  # type: ignore

from cellcontract import Cell

VERSION = "1.0.0"

LLM_CACHE_CONFIDENCE_FLOOR = 0.7
"""LLM-derived entries are cached as authoritative only at/above this confidence.
Below it, :meth:`TransformCache.store` skips the write and :meth:`lookup` would never
return one — the cell re-resolves and surfaces for review (the poisoning guard)."""

CACHE_FILENAME = "transform_cache.sqlite"
PIN_RULES_FILENAME = "parse_rules.yaml"

_PINNED_VERSION = "__pinned__"
"""Sentinel ``transform_version`` stored on human-pinned rows so they are
version-independent — :meth:`lookup` checks these first, ignoring the live version."""

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key_hash          TEXT PRIMARY KEY,
    transform         TEXT NOT NULL,
    transform_version TEXT NOT NULL,
    input             TEXT NOT NULL,
    context_sig       TEXT NOT NULL DEFAULT '',
    output_json       TEXT NOT NULL,
    method            TEXT NOT NULL,
    confidence        REAL NOT NULL DEFAULT 0.0,
    model             TEXT,
    pinned            INTEGER NOT NULL DEFAULT 0,
    created_at        REAL NOT NULL,
    last_hit_at       REAL,
    hit_count         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_cache_pin ON cache (transform, context_sig, pinned);
CREATE INDEX IF NOT EXISTS idx_cache_ver ON cache (transform, transform_version);
CREATE INDEX IF NOT EXISTS idx_cache_method ON cache (transform, method);
"""


# --------------------------------------------------------------------------- #
# Key derivation                                                              #
# --------------------------------------------------------------------------- #
def normalize_input(value: Any) -> str:
    """Normalize a raw cell to the canonical string the key is computed over.

    Unicode-NFC + collapsed internal whitespace + trimmed, so cosmetic variants
    (``"John  Smith "`` vs ``"John Smith"``) hit the same cache entry. ``None``
    normalizes to the empty string. Note: this is a *key* normalization, not the
    transform's own cleansing — the deterministic primitive still sees the raw cell.
    """
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    return " ".join(text.split())


def make_key(
    transform: str,
    transform_version: str,
    input_value: Any,
    context_signature: str = "",
) -> str:
    """Cache key = sha256 over (transform, version, normalized_input, context_sig).

    ``context_signature`` captures only the column-level decisions that change the
    output (e.g. ``"name_order=last_first"``, ``"date_format=MDY"``); empty for
    context-free transforms. Including it prevents reusing a parse that was only
    correct under a since-changed column interpretation (operating-model §5.3).
    """
    h = hashlib.sha256()
    for part in (transform, transform_version, normalize_input(input_value), context_signature):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Row → Cell                                                                  #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class CacheEntry:
    """A flat view of one cache row (used by review/export helpers)."""

    key_hash: str
    transform: str
    transform_version: str
    input: str
    context_sig: str
    output: Any
    method: str
    confidence: float
    model: Optional[str]
    pinned: bool
    created_at: float
    last_hit_at: Optional[float]
    hit_count: int


def _row_to_entry(row: sqlite3.Row) -> CacheEntry:
    return CacheEntry(
        key_hash=row["key_hash"],
        transform=row["transform"],
        transform_version=row["transform_version"],
        input=row["input"],
        context_sig=row["context_sig"],
        output=json.loads(row["output_json"]),
        method=row["method"],
        confidence=row["confidence"],
        model=row["model"],
        pinned=bool(row["pinned"]),
        created_at=row["created_at"],
        last_hit_at=row["last_hit_at"],
        hit_count=row["hit_count"],
    )


def _row_to_cell(row: sqlite3.Row, *, served_method: str) -> Cell:
    """Build the :class:`Cell` returned on a cache hit.

    ``served_method`` stamps the provenance of *this* delivery (``"cache"`` /
    ``"cache:pinned"``) while ``meta`` preserves how the value was originally
    produced (deterministic / llm / human) and the model, if any.
    """
    meta: dict[str, Any] = {
        "cache": True,
        "origin_method": row["method"],
        "transform_version": row["transform_version"],
    }
    if row["context_sig"]:
        meta["context_signature"] = row["context_sig"]
    if row["model"]:
        meta["model"] = row["model"]
    if row["pinned"]:
        meta["pinned"] = True
    return Cell(
        value=json.loads(row["output_json"]),
        confidence=row["confidence"],
        method=served_method,
        needs_llm=False,
        meta=meta,
    )


# --------------------------------------------------------------------------- #
# The cache handle                                                            #
# --------------------------------------------------------------------------- #
class TransformCache:
    """Context-managed sqlite handle on ``ledger/transform_cache.sqlite``.

    Usage::

        with TransformCache(project_dir / "ledger") as cache:
            cell = cache.lookup("parse_name", "1.0.0", "John M. Smith, Jr.")
            if cell is None:
                cell = parse_name.clean(raw)
                cache.store("parse_name", "1.0.0", raw, cell)
    """

    def __init__(self, ledger_dir: str | Path) -> None:
        self.ledger_dir = Path(ledger_dir)
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.ledger_dir / CACHE_FILENAME
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # -- context manager -------------------------------------------------- #
    def __enter__(self) -> "TransformCache":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None  # type: ignore[assignment]

    # -- lookup ----------------------------------------------------------- #
    def lookup(
        self,
        transform: str,
        transform_version: str,
        input_value: Any,
        context_signature: str = "",
    ) -> Optional[Cell]:
        """Return a cached :class:`Cell`, or ``None`` on a miss.

        Authority order (operating-model §5.3):

        1. **human-pinned** rules win and are version-independent — checked first
           against the sentinel pinned version, ignoring ``transform_version``;
        2. otherwise the **version-scoped derived** entry (deterministic or
           above-floor llm) for this exact ``transform_version``.

        On a hit, ``hit_count`` is incremented and ``last_hit_at`` is stamped
        (the dedup/throughput signal the review surfaces).
        """
        pinned_key = make_key(transform, _PINNED_VERSION, input_value, context_signature)
        row = self._fetch(pinned_key)
        if row is not None:
            self._bump(pinned_key)
            return _row_to_cell(row, served_method="cache:pinned")

        derived_key = make_key(transform, transform_version, input_value, context_signature)
        row = self._fetch(derived_key)
        if row is None:
            return None
        # Defensive: a sub-floor llm entry should never have been stored, but if a
        # legacy/poisoned row slipped in, do not serve it as authoritative.
        if row["method"].startswith("llm") and row["confidence"] < LLM_CACHE_CONFIDENCE_FLOOR:
            return None
        self._bump(derived_key)
        return _row_to_cell(row, served_method="cache")

    def _fetch(self, key_hash: str) -> Optional[sqlite3.Row]:
        cur = self._conn.execute("SELECT * FROM cache WHERE key_hash = ?", (key_hash,))
        return cur.fetchone()

    def _bump(self, key_hash: str) -> None:
        self._conn.execute(
            "UPDATE cache SET hit_count = hit_count + 1, last_hit_at = ? WHERE key_hash = ?",
            (time.time(), key_hash),
        )
        self._conn.commit()

    # -- store ------------------------------------------------------------ #
    def store(
        self,
        transform: str,
        transform_version: str,
        input_value: Any,
        cell: Cell,
        context_signature: str = "",
        model: Optional[str] = None,
    ) -> bool:
        """Cache a derived (deterministic or llm) result, version-scoped.

        Skips the write — returning ``False`` — when the cell still wants the LLM
        (``needs_llm``) or when an llm-method cell is below
        :data:`LLM_CACHE_CONFIDENCE_FLOOR`. Below-floor llm results are deliberately
        *not* cached as authoritative so the cell re-resolves / is reviewed rather
        than poisoning future rows (SPEC §5.3).

        The LLM tier (the ``cleanse --llm`` path, SPEC §8 stage 8, driven by the
        `/migrate` command) calls this **after** producing and re-validating a
        value — that write-back is
        what guarantees a string is parsed at most once per transform version.

        Returns:
            True if the entry was written, False if intentionally skipped.
        """
        if cell.needs_llm:
            return False
        is_llm = cell.method.startswith("llm")
        if is_llm and cell.confidence < LLM_CACHE_CONFIDENCE_FLOOR:
            return False
        key_hash = make_key(transform, transform_version, input_value, context_signature)
        self._upsert(
            key_hash=key_hash,
            transform=transform,
            transform_version=transform_version,
            input_value=normalize_input(input_value),
            context_signature=context_signature,
            output=cell.value,
            method=cell.method,
            confidence=cell.confidence,
            model=model,
            pinned=False,
        )
        return True

    # -- pin -------------------------------------------------------------- #
    def pin(
        self,
        transform: str,
        input_value: Any,
        output: Any,
        context_signature: str = "",
        note: Optional[str] = None,
    ) -> str:
        """Write an authoritative, **version-independent** pinned entry.

        Pinned rules are the human-corrected source of truth: they win over any
        derived entry and survive every version bump (stored under the sentinel
        :data:`_PINNED_VERSION`, looked up first by :meth:`lookup`). This is the
        "a human correction pins + overwrites" branch of the poisoning guard.

        Returns the key_hash of the pinned entry.
        """
        key_hash = make_key(transform, _PINNED_VERSION, input_value, context_signature)
        self._upsert(
            key_hash=key_hash,
            transform=transform,
            transform_version=_PINNED_VERSION,
            input_value=normalize_input(input_value),
            context_signature=context_signature,
            output=output,
            method="human",
            confidence=1.0,
            model=note,
            pinned=True,
        )
        return key_hash

    def _upsert(
        self,
        *,
        key_hash: str,
        transform: str,
        transform_version: str,
        input_value: str,
        context_signature: str,
        output: Any,
        method: str,
        confidence: float,
        model: Optional[str],
        pinned: bool,
    ) -> None:
        now = time.time()
        self._conn.execute(
            """
            INSERT INTO cache (
                key_hash, transform, transform_version, input, context_sig,
                output_json, method, confidence, model, pinned, created_at, hit_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(key_hash) DO UPDATE SET
                output_json = excluded.output_json,
                method      = excluded.method,
                confidence  = excluded.confidence,
                model       = excluded.model,
                pinned      = excluded.pinned,
                transform_version = excluded.transform_version
            """,
            (
                key_hash,
                transform,
                transform_version,
                input_value,
                context_signature,
                json.dumps(output, default=str),
                method,
                float(confidence),
                model,
                1 if pinned else 0,
                now,
            ),
        )
        self._conn.commit()

    # -- invalidation / review ------------------------------------------- #
    def invalidate(self, transform: str, transform_version: Optional[str] = None) -> int:
        """Flush derived (non-pinned) entries for ``transform`` on a version bump.

        Pinned rules always survive. With ``transform_version`` given, only that
        version's derived rows are flushed; without it, all derived rows for the
        transform are flushed (lazy recompute then re-fills under the new version).

        Returns the number of rows deleted.
        """
        if transform_version is None:
            cur = self._conn.execute(
                "DELETE FROM cache WHERE transform = ? AND pinned = 0",
                (transform,),
            )
        else:
            cur = self._conn.execute(
                "DELETE FROM cache WHERE transform = ? AND transform_version = ? AND pinned = 0",
                (transform, transform_version),
            )
        self._conn.commit()
        return cur.rowcount

    def review_sample(self, transform: Optional[str] = None, limit: int = 50) -> list[CacheEntry]:
        """Return a sample of **llm-derived** entries for the poisoning-guard review.

        Highest-leverage first (most hits, then most recent), so the reviewer sees
        the entries whose correctness propagates to the most rows. Anything wrong
        gets :meth:`pin`-corrected; a systematic error is flushed by version bump.
        """
        params: list[Any] = []
        sql = "SELECT * FROM cache WHERE pinned = 0 AND method LIKE 'llm%'"
        if transform is not None:
            sql += " AND transform = ?"
            params.append(transform)
        sql += " ORDER BY hit_count DESC, created_at DESC LIMIT ?"
        params.append(int(limit))
        cur = self._conn.execute(sql, params)
        return [_row_to_entry(r) for r in cur.fetchall()]

    def pins(self, transform: Optional[str] = None) -> list[CacheEntry]:
        """All current pinned entries (for export / inspection)."""
        if transform is None:
            cur = self._conn.execute(
                "SELECT * FROM cache WHERE pinned = 1 ORDER BY transform, input"
            )
        else:
            cur = self._conn.execute(
                "SELECT * FROM cache WHERE pinned = 1 AND transform = ? ORDER BY input",
                (transform,),
            )
        return [_row_to_entry(r) for r in cur.fetchall()]

    def iter_all(self) -> Iterator[CacheEntry]:
        """Iterate every cache row (diagnostics)."""
        cur = self._conn.execute("SELECT * FROM cache")
        for row in cur:
            yield _row_to_entry(row)

    # -- parse_rules.yaml (the pinned-rule source of truth) -------------- #
    def seed_from_rules(self, path: str | Path) -> int:
        """Load ``ledger/parse_rules.yaml`` and upsert each rule as a pinned entry.

        ``parse_rules.yaml`` is the human-readable, diff-able **source of truth**;
        the sqlite cache is the derived index seeded from it. Re-running is
        idempotent (upsert by key). Each rule:

            {transform, input, context_signature?, output, note?, pinned_by?, pinned_at?}

        Returns the number of rules seeded.
        """
        rules = _read_rules(path)
        count = 0
        for rule in rules:
            note = rule.get("note")
            self.pin(
                transform=rule["transform"],
                input_value=rule["input"],
                output=rule["output"],
                context_signature=rule.get("context_signature", ""),
                note=note,
            )
            count += 1
        return count

    def export_pins(self, path: str | Path) -> int:
        """Write current pinned entries back to ``parse_rules.yaml``.

        Round-trips human corrections made via :meth:`pin` into the diff-able source
        of truth. Returns the number of rules written.
        """
        rules: list[dict[str, Any]] = []
        for entry in self.pins():
            rule: dict[str, Any] = {
                "transform": entry.transform,
                "input": entry.input,
                "output": entry.output,
            }
            if entry.context_sig:
                rule["context_signature"] = entry.context_sig
            if entry.model:  # `model` carries the pin note for human entries
                rule["note"] = entry.model
            rules.append(rule)
        _write_rules(path, rules)
        return len(rules)


# --------------------------------------------------------------------------- #
# parse_rules.yaml read/write (dependency-light, matching ledger.py's yaml use)#
# --------------------------------------------------------------------------- #
# ledger.py treats pyyaml as a hard dep but degrades gracefully when it is absent.
# Here we go one step further so the cache stays usable in a stdlib-only venv: if
# pyyaml is unavailable we transparently fall back to a JSONL sidecar (`<name>.jsonl`)
# carrying the same rule list. The YAML file remains the canonical artifact when
# pyyaml is present.
def _rules_payload(rules: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema_version": 1, "pinned_rules": rules}


def _jsonl_sidecar(path: str | Path) -> Path:
    return Path(path).with_suffix(Path(path).suffix + ".jsonl")


def _read_rules(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if yaml is not None and p.exists():
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return list(raw.get("pinned_rules") or [])
    sidecar = _jsonl_sidecar(path)
    if sidecar.exists():
        out: list[dict[str, Any]] = []
        for line in sidecar.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out
    if not p.exists():
        return []
    raise RuntimeError(
        f"Cannot read {p}: PyYAML is not installed and no JSONL sidecar exists. "
        "Install pyyaml or provide a .jsonl sidecar."
    )


def _write_rules(path: str | Path, rules: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if yaml is not None:
        p.write_text(
            yaml.safe_dump(_rules_payload(rules), sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return
    sidecar = _jsonl_sidecar(path)
    sidecar.write_text(
        "".join(json.dumps(r, default=str) + "\n" for r in rules),
        encoding="utf-8",
    )
