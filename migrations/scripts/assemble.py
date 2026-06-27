"""Stage 6 — Assemble. The deterministic canonical-graph builder.

Turns flat, cleansed client rows into Everspot's relational structure and writes
the external-id-keyed canonical NDJSON artifact (one file per entity), conforming
to ``schemas/canonical-record.schema.json``. This is the **mechanical** path of the
assemble stage (SPEC §8 stage 9): the genuinely-ambiguous decisions (which column
maps to what, what a STAT code means, which two records are the same person) are
already resolved upstream by the mapping stage + the single question round and
recorded in the ledger. Assemble only applies those settled decisions,
deterministically and idempotently.

What it does (SPEC §8 stage 9):

- Applies column mappings + value-set translations to each source row.
- Splits each BURIAL row into a **Customer (decedent) + an Interment**
  (``interment.deceased_ref`` is REQUIRED and non-null).
- Builds the ownership chain: a **PropertyCommitment** (sale/reservation) →
  **OwnerFileLine** (sale_date/sale_price/deed_date/deed_number in config) →
  **OwnerFile**, with owners attached by pivot role.
- Money → integer cents, phones → digits, names → split fields, dates → partial
  dates ``{year, month, day, estimated}``, property location strings → custom
  attribute fields.
- Mints a stable ``external_id`` per record via :mod:`external_ids` (bound to
  ``source_id``); every FK is the parent's ``*_ref`` external_id.
- Stamps ``_provenance{table,row}`` + ``_confidence`` on every record.

Inputs:
    snapshots/<v>/tables/<table>.parquet   normalized cells + source_id/row_hash
    ledger/mapping.yaml + value_sets.yaml   the settled mapping decisions
    ledger/external_ids.json                already-minted ids (reused, never re-minted)
    snapshots/<v>/delta.json (optional)     scope to CHANGED + NEW on v2+

Outputs:
    runs/<v>/canonical/<entity>.ndjson      the canonical artifact
    runs/<v>/canonical/assemble_report.json needs-attention items (unmapped codes,
                                            unresolvable required refs)
    ledger/external_ids.json                updated with newly-minted bindings

Genuinely-ambiguous cases (a new STAT code, an interment whose decedent did not
resolve, an ownership row with no resolvable property) are NOT papered over with a
null: they are collected in ``assemble_report.json`` as needs-attention items for
the single question round (`migrate discover`) to surface.

Spec & knowledge that specify the rules:
    SPEC.md §8 stage 9  ·  knowledge/topics/single-flat-table-multi-entity.md
    knowledge/topics/partial-dates.md
"""

from __future__ import annotations

import calendar
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import pandas as pd

import contract
import digits_only
import normalize_date
import normalize_phone
import parse_name
import to_cents
from cellcontract import Cell
from external_ids import ExternalIdLedger
from identity import SOURCE_ID_COL
from ledger import ColumnMapping, Ledger, MappingSpec
from transform_cache import TransformCache

VERSION = "1.0.0"

# Default interment status when the source carries no scheduling state — a
# historical burial is, by definition, completed.
_DEFAULT_INTERMENT_STATUS = "completed"

# Transform name → (module, transform VERSION, output kind). The cache key is
# keyed on this transform name + version, so a cache HIT for "parse_name" on an
# unchanged name string is reused even when another cell in the row changed.
_TRANSFORMS = {
    "parse_name": (parse_name, parse_name.VERSION),
    "normalize_date": (normalize_date, normalize_date.VERSION),
    "normalize_phone": (normalize_phone, normalize_phone.VERSION),
    "to_cents": (to_cents, to_cents.VERSION),
    "digits_only": (digits_only, digits_only.VERSION),
}

# Property fields that, per the schema, are first-class columns; everything else a
# property row maps to (section/lot/space and friends) becomes a custom attribute.
_PROPERTY_SCALAR_FIELDS = {"section", "lot", "space", "status_id", "property_type_id"}

# Ownership-detail source columns on a customer-master row (ingest lowercases all
# column names). These feed the OwnerFileLine.config_data / commitment.
_OWNERSHIP_COLS = {
    "sale_price": "sale_price",
    "sale_date": "sale_date",
    "deed_number": "deed_no",
}


# --------------------------------------------------------------------------- #
# Needs-attention reporting                                                    #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class NeedsAttention:
    """One thing assemble could not settle deterministically (question-round input)."""

    kind: str  # "unmapped_value" | "unresolved_ref" | "missing_required" | "needs_llm" | "data_quality"
    table: str
    source_id: str
    detail: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "table": self.table,
            "source_id": self.source_id,
            "detail": self.detail,
            "context": self.context,
        }


@dataclass(slots=True)
class Disposition:
    """What became of ONE source row — the unit of count-conservation accounting.

    Every source row the assembler iterates gets a disposition so conservation can
    EXPLAIN it against the manifest's true row total (instead of self-deriving the
    source count from the canonical records, which structurally cannot see a drop):

      - ``produced``  : entities/external_ids this row created (a single row can
                        produce several, e.g. customer + interment + property).
      - ``deduped_into``: parent external_ids this row MERGED into (e.g. a multi-
                          occupancy second row whose property merged into the existing
                          property's external_id — it adds no new property record).
      - ``skipped_out_of_scope``: filtered out (scoped run, ``in_scope`` False).
      - ``errored``   : failed with a reason (best-effort; not silently swallowed).

    A row is ACCOUNTED when it produced ≥1 entity OR deduped_into ≥1 parent OR was
    skipped_out_of_scope OR errored. A row that did NONE of these is an UNEXPLAINED
    drop (the failure conservation must catch). A single row may both produce
    (customer+interment) AND dedup (property) — both are recorded; it stays accounted.
    """

    table: str
    source_id: str
    produced: list[dict[str, str]] = field(default_factory=list)  # [{entity, external_id}]
    deduped_into: list[str] = field(default_factory=list)         # parent external_ids
    skipped_out_of_scope: bool = False
    errored: Optional[str] = None

    @property
    def accounted(self) -> bool:
        return bool(
            self.produced or self.deduped_into or self.skipped_out_of_scope or self.errored
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "table": self.table,
            "source_id": self.source_id,
            "produced": self.produced,
            "deduped_into": self.deduped_into,
            "skipped_out_of_scope": self.skipped_out_of_scope,
            "errored": self.errored,
            "accounted": self.accounted,
        }


