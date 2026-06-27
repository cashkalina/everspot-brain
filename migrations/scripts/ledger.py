"""The Decision Ledger — the project's durable memory + the version-aware cache.

The ledger is keyed by *what a decision is about* (a column, a source record's
stable id, a value) — never by row position or which drop it came from — so it
survives across drops and is re-applied automatically (operating-model §1).

Files (under ``ledger/``):
    mapping.yaml         column → target field + transform (versioned)
    value_sets.yaml      value-set translations, e.g. STAT: {A: active-sale, ...}
    cell_overrides.jsonl manual per-cell corrections, keyed (table, source_id, column)
    external_ids.json    source_id → external_id → everspot id (see external_ids.py)

The cache (operating-model §5.2): a cleansed cell records the ``script_version`` and
``mapping_version`` it was produced under. :func:`needs_recompute` recomputes a
cached cell when **either** the record changed (handled by delta.py) **or** the
transform/mapping that produced it changed. Improving a script later → bump its
version → only the cells it touched recompute.

everspot-brain doc that specifies the rules:
    system-wiki/system/data-migration.md  (§ the decision ledger, version-aware cache)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a hard dep in requirements.txt
    yaml = None  # type: ignore

from cellcontract import Cell

VERSION = "1.0.0"


# --------------------------------------------------------------------------- #
# Mapping spec (mapping.yaml — schemas/mapping.schema.json)                     #
# --------------------------------------------------------------------------- #
# The on-disk shape is the schema-conformant one the Map stage authors and the
# project template ships: ``tables`` is a *list* of table blocks, each with
# ``source_table`` / ``target_entity`` / ``secondary_entities`` / ``columns`` /
# ``reference_resolution``; columns use ``action`` in
# {map, split_name, value_map, derive, external_id, unmapped}, ``value_set_ref``
# (not ``value_set``), and a ``transform`` like ``parse_name`` (or the versioned
# ``parse_name@1.2.0`` form, whose ``@`` tail is parsed off into ``transform_version``).
@dataclass(slots=True)
class ReferenceResolution:
    """A value-set → tenant reference-ID resolution for a target field."""

    field: str
    via: str = "list_options"
    type: str = ""
    resolved: dict[str, Any] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ColumnMapping:
    """One source column → target field(s) + transform (schema: columnMapping)."""

    source: str
    action: str = "map"  # map | split_name | value_map | derive | external_id | unmapped
    target: Optional[str] = None
    targets: list[str] = field(default_factory=list)
    transform: Optional[str] = None  # the cleansing primitive's name, e.g. "parse_name"
    transform_version: Optional[str] = None
    value_set_ref: Optional[str] = None  # key into value_sets for action=value_map
    derivation: Optional[str] = None
    confidence: float = 1.0
    note: Optional[str] = None


@dataclass(slots=True)
class MappingSpec:
    """A table's mapping block (schema: tableMapping)."""

    source_table: str
    target_entity: str = ""
    secondary_entities: list[str] = field(default_factory=list)
    columns: list[ColumnMapping] = field(default_factory=list)
    reference_resolution: list[ReferenceResolution] = field(default_factory=list)

    def column(self, source: str) -> Optional[ColumnMapping]:
        return next((c for c in self.columns if c.source == source), None)

    def column_by_action(self, action: str) -> list[ColumnMapping]:
        return [c for c in self.columns if c.action == action]

    def reference_for(self, field_name: str) -> Optional[ReferenceResolution]:
        return next((r for r in self.reference_resolution if r.field == field_name), None)


def _require_yaml() -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is required (add `pyyaml` to the environment).")