@dataclass(slots=True)
class AssembleResult:
    canonical_dir: Path
    entity_counts: dict[str, int] = field(default_factory=dict)
    minted: int = 0
    reused: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    needs_attention: list[NeedsAttention] = field(default_factory=list)
    written_files: list[Path] = field(default_factory=list)
    dispositions: list[Disposition] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Cell-level transform application (Tier-3 cache aware)                         #
# --------------------------------------------------------------------------- #
class _Transformer:
    """Applies a column's transform through the value cache, counting hits/misses.

    The hit/miss counters are how the integration test *proves* the Tier-3 cache:
    a CHANGED row whose name string did not change yields a cache HIT for the name
    parse (no re-parse), even though another cell in that row changed.
    """

    def __init__(self, cache: Optional[TransformCache]) -> None:
        self.cache = cache
        self.hits = 0
        self.misses = 0

    def apply(
        self,
        transform_name: str,
        raw_value: Any,
        *,
        context_signature: str = "",
    ) -> Cell:
        mod, version = _TRANSFORMS[transform_name]
        if self.cache is None:
            return mod.clean(raw_value)

        hit = self.cache.lookup(transform_name, version, raw_value, context_signature)
        if hit is not None:
            self.hits += 1
            return hit

        self.misses += 1
        cell = mod.clean(raw_value)
        if not cell.needs_llm:
            self.cache.store(transform_name, version, raw_value, cell, context_signature)
        return cell