def _split_transform_version(value: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """``"parse_name@1.2.0"`` → ``("parse_name", "1.2.0")``; bare name → (name, None)."""
    if not value:
        return None, None
    if "@" in value:
        name, _, ver = value.partition("@")
        return name or None, ver or None
    return value, None


def _column_from_dict(raw: dict[str, Any]) -> ColumnMapping:
    """Build a ColumnMapping, normalizing the transform/version split.

    The template/schema sometimes carry the version as a ``name@version`` token
    (in ``transform`` and/or an explicit ``transform_version``). We always end up
    with ``transform`` = the bare primitive name and ``transform_version`` = the
    bare semver (the part the Tier-3 cache key uses).
    """
    data = dict(raw)
    transform, ver_from_transform = _split_transform_version(data.get("transform"))
    data["transform"] = transform

    explicit = data.get("transform_version")
    if explicit:
        # An explicit "parse_name@1.0.0" collapses to "1.0.0"; a bare "1.0.0" stays.
        _, ver_tail = _split_transform_version(explicit)
        data["transform_version"] = ver_tail if ver_tail is not None else explicit
    else:
        data["transform_version"] = ver_from_transform

    allowed = set(ColumnMapping.__dataclass_fields__)  # type: ignore[attr-defined]
    return ColumnMapping(**{k: v for k, v in data.items() if k in allowed})


def load_mapping(path: str | Path) -> dict[str, MappingSpec]:
    """Load ``mapping.yaml`` → ``{source_table: MappingSpec}`` (schema-conformant).

    The schema's ``tables`` is a list; we index it by ``source_table`` for lookup.
    """
    _require_yaml()
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    out: dict[str, MappingSpec] = {}
    for block in (raw.get("tables") or []):
        table = block["source_table"]
        cols = [_column_from_dict(c) for c in (block.get("columns") or [])]
        refs = [
            ReferenceResolution(
                field=r["field"],
                via=r.get("via", "list_options"),
                type=r.get("type", ""),
                resolved=dict(r.get("resolved") or {}),
                missing=list(r.get("missing") or []),
            )
            for r in (block.get("reference_resolution") or [])
        ]
        out[table] = MappingSpec(
            source_table=table,
            target_entity=block.get("target_entity", ""),
            secondary_entities=list(block.get("secondary_entities") or []),
            columns=cols,
            reference_resolution=refs,
        )
    return out


def _prune(d: dict[str, Any], *, keep: tuple[str, ...] = ()) -> dict[str, Any]:
    """Drop empty optional keys (keeps ``keep`` even when falsy, for required fields)."""
    return {k: v for k, v in d.items() if k in keep or v not in (None, [], "", {})}


def save_mapping(specs: dict[str, MappingSpec], path: str | Path) -> None:
    _require_yaml()
    tables = []
    for s in specs.values():
        cols = [_prune(asdict(c), keep=("source", "action", "confidence")) for c in s.columns]
        block: dict[str, Any] = {
            "source_table": s.source_table,
            "target_entity": s.target_entity,
        }
        if s.secondary_entities:
            block["secondary_entities"] = list(s.secondary_entities)
        block["columns"] = cols
        if s.reference_resolution:
            block["reference_resolution"] = [
                _prune(asdict(r), keep=("field", "via", "type"))
                for r in s.reference_resolution
            ]
        tables.append(block)
    payload = {"schema_version": 1, "tables": tables}
    Path(path).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Value sets (value_sets.yaml)                                                 #
# --------------------------------------------------------------------------- #
def load_value_sets(path: str | Path) -> dict[str, dict[str, Any]]:
    """Load ``value_sets.yaml`` → ``{"TABLE.COLUMN": {raw_value: resolved}}``.

    Reads the schema-conformant shape (``schemas/value_sets.schema.json``): a list
    under ``value_sets``, each entry keyed by ``(table, column)`` with a ``values``
    list of ``{source_value, target_value, ...}``. We flatten to a flat lookup
    keyed ``"<TABLE>.<COLUMN>"`` (matching ``columnMapping.value_set_ref``), whose
    value is ``{source_value: target_value}``. ``target_value`` is a status/type
    string, a tenant list_option id, or null (plan §4.1).
    """
    _require_yaml()
    p = Path(path)
    if not p.exists():
        return {}
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: dict[str, dict[str, Any]] = {}
    for vs in (raw.get("value_sets") or []):
        key = f"{vs['table']}.{vs['column']}"
        out[key] = {
            v["source_value"]: v.get("target_value")
            for v in (vs.get("values") or [])
        }
    return out


def value_set_known_values(path: str | Path) -> dict[str, set[str]]:
    """``{"TABLE.COLUMN": {known source values}}`` — for surfacing *unmapped* codes.

    A source code absent from this set (and not in the flat map) is a new code that
    must surface as a needs-attention item, never be silently dropped (§5.1).
    """
    _require_yaml()
    p = Path(path)
    if not p.exists():
        return {}
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: dict[str, set[str]] = {}
    for vs in (raw.get("value_sets") or []):
        key = f"{vs['table']}.{vs['column']}"
        out[key] = {str(v["source_value"]) for v in (vs.get("values") or [])}
    return out


def save_value_sets(value_sets: dict[str, dict[str, Any]], path: str | Path) -> None:
    _require_yaml()
    Path(path).write_text(yaml.safe_dump(value_sets, sort_keys=True), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Cell overrides (cell_overrides.jsonl)                                        #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class CellOverride:
    """A manual per-cell correction, keyed (table, source_id, column).

    ``row_hash`` records the row state the override was made against; an override
    "still matches" only if the row hasn't changed underneath it (operating-model
    §5.1 — CHANGED re-applies still-matching overrides).
    """

    table: str
    source_id: str
    column: str
    value: Any
    row_hash: Optional[str] = None
    note: str = ""

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.table, self.source_id, self.column)


def load_overrides(path: str | Path) -> dict[tuple[str, str, str], CellOverride]:
    p = Path(path)
    out: dict[tuple[str, str, str], CellOverride] = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        ov = CellOverride(**rec)
        out[ov.key] = ov
    return out


def append_override(override: CellOverride, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(vars(override)) + "\n")


# --------------------------------------------------------------------------- #
# The full ledger handle                                                       #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class Ledger:
    """In-memory view of a project's ledger directory."""

    ledger_dir: Path
    mappings: dict[str, MappingSpec] = field(default_factory=dict)
    value_sets: dict[str, dict[str, Any]] = field(default_factory=dict)
    overrides: dict[tuple[str, str, str], CellOverride] = field(default_factory=dict)
    schema_version: int = 1
    known_value_set_codes: dict[str, set] = field(default_factory=dict)

    @classmethod
    def load(cls, ledger_dir: str | Path) -> "Ledger":
        d = Path(ledger_dir)
        mapping_path = d / "mapping.yaml"
        schema_version = 1
        if mapping_path.exists() and yaml is not None:
            raw = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
            schema_version = int(raw.get("schema_version", 1))
        return cls(
            ledger_dir=d,
            mappings=load_mapping(mapping_path) if mapping_path.exists() else {},
            value_sets=load_value_sets(d / "value_sets.yaml"),
            overrides=load_overrides(d / "cell_overrides.jsonl"),
            schema_version=schema_version,
            known_value_set_codes=value_set_known_values(d / "value_sets.yaml"),
        )

    def mapping_version(self, table: str) -> int:
        """The whole-mapping version (Tier-2 cell-cache gate, §5.2).

        Per-transform version lives on each column's ``transform_version``; the
        table-level gate uses the ledger's ``schema_version``.
        """
        return self.schema_version if self.mappings.get(table) else 0


# --------------------------------------------------------------------------- #
# Applying the ledger to records                                               #
# --------------------------------------------------------------------------- #
def apply_mappings(df: pd.DataFrame, mapping: MappingSpec) -> pd.DataFrame:
    """Rename/select source columns to target fields per ``mapping``.

    Handles the straightforward ``action=map`` rename and drops ``action=ignore``
    columns. Structural actions (``split_name`` fanning into several targets,
    ``value_map``, ``external_id``) are applied by their dedicated helpers/stages —
    here we just carry the source column through under its target name so the
    cleanse stage can transform it.
    """
    rename: dict[str, str] = {}
    drop: list[str] = []
    for col in mapping.columns:
        if col.source not in df.columns:
            continue
        if col.action == "ignore":
            drop.append(col.source)
        elif col.action == "map" and col.target:
            rename[col.source] = col.target
        # split_name / value_map / external_id keep their source name for the
        # transform/value-set/external-id steps to consume.
    out = df.drop(columns=drop, errors="ignore").rename(columns=rename)
    return out


def apply_value_sets(
    series: pd.Series,
    value_set_name: str,
    value_sets: dict[str, dict[str, Any]],
    *,
    default: Any = None,
) -> pd.Series:
    """Translate raw codes in ``series`` via ``value_sets[value_set_name]``.

    Unknown values map to ``default`` (typically ``None``) — the cleanse stage's
    :mod:`resolve_list_option` raises the Gate-1 question for those.
    """
    table = value_sets.get(value_set_name, {})
    return series.map(lambda v: table.get(v, default) if v is not None else None)


def apply_overrides(
    df: pd.DataFrame,
    table: str,
    overrides: dict[tuple[str, str, str], CellOverride],
    *,
    source_id_col: str = "source_id",
    row_hash_col: str = "row_hash",
) -> pd.DataFrame:
    """Apply still-matching manual cell overrides to ``df`` in place (copy).

    An override applies only when its ``row_hash`` is unset (always) or equals the
    current row's hash (the row hasn't changed since the correction was made) —
    operating-model §5.1.
    """
    out = df.copy()
    if source_id_col not in out.columns:
        return out
    hash_lookup = (
        dict(zip(out[source_id_col], out[row_hash_col])) if row_hash_col in out.columns else {}
    )
    for (ov_table, source_id, column), ov in overrides.items():
        if ov_table != table or column not in out.columns:
            continue
        if ov.row_hash is not None and hash_lookup.get(source_id) not in (None, ov.row_hash):
            continue  # stale override; the row changed underneath it
        out.loc[out[source_id_col] == source_id, column] = ov.value
    return out


# --------------------------------------------------------------------------- #
# Version-aware cache (operating-model §5.2)                                   #
# --------------------------------------------------------------------------- #
def needs_recompute(
    cell_meta: Optional[dict[str, Any]],
    current_script_version: str,
    current_mapping_version: int,
) -> bool:
    """Decide whether a cached cleansed cell must be recomputed.

    A cell carries the versions it was produced under::

        {"script_version": "1.0.0", "mapping_version": 3, ...}

    Recompute when there is no cache, or when *either* version drifted from what
    produced the cached value. (Record-level CHANGED is handled upstream by
    delta.py; this guards the orthogonal "the transform/mapping improved" case.)

    Returns:
        True if the cell must be recomputed.
    """
    if not cell_meta:
        return True
    cached_script = cell_meta.get("script_version")
    cached_mapping = cell_meta.get("mapping_version")
    if cached_script != current_script_version:
        return True
    if cached_mapping != current_mapping_version:
        return True
    return False


def stamp_versions(cell: Cell, script_version: str, mapping_version: int) -> Cell:
    """Record the producing versions on a cell so the cache can later gate it."""
    return cell.with_meta(script_version=script_version, mapping_version=mapping_version)


def recompute_targets(
    cached_meta_by_key: dict[Any, dict[str, Any]],
    current_script_version: str,
    current_mapping_version: int,
) -> list[Any]:
    """Bulk cache check: which cached cells (by key) need recompute this run."""
    return [
        key
        for key, meta in cached_meta_by_key.items()
        if needs_recompute(meta, current_script_version, current_mapping_version)
    ]