# --------------------------------------------------------------------------- #
# Small value helpers                                                          #
# --------------------------------------------------------------------------- #
def _clean_scalar(value: Any) -> Optional[str]:
    """Render a raw cell to a trimmed string, treating NaN/blank as None."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text or None


def _name_parts(cell: Cell) -> dict[str, Any]:
    """Project a parse_name Cell to canonical name fields (last_name required)."""
    value = cell.value if isinstance(cell.value, dict) else {}
    last = value.get("last") or value.get("raw") or None
    return {
        "first_name": value.get("first"),
        "middle_name": value.get("middle"),
        "last_name": last,
        "suffix_raw": value.get("suffix"),
    }


def _resolve_suffix_id(spec: MappingSpec, suffix_raw: Optional[str]) -> Optional[int]:
    """Resolve a raw suffix token to a tenant list_option id via reference_resolution."""
    if not suffix_raw:
        return None
    ref = spec.reference_for("suffix_id")
    if ref is None:
        return None
    return ref.resolved.get(suffix_raw)


def _min_conf(*cells: Optional[Cell]) -> float:
    confs = [c.confidence for c in cells if c is not None]
    return round(min(confs), 4) if confs else 1.0


# Secondary-entity fields that carry data onto a record but are NOT, on their own,
# evidence that the secondary entity exists. A bare surname / middle name / suffix on
# a grave marker does not prove a burial; a first name, a date, or a typed reference
# does. The combined-table builder uses this to decide whether a row's secondary
# entities (e.g. a decedent + interment) should be emitted at all, so empty/reserved
# parents stay parent-only instead of sprouting phantom child records.
_NON_TRIGGER_FIELDS = {
    "last_name", "middle_name", "suffix_id", "maiden_name", "prefix", "title", "title_id",
}

_DATE_PARTS = {"year", "month", "day"}

# Per-entity whitelist of first-class canonical scalar fields the combined builder
# copies straight onto the record; everything else a column targets becomes an
# attribute (Everspot's custom Attribute engine at load time).
_ENTITY_SCALAR_FIELDS = {
    "property": {"property_type_id", "section", "lot", "space", "status_id"},
    "customer": {
        "first_name", "middle_name", "last_name", "suffix_id", "is_organization",
        "organization_name", "status", "email", "contact_phone",
    },
    "interment": {"interment_type_id", "status", "next_of_kin_relation"},
}


def _parse_target(target: Optional[str], primary: str) -> tuple[str, Optional[str], str, Optional[str]]:
    """Resolve a (possibly entity-qualified) mapping target to its destination.

    Grammar (``.``-separated), so a single flat source table can feed several canonical
    entities from one row:

    - ``"section"``                       -> (primary, "section", "field", None)
    - ``"property.section"``              -> ("property", "section", "field", None)
    - ``"customer.attributes.maiden"``    -> ("customer", "maiden", "attr", None)
    - ``"interment.interment_date.year"`` -> ("interment", "interment_date", "date", "year")

    Returns ``(entity, field, kind, part)`` where kind in {field, attr, date}.
    """
    if not target:
        return primary, None, "field", None
    parts = target.split(".")
    if len(parts) == 1:
        return primary, parts[0], "field", None
    if len(parts) == 2:
        return parts[0], parts[1], "field", None
    entity, mid, last = parts[0], parts[1], parts[-1]
    if mid == "attributes":
        return entity, parts[2], "attr", None
    if last in _DATE_PARTS:
        return entity, mid, "date", last
    return entity, last, "attr", None


def _int_or_none(value: Any) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _compose_partial_date(raw_parts: dict[str, Any]) -> tuple[Optional[dict], list[str]]:
    """Build a partialDate {year,month,day,estimated} from split Y/M/D source columns.

    A very common legacy shape (separate Birth Month / Birth Day / Birth Year columns,
    often with 0 placeholders and the odd year leaked into a month field). A 0 (or empty)
    part is a benign "unknown" → null, no flag. A part that is present, non-zero, and
    out of range (e.g. a year sitting in the month column) is genuinely anomalous: it is
    dropped to null and *reported* so the cell can be flagged — never silently coerced.
    Returns ``(partialDate-or-None, out_of_range_parts)``; ``estimated`` is true when the
    date is incomplete (month or day unknown).
    """
    y, m, d = (_int_or_none(raw_parts.get(p)) for p in ("year", "month", "day"))
    out_of_range = [
        name
        for name, val, lo, hi in (("year", y, 1, 9999), ("month", m, 1, 12), ("day", d, 1, 31))
        if val is not None and val != 0 and not (lo <= val <= hi)
    ]
    y = y if (y and 1 <= y <= 9999) else None
    m = m if (m and 1 <= m <= 12) else None
    d = d if (d and 1 <= d <= 31) else None
    # Calendar validity: a day that is in-range but impossible for the month/year
    # (e.g. Apr 31, Feb 29 in a non-leap year) is dropped to null + reported. A true
    # partial date (year-only, year+month) is left intact — it is legitimately partial.
    if y and m and d:
        max_day = calendar.monthrange(y, m)[1]
        if d > max_day:
            out_of_range.append("day")
            d = None
    # A day is meaningless without a month (and the partial-date contract rejects it):
    # drop an orphan day, keeping the year/estimated. Not an anomaly — just incomplete.
    if m is None and d is not None:
        d = None
    if y is None and m is None and d is None:
        return None, out_of_range
    return {"year": y, "month": m, "day": d, "estimated": m is None or d is None}, out_of_range


# --------------------------------------------------------------------------- #
# Per-table assembly                                                           #
# --------------------------------------------------------------------------- #
class _Builder:
    """Accumulates canonical records across tables, mints ids, links FKs."""

    def __init__(
        self,
        ledger: Ledger,
        ext_ids: ExternalIdLedger,
        transformer: _Transformer,
    ) -> None:
        self.ledger = ledger
        self.ext_ids = ext_ids
        self.tx = transformer
        self.records: dict[str, list[dict]] = {}
        self.needs_attention: list[NeedsAttention] = []
        # Per-source-row disposition ledger (count-conservation accounting). Keyed by
        # (table, source_id); insertion order preserved so the on-disk ledger mirrors
        # iteration order.
        self.dispositions: dict[tuple[str, str], Disposition] = {}
        # The property table's external_id-column VALUE (the plot number) → property
        # external_id, so BURIALS/owners can link by the plot value they carry,
        # independent of source-table-name casing.
        self.property_by_plot: dict[str, str] = {}
        self.minted = 0
        self.reused = 0

    # -- disposition accounting ------------------------------------------- #
    def _disp(self, table: str, source_id: str) -> Disposition:
        """Get-or-create the disposition for one source row (idempotent per row)."""
        key = (table, str(source_id))
        d = self.dispositions.get(key)
        if d is None:
            d = Disposition(table=table, source_id=str(source_id))
            self.dispositions[key] = d
        return d

    def _produced(self, table: str, source_id: str, entity: str, external_id: str) -> None:
        self._disp(table, source_id).produced.append(
            {"entity": entity, "external_id": external_id}
        )

    def _deduped(self, table: str, source_id: str, parent_ext: str) -> None:
        self._disp(table, source_id).deduped_into.append(parent_ext)

    def _skipped(self, table: str, source_id: str) -> None:
        self._disp(table, source_id).skipped_out_of_scope = True

    # -- id minting ------------------------------------------------------- #
    def _ext(self, source_id: str, entity: str) -> str:
        before = source_id in self.ext_ids.entries
        ext = self.ext_ids.mint_for(source_id, entity)
        if before:
            self.reused += 1
        else:
            self.minted += 1
        return ext

    def _emit(self, entity: str, record: dict) -> None:
        # Contract gate (SPEC §6.4): validate the LOGICAL canonical record as it is
        # built. An unknown field / missing required field-or-FK / type mismatch is a
        # LOUD failure here instead of a silent drop downstream. Data-quality issues
        # are NOT contract violations — those keep flowing through needs_attention.
        if entity in contract.contract_entities():
            contract.validate_or_raise(entity, record)
        self.records.setdefault(entity, []).append(record)

    def _flag(self, na: NeedsAttention) -> None:
        self.needs_attention.append(na)

    def _apply(
        self,
        transform_name: str,
        raw: Any,
        spec: MappingSpec,
        source_id: str,
        column: Optional[str],
    ) -> Cell:
        """Apply a transform (cache-aware) and surface any unresolved residual.

        When a primitive returns ``needs_llm`` it has explicitly punted the cell to
        the LLM tier (e.g. two-people-in-one-cell, unparseable date). The
        deterministic path still emits its best-effort value, but the cell is NOT
        silently accepted: it becomes a ``needs_llm`` needs-attention item so the operator
        sees the deferred work instead of it vanishing into record confidence. In a
        full run the LLM tier resolves these (``needs_llm`` cleared), so they no
        longer flag — this only lights up genuinely-unresolved cells.

        The detail/context deliberately carry NO raw cell value (it is often PII):
        the cell is identified by source_id + column for lookup.
        """
        cell = self.tx.apply(transform_name, raw)
        if cell.needs_llm:
            reason = cell.meta.get("reason") if isinstance(cell.meta, dict) else None
            self._flag(
                NeedsAttention(
                    kind="needs_llm",
                    table=spec.source_table,
                    source_id=source_id,
                    detail=(
                        f"{transform_name} on column {column!r} was deferred to the LLM tier "
                        f"({reason or cell.method}, confidence {cell.confidence})"
                    ),
                    context={
                        "column": column,
                        "transform": transform_name,
                        "reason": reason,
                        "method": cell.method,
                        "confidence": cell.confidence,
                    },
                )
            )
        return cell

    # -- column helpers --------------------------------------------------- #
    @staticmethod
    def _provenance(table: str, row_index: int, source_id: str) -> dict:
        return {"table": table, "row": row_index + 1, "source_id": source_id}

    def _value_map(
        self,
        spec: MappingSpec,
        col: ColumnMapping,
        raw: Optional[str],
        source_id: str,
    ) -> Optional[Any]:
        """Translate a coded value; surface a NEW code as needs-attention (§5.1)."""
        if raw is None:
            return None
        vs_key = col.value_set_ref or f"{spec.source_table}.{col.source}"
        table = self.ledger.value_sets.get(vs_key, {})
        if raw in table:
            return table[raw]
        # Unknown code: never silently dropped — it becomes a needs-attention item.
        self._flag(
            NeedsAttention(
                kind="unmapped_value",
                table=spec.source_table,
                source_id=source_id,
                detail=f"value-set {vs_key}: code {raw!r} is not mapped",
                context={"column": col.source, "value": raw, "value_set": vs_key},
            )
        )
        return None

    def _resolve_reference(
        self, spec: MappingSpec, field: str, value: Optional[str], source_id: str
    ) -> Optional[int]:
        """Resolve a raw/coded value to a tenant reference id via reference_resolution.

        A value with no resolution (no tenant match in the Wave-0 snapshot) is never
        invented: it is flagged as an ``unresolved_ref`` needs-attention item (surfaced
        in the single question round) and returns None, driving Wave-0b reference
        creation (SPEC §8 stages 6-7).
        """
        if value is None:
            return None
        ref = spec.reference_for(field)
        resolved = ref.resolved.get(value) if ref else None
        if resolved is None:
            self._flag(
                NeedsAttention(
                    kind="unresolved_ref",
                    table=spec.source_table,
                    source_id=source_id,
                    detail=f"{field}: value {value!r} has no tenant reference id (needs Wave-0b create)",
                    context={"field": field, "value": value},
                )
            )
        return resolved

    def _attach_dates(
        self,
        rec: dict[str, Any],
        entity: str,
        dates: dict[tuple[str, str], dict[str, Any]],
        spec: MappingSpec,
        source_id: str,
    ) -> None:
        """Compose every split Y/M/D date the mapping targets at ``entity`` and attach it.

        Generic over the date field name (``dob``/``dod``/``doi``/``interment_date``/…),
        so the mapping declares which dates exist via entity-qualified targets like
        ``interment.dod.year`` and the builder composes whatever is present — no field
        name is hard-coded here.
        """
        for (ent, fld), parts in dates.items():
            if ent != entity:
                continue
            partial, bad = _compose_partial_date(parts)
            if partial is not None:
                rec[fld] = partial
            if bad:
                self._flag(NeedsAttention(
                    kind="data_quality", table=spec.source_table, source_id=source_id,
                    detail=f"{fld} has out-of-range part(s) {bad}; dropped to null",
                    context={"field": fld, "out_of_range": bad},
                ))

    # -- combined flat table → primary + secondary entities --------------- #
    def _build_combined_table(
        self, spec: MappingSpec, df: pd.DataFrame, scope: Optional[set[str]]
    ) -> None:
        """Build a primary entity + its ``secondary_entities`` from one flat table.

        The general path for a single source table whose every row is a parent record
        (e.g. a grave = property) that MAY also carry child records (a decedent customer
        + an interment). Columns route to an entity by an entity-qualified ``target``
        (``property.section``, ``customer.last_name``, ``interment.interment_date.year``);
        an unqualified target lands on the primary entity.

        What this adds over the single-entity builders (each general, not client-specific):
          1. Honors ``secondary_entities`` — the schema's documented multi-entity case
             that the per-target dispatch never read.
          2. De-duplicates the parent across rows by its ``external_id``-action key, so N
             rows sharing one grave become ONE property with N interments.
          3. Emits a secondary entity only when the row carries real evidence of it (a
             triggering field), so empty/reserved parents stay parent-only.
          4. Composes split Y/M/D source columns into partial dates and resolves coded
             values to tenant reference ids, flagging the unresolved instead of guessing.
        """
        primary = spec.target_entity
        secondaries = list(spec.secondary_entities)
        cemetery_ref = "src:cemetery:default"
        group_ext = self._ext("PROPERTY_GROUP:default", "property_group")
        group_emitted = False
        emitted_parent: set[str] = set()

        for idx, row in df.iterrows():
            source_id = row[SOURCE_ID_COL]
            in_scope = scope is None or source_id in scope
            prov = self._provenance(spec.source_table, idx, source_id)

            fields: dict[str, dict[str, Any]] = {e: {} for e in [primary, *secondaries]}
            attrs: dict[str, dict[str, Any]] = {e: {} for e in [primary, *secondaries]}
            dates: dict[tuple[str, str], dict[str, Any]] = {}
            contributing: list[Cell] = []
            triggered: set[str] = set()
            key_parts: list[str] = []

            for col in spec.columns:
                if col.action == "unmapped":
                    continue
                raw = _clean_scalar(row.get(col.source))
                entity, field, kind, part = _parse_target(col.target, primary)

                if col.action == "external_id":
                    key_parts.append(raw or "")
                    if field:
                        fields.setdefault(entity, {})[field] = raw
                    continue
                if raw is None or field is None:
                    continue

                if col.action == "value_map":
                    token = self._value_map(spec, col, raw, source_id)
                    value: Any = token
                    if field.endswith("_id"):
                        value = self._resolve_reference(spec, field, token, source_id)
                    fields.setdefault(entity, {})[field] = value
                    if field not in _NON_TRIGGER_FIELDS:
                        triggered.add(entity)
                    continue

                if kind == "date":
                    dates.setdefault((entity, field), {})[part] = raw
                    if field not in _NON_TRIGGER_FIELDS:
                        triggered.add(entity)
                    continue

                value = raw
                if col.transform in _TRANSFORMS:
                    cell = self._apply(col.transform, raw, spec, source_id, col.source)
                    contributing.append(cell)
                    value = cell.value
                if field.endswith("_id"):
                    value = self._resolve_reference(spec, field, raw, source_id)
                if kind == "attr" or field not in _ENTITY_SCALAR_FIELDS.get(entity, set()):
                    attrs.setdefault(entity, {})[field] = value
                else:
                    fields.setdefault(entity, {})[field] = value
                if field not in _NON_TRIGGER_FIELDS:
                    triggered.add(entity)

            # 1) parent (property), de-duplicated by its external_id key
            parent_src = f"{primary.upper()}:{spec.source_table}:{'|'.join(key_parts)}"
            parent_ext = self.ext_ids.lookup_by_source(parent_src) or self._ext(parent_src, primary)
            if not in_scope:
                # Out-of-scope rows are filtered, not lost — accounted as skipped.
                self._skipped(spec.source_table, source_id)
                continue
            if parent_src not in emitted_parent:
                emitted_parent.add(parent_src)
                if primary == "property" and not group_emitted:
                    self._emit("property_group", {
                        "external_id": group_ext, "name": "Default Section",
                        "cemetery_ref": cemetery_ref, "_provenance": prov, "_confidence": 1.0,
                    })
                    group_emitted = True
                parent: dict[str, Any] = {"external_id": parent_ext}
                if primary == "property":
                    parent["property_group_ref"] = group_ext
                    parent["cemetery_ref"] = cemetery_ref
                parent.update(fields.get(primary, {}))
                if attrs.get(primary):
                    parent["attributes"] = attrs[primary]
                parent["_provenance"] = prov
                parent["_confidence"] = _min_conf(*contributing)
                self._emit(primary, parent)
                self._produced(spec.source_table, source_id, primary, parent_ext)
            else:
                # The parent already exists (multi-occupancy second row) — this row's
                # parent MERGES into it; no new parent record, but the row is accounted.
                self._deduped(spec.source_table, source_id, parent_ext)

            # 2) secondary entities — only when the row carries evidence of them
            if not (triggered & set(secondaries)):
                continue

            decedent_ext = None
            if "customer" in secondaries:
                # A distinct customer per row: a decedent is never merged across rows,
                # even when two rows share a surname (they are different people).
                decedent_ext = self._ext(f"DECEDENT:{source_id}", "customer")
                cust: dict[str, Any] = {
                    "external_id": decedent_ext, "status": "customer",
                    "first_name": None, "middle_name": None, "last_name": None, "suffix_id": None,
                }
                cust.update(fields.get("customer", {}))
                self._attach_dates(cust, "customer", dates, spec, source_id)
                if attrs.get("customer"):
                    cust["attributes"] = attrs["customer"]
                if not cust.get("last_name"):
                    cust["last_name"] = "UNKNOWN"
                    self._flag(NeedsAttention(
                        kind="missing_required", table=spec.source_table, source_id=source_id,
                        detail="customer last_name absent; defaulted to UNKNOWN", context={},
                    ))
                cust["_provenance"] = prov
                cust["_confidence"] = _min_conf(*contributing)
                self._emit("customer", cust)
                self._produced(spec.source_table, source_id, "customer", decedent_ext)

            if "interment" in secondaries:
                interm_ext = self._ext(source_id, "interment")
                interm: dict[str, Any] = {
                    "external_id": interm_ext,
                    "deceased_ref": decedent_ext,
                    "property_ref": parent_ext if primary == "property" else None,
                    "status": _DEFAULT_INTERMENT_STATUS,
                }
                interm.update({k: v for k, v in fields.get("interment", {}).items()
                               if k in _ENTITY_SCALAR_FIELDS["interment"]})
                self._attach_dates(interm, "interment", dates, spec, source_id)
                if attrs.get("interment"):
                    interm["attributes"] = attrs["interment"]
                interm["_provenance"] = prov
                interm["_confidence"] = _min_conf(*contributing)
                self._emit("interment", interm)
                self._produced(spec.source_table, source_id, "interment", interm_ext)

    # -- table dispatch --------------------------------------------------- #
    def build_table(self, spec: MappingSpec, df: pd.DataFrame, scope: Optional[set[str]]) -> None:
        if spec.secondary_entities:
            self._build_combined_table(spec, df, scope)
            return
        target = spec.target_entity
        if target == "customer":
            self._build_customer_table(spec, df, scope)
        elif target == "property":
            self._build_property_table(spec, df, scope)
        elif target == "interment":
            self._build_interment_table(spec, df, scope)
        else:
            # Other primary entities can be added here; nothing in V1 synthetic set.
            pass

    # -- customer + ownership chain (MASTER_OWNERS) ----------------------- #
    def _build_customer_table(self, spec: MappingSpec, df: pd.DataFrame, scope: Optional[set[str]]) -> None:
        for idx, row in df.iterrows():
            source_id = row[SOURCE_ID_COL]
            if scope is not None and source_id not in scope:
                self._skipped(spec.source_table, source_id)
                continue
            cust_ext = self._ext(source_id, "customer")
            cust: dict[str, Any] = {
                "external_id": cust_ext,
                "status": "customer",
                "first_name": None,
                "middle_name": None,
                "last_name": None,
                "suffix_id": None,
            }
            contributing: list[Cell] = []

            for col in spec.columns:
                raw = _clean_scalar(row.get(col.source))
                if col.action == "external_id" or col.action == "unmapped":
                    continue
                if col.action == "split_name":
                    cell = self._apply("parse_name", raw, spec, source_id, col.source)
                    contributing.append(cell)
                    parts = _name_parts(cell)
                    cust["first_name"] = parts["first_name"]
                    cust["middle_name"] = parts["middle_name"]
                    cust["last_name"] = parts["last_name"]
                    cust["suffix_id"] = _resolve_suffix_id(spec, parts["suffix_raw"])
                elif col.action == "value_map":
                    cust[col.target or "status"] = self._value_map(spec, col, raw, source_id) or "lead"
                elif col.action == "map":
                    if col.transform == "normalize_phone":
                        cell = self._apply("normalize_phone", raw, spec, source_id, col.source)
                        contributing.append(cell)
                        cust[col.target] = cell.value
                    elif col.transform in _TRANSFORMS:
                        cell = self._apply(col.transform, raw, spec, source_id, col.source)
                        contributing.append(cell)
                        cust[col.target] = cell.value
                    else:
                        cust[col.target] = raw

            cust["_provenance"] = self._provenance(spec.source_table, idx, source_id)
            cust["_confidence"] = _min_conf(*contributing)
            if not cust.get("last_name"):
                cust["last_name"] = "UNKNOWN"
                self._flag(
                    NeedsAttention(
                        kind="missing_required",
                        table=spec.source_table,
                        source_id=source_id,
                        detail="customer last_name did not parse; defaulted to UNKNOWN",
                        context={},
                    )
                )
            self._emit("customer", cust)
            self._produced(spec.source_table, source_id, "customer", cust_ext)

            # Ownership chain: this owner holds a commitment on a property.
            self._build_ownership_for_owner(spec, row, source_id, cust_ext, idx)

    def _build_ownership_for_owner(
        self,
        spec: MappingSpec,
        row: pd.Series,
        source_id: str,
        owner_ext: str,
        idx: int,
    ) -> None:
        """Emit PropertyCommitment → OwnerFileLine → OwnerFile for an owner row.

        Only built when the owner row references a property (a PLOT_NO link column,
        action=derive → property_ref) AND the property resolves.
        """
        link_col = next(
            (c for c in spec.columns if c.action == "derive" and "property_ref" in (c.targets or [])),
            None,
        )
        if link_col is None:
            return
        plot_raw = _clean_scalar(row.get(link_col.source))
        if plot_raw is None:
            return
        property_ext = self.property_by_plot.get(plot_raw)
        if property_ext is None:
            self._flag(
                NeedsAttention(
                    kind="unresolved_ref",
                    table=spec.source_table,
                    source_id=source_id,
                    detail=f"owner references plot {plot_raw!r} with no resolvable property",
                    context={"plot": plot_raw},
                )
            )
            return

        prov = self._provenance(spec.source_table, idx, source_id)
        cemetery_ref = "src:cemetery:default"

        deed_col = _OWNERSHIP_COLS["deed_number"]
        of_ext = self._ext(f"OWNER_FILE:{source_id}", "owner_file")
        self._emit(
            "owner_file",
            {
                "external_id": of_ext,
                "cemetery_ref": cemetery_ref,
                "deed_number": _clean_scalar(row.get(deed_col)) if deed_col in row.index else None,
                "_provenance": prov,
                "_confidence": 1.0,
            },
        )
        self._produced(spec.source_table, source_id, "owner_file", of_ext)

        commit_ext = self._ext(f"COMMITMENT:{source_id}", "property_commitment")
        sale_cell = None
        amount_cents: Optional[int] = None
        price_col = _OWNERSHIP_COLS["sale_price"]
        if price_col in row.index:
            sale_cell = self._apply("to_cents", _clean_scalar(row.get(price_col)), spec, source_id, price_col)
            amount_cents = sale_cell.value
        committed = None
        commit_kind = "sale" if amount_cents else "reservation"
        commit_date_cell = None
        date_col = _OWNERSHIP_COLS["sale_date"]
        if date_col in row.index:
            commit_date_cell = self._apply("normalize_date", _clean_scalar(row.get(date_col)), spec, source_id, date_col)
            committed = commit_date_cell.value
        self._emit(
            "property_commitment",
            {
                "external_id": commit_ext,
                "property_ref": property_ext,
                "owner_file_ref": of_ext,
                "type": commit_kind,
                "amount_cents": amount_cents,
                "committed_date": committed,
                "_provenance": prov,
                "_confidence": _min_conf(sale_cell, commit_date_cell),
            },
        )
        self._produced(spec.source_table, source_id, "property_commitment", commit_ext)

        ofl_ext = self._ext(f"OWNER_FILE_LINE:{source_id}", "owner_file_line")
        self._emit(
            "owner_file_line",
            {
                "external_id": ofl_ext,
                "owner_file_ref": of_ext,
                "owner_ref": owner_ext,
                "role": "primary",
                "ownership_percentage": None,
                "_provenance": prov,
                "_confidence": 1.0,
            },
        )
        self._produced(spec.source_table, source_id, "owner_file_line", ofl_ext)

    # -- property (PLOTS) ------------------------------------------------- #
    def _build_property_table(self, spec: MappingSpec, df: pd.DataFrame, scope: Optional[set[str]]) -> None:
        group_ext = self._ext("PROPERTY_GROUP:default", "property_group")
        cemetery_ref = "src:cemetery:default"
        group_emitted = False
        key_col = next((c.source for c in spec.columns if c.action == "external_id"), None)
        for idx, row in df.iterrows():
            source_id = row[SOURCE_ID_COL]

            in_scope = scope is None or source_id in scope
            prop_ext = self.ext_ids.lookup_by_source(source_id) or self._ext(source_id, "property")
            # Record the plot-value → property mapping so BURIALS/owners can link by
            # the plot value they carry, even to unchanged (out-of-scope) properties.
            plot_value = _clean_scalar(row.get(key_col)) if key_col else None
            if plot_value is not None:
                self.property_by_plot[plot_value] = prop_ext
            if not in_scope:
                self._skipped(spec.source_table, source_id)
                continue

            if not group_emitted:
                self._emit(
                    "property_group",
                    {
                        "external_id": group_ext,
                        "name": "Default Section",
                        "cemetery_ref": cemetery_ref,
                        "_provenance": self._provenance(spec.source_table, idx, source_id),
                        "_confidence": 1.0,
                    },
                )
                group_emitted = True

            prop: dict[str, Any] = {
                "external_id": prop_ext,
                "property_group_ref": group_ext,
                "cemetery_ref": cemetery_ref,
                "section": None,
                "lot": None,
                "space": None,
            }
            attributes: dict[str, Any] = {}
            contributing: list[Cell] = []
            for col in spec.columns:
                raw = _clean_scalar(row.get(col.source))
                if col.action in ("external_id", "unmapped"):
                    continue
                if col.action == "map" and col.transform in _TRANSFORMS:
                    cell = self._apply(col.transform, raw, spec, source_id, col.source)
                    contributing.append(cell)
                    if col.target in _PROPERTY_SCALAR_FIELDS:
                        prop[col.target] = cell.value
                    else:
                        attributes[col.target] = cell.value
                elif col.action == "map":
                    if col.target in _PROPERTY_SCALAR_FIELDS:
                        prop[col.target] = raw
                    else:
                        attributes[col.target] = raw

            if attributes:
                prop["attributes"] = attributes
            prop["_provenance"] = self._provenance(spec.source_table, idx, source_id)
            prop["_confidence"] = _min_conf(*contributing)
            self._emit("property", prop)
            self._produced(spec.source_table, source_id, "property", prop_ext)

    # -- interment + decedent customer (BURIALS) -------------------------- #
    def _build_interment_table(self, spec: MappingSpec, df: pd.DataFrame, scope: Optional[set[str]]) -> None:
        link_col = next(
            (c for c in spec.columns if c.action == "derive" and "property_ref" in (c.targets or [])),
            None,
        )
        for idx, row in df.iterrows():
            source_id = row[SOURCE_ID_COL]
            if scope is not None and source_id not in scope:
                self._skipped(spec.source_table, source_id)
                continue
            prov = self._provenance(spec.source_table, idx, source_id)

            # 1) The decedent Customer (its external_id is the interment's deceased_ref).
            decedent_ext = self._ext(f"DECEDENT:{source_id}", "customer")
            name_cell = None
            decedent: dict[str, Any] = {
                "external_id": decedent_ext,
                "status": "customer",
                "first_name": None,
                "middle_name": None,
                "last_name": None,
                "suffix_id": None,
            }
            interment_date = None
            date_cell = None
            for col in spec.columns:
                raw = _clean_scalar(row.get(col.source))
                if col.action == "split_name":
                    name_cell = self._apply("parse_name", raw, spec, source_id, col.source)
                    parts = _name_parts(name_cell)
                    decedent["first_name"] = parts["first_name"]
                    decedent["middle_name"] = parts["middle_name"]
                    decedent["last_name"] = parts["last_name"]
                    decedent["suffix_id"] = _resolve_suffix_id(spec, parts["suffix_raw"])
                elif col.action == "map" and col.transform == "normalize_date":
                    date_cell = self._apply("normalize_date", raw, spec, source_id, col.source)
                    interment_date = date_cell.value
            decedent["_provenance"] = prov
            decedent["_confidence"] = _min_conf(name_cell)
            if not decedent.get("last_name"):
                decedent["last_name"] = "UNKNOWN"
            self._emit("customer", decedent)
            self._produced(spec.source_table, source_id, "customer", decedent_ext)

            # 2) The property the burial sits in (derive → property_ref).
            property_ref = None
            if link_col is not None:
                plot_raw = _clean_scalar(row.get(link_col.source))
                if plot_raw is not None:
                    property_ref = self.property_by_plot.get(plot_raw)
                    if property_ref is None:
                        self._flag(
                            NeedsAttention(
                                kind="unresolved_ref",
                                table=spec.source_table,
                                source_id=source_id,
                                detail=f"burial references plot {plot_raw!r} with no resolvable property",
                                context={"plot": plot_raw},
                            )
                        )

            # 3) The Interment — deceased_ref is REQUIRED and non-null.
            interment_ext = self._ext(source_id, "interment")
            interment: dict[str, Any] = {
                "external_id": interment_ext,
                "deceased_ref": decedent_ext,
                "property_ref": property_ref,
                "status": _DEFAULT_INTERMENT_STATUS,
                "_provenance": prov,
                "_confidence": _min_conf(date_cell),
            }
            # The interment date is the canonical partial-date field `doi` (date of
            # interment), NOT a non-existent scalar `interment_date`. normalize_date
            # already returns a {year,month,day,estimated} object, so it drops straight
            # in. (Emitting `interment_date` here breached the Target Contract — see
            # LESSONS #8.)
            if interment_date:
                interment["doi"] = interment_date
            self._emit("interment", interment)
            self._produced(spec.source_table, source_id, "interment", interment_ext)


# --------------------------------------------------------------------------- #
# Orchestration                                                                #
# --------------------------------------------------------------------------- #
def _table_order(specs: dict[str, MappingSpec]) -> list[str]:
    """Build properties first so BURIALS/owners can resolve their property refs."""
    priority = {"property": 0, "property_group": 0, "customer": 1, "interment": 2}
    return sorted(specs, key=lambda t: priority.get(specs[t].target_entity, 9))


def summarize_needs_attention(items: list[NeedsAttention]) -> dict[str, Any]:
    """Aggregate needs-attention items so a large list stays reviewable.

    A dry-run (no LLM tier) can defer tens of thousands of cells; an item-per-cell
    list buries the high-stakes structural cases (e.g. two-people-in-one-cell, which
    changes record counts) among routine low-confidence values (2-digit years). The
    summary groups by kind, and within ``needs_llm`` by ``transform/reason``, so the
    distribution — not the raw volume — is what surfaces in the single question round.
    """
    by_kind = Counter(na.kind for na in items)
    by_reason = Counter(
        f"{na.context.get('transform', '?')}/{na.context.get('reason') or na.context.get('method', '?')}"
        for na in items
        if na.kind == "needs_llm"
    )
    return {
        "total": len(items),
        "by_kind": dict(by_kind.most_common()),
        "needs_llm_by_reason": dict(by_reason.most_common()),
    }


def _load_scope(delta_path: Path) -> Optional[set[str]]:
    """CHANGED + NEW source_ids from delta.json (None when no delta → full run)."""
    if not delta_path.exists():
        return None
    data = json.loads(delta_path.read_text(encoding="utf-8"))
    scope: set[str] = set()
    for td in (data.get("tables") or {}).values():
        scope.update(td.get("new") or [])
        scope.update(td.get("changed") or [])
    return scope


def assemble(
    project_root: str | Path,
    snapshot: str,
    *,
    use_cache: bool = True,
    scoped: bool = True,
) -> AssembleResult:
    """Assemble the canonical graph for one snapshot.

    Args:
        project_root: The project dir (holds ``ledger/``, ``snapshots/``, ``runs/``).
        snapshot: e.g. ``"v1"``.
        use_cache: Wire the Tier-3 transform cache (the value-level parse memory).
        scoped: On v2+, restrict to CHANGED + NEW via ``delta.json`` (operating-model
            §5.4). On v1 (no delta) the whole snapshot is built.

    Returns:
        :class:`AssembleResult` with entity counts, mint/reuse + cache stats, and
        the needs-attention list.
    """
    root = Path(project_root)
    ledger_dir = root / "ledger"
    tables_dir = root / "snapshots" / snapshot / "tables"
    canonical_dir = root / "runs" / snapshot / "canonical"
    canonical_dir.mkdir(parents=True, exist_ok=True)

    ledger = Ledger.load(ledger_dir)
    ext_ids = ExternalIdLedger(ledger_dir / "external_ids.json")
    scope = _load_scope(root / "snapshots" / snapshot / "delta.json") if scoped else None

    cache_cm = TransformCache(ledger_dir) if use_cache else None
    cache = cache_cm if use_cache else None
    transformer = _Transformer(cache)
    builder = _Builder(ledger, ext_ids, transformer)

    try:
        for table in _table_order(ledger.mappings):
            spec = ledger.mappings[table]
            parquet = tables_dir / f"{table}.parquet"
            if not parquet.exists():
                continue
            df = pd.read_parquet(parquet)
            builder.build_table(spec, df, scope)
    finally:
        if cache_cm is not None:
            cache_cm.close()

    ext_ids.save()

    result = AssembleResult(canonical_dir=canonical_dir)
    result.minted = builder.minted
    result.reused = builder.reused
    result.cache_hits = transformer.hits
    result.cache_misses = transformer.misses
    result.needs_attention = builder.needs_attention
    result.dispositions = list(builder.dispositions.values())

    for entity, records in builder.records.items():
        path = canonical_dir / f"{entity}.ndjson"
        with path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, default=str) + "\n")
        result.entity_counts[entity] = len(records)
        result.written_files.append(path)

    # Per-source-row disposition ledger — the count-conservation evidence the validate
    # gate reconciles against the manifest's true row totals (H1). One entry per source
    # row the assembler iterated; written as its own artifact so a downstream stage reads
    # it without parsing the whole assemble_report.
    disp_summary = summarize_dispositions(result.dispositions)
    dispositions_doc = {
        "assemble_version": VERSION,
        "snapshot": snapshot,
        "summary": disp_summary,
        "dispositions": [d.to_dict() for d in result.dispositions],
    }
    (canonical_dir / "dispositions.json").write_text(
        json.dumps(dispositions_doc, indent=2, default=str), encoding="utf-8"
    )

    report = {
        "assemble_version": VERSION,
        "snapshot": snapshot,
        "scoped": scope is not None,
        "scoped_count": len(scope) if scope is not None else None,
        "entity_counts": result.entity_counts,
        "minted": result.minted,
        "reused": result.reused,
        "cache_hits": result.cache_hits,
        "cache_misses": result.cache_misses,
        "disposition_summary": disp_summary,
        "needs_attention_summary": summarize_needs_attention(result.needs_attention),
        "needs_attention": [na.to_dict() for na in result.needs_attention],
    }
    (canonical_dir / "assemble_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    _soft_validate(canonical_dir, result)
    return result


def summarize_dispositions(dispositions: list[Disposition]) -> dict[str, Any]:
    """Aggregate the per-row disposition ledger into reviewable totals.

    Reports how many source rows the assembler iterated and, of those, how many
    produced entities / deduped / were skipped / errored / went unaccounted. This is
    the assemble-side half of the conservation story; validate joins it against the
    manifest's true row total to surface rows the assembler never iterated at all.
    """
    produced = deduped = skipped = errored = unaccounted = 0
    produced_by_entity: Counter = Counter()
    for d in dispositions:
        if d.produced:
            produced += 1
            for p in d.produced:
                produced_by_entity[p["entity"]] += 1
        if d.deduped_into:
            deduped += 1
        if d.skipped_out_of_scope:
            skipped += 1
        if d.errored:
            errored += 1
        if not d.accounted:
            unaccounted += 1
    return {
        "rows_iterated": len(dispositions),
        "rows_produced_entities": produced,
        "rows_deduped": deduped,
        "rows_skipped_out_of_scope": skipped,
        "rows_errored": errored,
        "rows_unaccounted": unaccounted,
        "entities_produced": dict(produced_by_entity.most_common()),
    }


# --------------------------------------------------------------------------- #
# Soft schema validation (only if jsonschema is importable)                    #
# --------------------------------------------------------------------------- #
def _soft_validate(canonical_dir: Path, result: AssembleResult) -> None:
    """Validate each NDJSON line against canonical-record.schema.json, if available.

    The validator's ``$ref``s are resolved via the modern ``referencing`` library (the
    replacement for the deprecated ``jsonschema.RefResolver``). The guard catches BOTH
    ``ImportError`` (no jsonschema) AND ``AttributeError`` (a future jsonschema that has
    removed ``RefResolver`` while ``referencing`` is also absent) so this soft check can
    never crash the stage AFTER the canonical artifact has already been written.
    """
    try:
        import jsonschema

        import validate as validate_mod
    except ImportError:  # pragma: no cover - soft check
        return
    schema_path = (
        Path(__file__).resolve().parent.parent / "schemas" / "canonical-record.schema.json"
    )
    if not schema_path.exists():
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    defs = schema.get("$defs", {})

    failures = 0
    for entity, _ in result.entity_counts.items():
        if entity not in defs:
            continue
        try:
            validator = validate_mod._make_ref_validator(jsonschema, schema, entity)
        except AttributeError:  # pragma: no cover - RefResolver removed AND no referencing
            return
        path = canonical_dir / f"{entity}.ndjson"
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            errors = list(validator.iter_errors(record))
            if errors:
                failures += 1
                if failures <= 10:
                    print(
                        f"[assemble] schema FAIL {entity}.ndjson:{line_no}: "
                        f"{errors[0].message}"
                    )
    if failures:
        print(f"[assemble] ⚠ {failures} canonical record(s) failed schema validation.")
    else:
        print("[assemble] ✓ canonical records validate against canonical-record.schema.json")
