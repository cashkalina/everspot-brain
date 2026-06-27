"""Stage 5 — Auto-draft mapping (SPEC §8 stage 5).

A DETERMINISTIC best-effort drafter. Given a profiled snapshot + the Target Contract
(§6) + the tenant reference snapshot (``ledger/reference_data.json``), it proposes,
for each source column, a target ``entity.field`` and an action — by name/shape match
against the contract's LOGICAL fields, using the data-shape signals the profiler
already computed (§8 stage 3). It resolves value-set candidates against the existing
tenant ``list_options`` via :mod:`resolve_list_option` (the library primitive, by name
— never reinvented), proposing ``source_value -> id`` mappings; values that don't
resolve cleanly become GAPS (questions), never invented ids.

Output (writes ONLY if a settled ledger is absent — never clobbers human decisions;
falls back to a ``.draft`` sidecar when a settled mapping already exists):
  - ``ledger/mapping.yaml``       a DRAFT mapping (schema-conformant; assemble reads it)
  - ``ledger/value_sets.yaml``    DRAFT value-set translations
  - ``runs/<v>/mapping_review.md`` human-readable: confident mappings, value-set
                                   resolutions, and the GAPS the question round closes

HONEST SCOPE (SPEC §8 stage 5 caveat). Deterministic drafting handles the obvious
1:1 column->field mappings, split Y/M/D partial-date families, and value-set
resolution against existing tenant list_options. It DEFERS (emits a structural gap
rather than guessing):
  - which entity a flat row primarily IS, and its ``secondary_entities`` routing
    (one flat row -> Property + Customer + Interment) — a multi-entity decision that
    exceeds deterministic drafting; the orchestrator's AI stage + the question round
    decide it;
  - any required target field with no confidently-matched source column;
  - value-set values that don't resolve to a real tenant list_option id.

This module is GENERAL — it carries no client column names; every match keys off the
column's name SHAPE and profiled signals at run time.

Design references: SPEC §6 (contract authority), §8 stage 3/5, §9 (gaps -> questions).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

try:
    from rapidfuzz import fuzz
except ImportError:  # pragma: no cover
    fuzz = None  # type: ignore

import contract
import resolve_list_option

VERSION = "1.0.0"

# Confidence floors. A column draft at/above HIGH is a recorded default; below it is a
# GAP the question round surfaces. Value-set resolution reuses resolve_list_option's
# own strong/weak thresholds (so the library stays the source of truth).
_HIGH = 0.85
_NAME_FUZZ_STRONG = 88.0   # column-name <-> field-name fuzzy score for a confident 1:1
_NAME_FUZZ_WEAK = 72.0     # below strong but plausible -> low-confidence draft / gap
# A coded low-cardinality column is checked against list_option TYPE names with a
# looser bar (a "type" coded column is a strong value-set signal even when its name is
# abbreviated, e.g. ITYPE -> interment_type). The resolution is still id-by-id, and
# unresolved values still become questions, so a loose name match is safe here.
_VALUE_SET_FUZZ = 78.0


# --------------------------------------------------------------------------- #
# Name-shape -> contract-field hints (generic English tokens, never client names) #
# --------------------------------------------------------------------------- #
# Token aliases: source-column tokens that strongly imply a logical target field.
# Keyed by the contract field's bare name; the values are the column-name tokens
# (from profile) that map to it. General Everspot/legacy vocabulary only.
_FIELD_TOKEN_ALIASES: dict[str, set[str]] = {
    "first_name": {"first", "fname", "firstname", "given", "forename"},
    "last_name": {"last", "lname", "lastname", "surname", "sur", "family"},
    "middle_name": {"middle", "mname", "mid", "middlename"},
    "company_name": {"company", "organization", "org", "business"},
    "contact_email": {"email", "mail", "e"},
    "contact_phone": {"phone", "tel", "telephone", "mobile", "cell"},
    "section": {"section", "sec", "block"},
    "lot": {"lot", "row"},
    "space": {"space", "grave", "sp"},
    "age": {"age"},
    "next_of_kin_relation": {"relation", "relationship", "nok", "kin"},
}

# A column whose tokens hit one of these maps to the named partial-date logical field.
_DATE_FIELD_TOKENS: dict[str, set[str]] = {
    "dob": {"birth", "born", "dob", "birthdate"},
    "dod": {"death", "died", "dod", "deathdate", "deceased"},
    "doi": {"interment", "interred", "buried", "burial", "doi"},
}
_DATE_PART_TOKENS = {"year": {"year", "yr", "yyyy"}, "month": {"month", "mon", "mm"}, "day": {"day", "dd"}}


# Required-on-insert target fields with an OBVIOUS default (SPEC §9.3 confident
# default, not a question). A historical migrated customer/interment is settled
# (completed); active status is the customer norm. GENERAL Everspot facts, not client.
_DEFAULTABLE_REQUIRED: dict[tuple[str, str], Any] = {
    ("interment", "status"): "completed",
    ("customer", "status"): "active",
}


def _tokens(name: str) -> set[str]:
    return set(re.split(r"[^a-z0-9]+", name.lower())) - {""}


def _fuzz(a: str, b: str) -> float:
    if fuzz is None:  # pragma: no cover
        return 100.0 if a.lower() == b.lower() else 0.0
    return float(fuzz.WRatio(a.lower(), b.lower()))


# --------------------------------------------------------------------------- #
# Draft data structures                                                        #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class ColumnDraft:
    """One drafted source-column decision."""

    source: str
    action: str                     # map | value_map | external_id | unmapped
    target: Optional[str] = None    # entity.field (or entity.field.part for dates)
    value_set_ref: Optional[str] = None
    confidence: float = 0.0
    note: str = ""
    is_gap: bool = False            # True -> surfaces in the question round
    gap_kind: Optional[str] = None  # value_set | unmapped | source_key | missing_required


@dataclass(slots=True)
class ValueSetDraft:
    table: str
    column: str
    target_field: str
    list_option_type: str
    resolved: dict[str, Any] = field(default_factory=dict)   # source_value -> id
    missing: list[str] = field(default_factory=list)         # values that didn't resolve
    fuzzy: list[str] = field(default_factory=list)           # resolved ONLY via a non-exact (fuzzy ≥90) match
    truncated: bool = False                                  # profiler capped the value set (codes unseen)


@dataclass(slots=True)
class TableDraft:
    table: str
    primary_entity: str
    secondary_entities: list[str]
    columns: list[ColumnDraft]
    value_sets: list[ValueSetDraft]
    reference_resolution: list[dict[str, Any]]
    primary_inferred: bool          # True -> the entity routing is a DEFERRED structural guess
    gaps: list[dict[str, Any]]      # missing-required / structural gaps (not per-column)


# --------------------------------------------------------------------------- #
# Entity routing (the structural decision — deterministically inferred, flagged) #
# --------------------------------------------------------------------------- #
# A flat burial register typically yields property (primary) + customer + interment.
# We can DETECT the shape (grave-locator signals + name signals + date signals) but
# the routing is a structural decision the drafter DEFERS: it proposes the standard
# burial split and marks it inferred so the question round can confirm/override.
def _infer_entity_routing(table_profile: dict[str, Any]) -> tuple[str, list[str], bool]:
    cols = table_profile.get("columns", {})
    signals = table_profile.get("signals", {})
    coltoks = {c: _tokens(c) for c in cols}

    has_locator = any(
        toks & (_FIELD_TOKEN_ALIASES["section"] | _FIELD_TOKEN_ALIASES["lot"] | _FIELD_TOKEN_ALIASES["space"])
        for toks in coltoks.values()
    )
    has_name = "name" in signals or any(
        toks & (_FIELD_TOKEN_ALIASES["first_name"] | _FIELD_TOKEN_ALIASES["last_name"])
        for toks in coltoks.values()
    )
    has_dates = "date" in signals or any(
        toks & set().union(*_DATE_FIELD_TOKENS.values()) for toks in coltoks.values()
    )

    if has_locator and (has_name or has_dates):
        # Standard flat-register burial split. DEFERRED structural guess.
        return "property", ["customer", "interment"], True
    if has_name and has_dates:
        return "customer", ["interment"], True
    if has_locator:
        return "property", [], True
    if has_name:
        return "customer", [], True
    # Genuinely undecidable shape -> let the question round/AI decide.
    return "", [], True


# --------------------------------------------------------------------------- #
# Column -> field matching                                                     #
# --------------------------------------------------------------------------- #
def _candidate_fields(entities: list[str]) -> list[tuple[str, str, dict[str, Any]]]:
    """All (entity, field, spec) across the candidate entities, scalars + lists + dates.

    Envelope/provenance + ref fields are excluded — refs are produced structurally by
    assemble (parent external_ids), not mapped from a source column.
    """
    out: list[tuple[str, str, dict[str, Any]]] = []
    for entity in entities:
        for name, spec in contract.entity_fields(entity).items():
            if name.startswith("_") or name == "external_id":
                continue
            if spec.get("type") in ("ref", "external_id", "object"):
                continue
            out.append((entity, name, spec))
    return out


def _match_date_field(toks: set[str], entities: list[str]) -> Optional[tuple[str, str, str]]:
    """A split Y/M/D part column -> (entity, partial_date_field, part) if it fits."""
    part = next((p for p, pt in _DATE_PART_TOKENS.items() if toks & pt), None)
    if part is None:
        return None
    family = next((f for f, ft in _DATE_FIELD_TOKENS.items() if toks & ft), None)
    if family is None:
        return None
    for entity in entities:
        spec = contract.entity_fields(entity).get(family)
        if spec and spec.get("type") == "partial_date":
            return entity, family, part
    return None


def _best_field_for_column(
    column: str, toks: set[str], candidates: list[tuple[str, str, dict[str, Any]]]
) -> Optional[tuple[str, str, dict[str, Any], float]]:
    """Best (entity, field, spec, score 0..1) for a column by token-alias + fuzzy name."""
    best: Optional[tuple[str, str, dict[str, Any], float]] = None
    for entity, fname, spec in candidates:
        score = 0.0
        aliases = _FIELD_TOKEN_ALIASES.get(fname, set())
        if toks & aliases:
            score = 0.97
        else:
            fz = _fuzz(column, fname)
            if fz >= _NAME_FUZZ_STRONG:
                score = 0.9
            elif fz >= _NAME_FUZZ_WEAK:
                score = 0.6
        if score and (best is None or score > best[3]):
            best = (entity, fname, spec, score)
    return best


# --------------------------------------------------------------------------- #
# Value-set drafting                                                           #
# --------------------------------------------------------------------------- #
def _draft_value_set(
    table: str,
    column: str,
    profile_values: dict[str, int],
    entity: str,
    field_name: str,
    list_option_type: str,
    reference_data: dict[str, Any],
    *,
    truncated: bool = False,
) -> ValueSetDraft:
    """Resolve each distinct source code to a real tenant list_option id (or GAP it).

    ``resolve_list_option`` reports confidence tiers: an EXACT key/name match returns
    confidence 1.0; a strong FUZZY (≥90) match still resolves to an id but at <1.0 with
    a ``fuzzy`` provenance flag; weak/unknown values stay unresolved. We record the
    fuzzy-only resolutions separately so the caller can keep them OPEN (a fuzzy hit is a
    candidate, not a certainty). ``truncated`` (from the profiler) means codes beyond the
    value-freq cap were never seen, so the resolution can't claim completeness.
    """
    rows = (reference_data.get("list_options", {}) or {}).get(list_option_type, []) or []
    options = resolve_list_option.build_options(rows)
    resolved: dict[str, Any] = {}
    missing: list[str] = []
    fuzzy: list[str] = []
    for raw in profile_values:
        cell = resolve_list_option.clean(raw, options)
        if cell.value is not None and cell.confidence >= resolve_list_option._STRONG_MATCH / 100.0:
            resolved[raw] = int(cell.value)
            if cell.meta.get("fuzzy") or cell.confidence < 1.0:
                fuzzy.append(raw)
        else:
            missing.append(raw)
    return ValueSetDraft(
        table=table, column=column, target_field=field_name,
        list_option_type=list_option_type, resolved=resolved, missing=missing,
        fuzzy=fuzzy, truncated=truncated,
    )


# --------------------------------------------------------------------------- #
# Per-table drafting                                                           #
# --------------------------------------------------------------------------- #
def _distinct_values(column_profile: dict[str, Any]) -> dict[str, int]:
    """Fallback distinct value set from a profile column's capped sample (freq unknown→1)."""
    return {str(v): 1 for v in column_profile.get("sample", [])}


def _value_set_field_for_column(
    column: str, toks: set[str], entities: list[str]
) -> Optional[tuple[str, str, str]]:
    """A low-cardinality coded column whose name matches a list_option field.

    Matches on (a) shared tokens between the column and the field's base name / its
    list_option type slug, or (b) a strong fuzzy match against either — so e.g.
    ``itype`` resolves to ``interment_type_id`` even with no shared token.
    """
    best: Optional[tuple[float, str, str, str]] = None
    for entity in entities:
        for fname, lo_type in contract.list_option_fields(entity).items():
            base = fname[:-3] if fname.endswith("_id") else fname
            name_pool = _tokens(base) | {lo_type, *_tokens(lo_type)}
            if toks & name_pool:
                return entity, fname, lo_type
            fz = max(_fuzz(column, base), _fuzz(column, lo_type))
            if fz >= _VALUE_SET_FUZZ and (best is None or fz > best[0]):
                best = (fz, entity, fname, lo_type)
    if best:
        return best[1], best[2], best[3]
    return None


def draft_table(
    table: str,
    table_profile: dict[str, Any],
    reference_data: dict[str, Any],
    source_key: Optional[list[str]] = None,
    key_status: str = "confirmed",
) -> TableDraft:
    primary, secondaries, inferred = _infer_entity_routing(table_profile)
    entities = [e for e in (primary, *secondaries) if e]
    candidates = _candidate_fields(entities) if entities else []
    lo_fields = {e: contract.list_option_fields(e) for e in entities}

    cols_profile = table_profile.get("columns", {})
    value_set_cols = set(table_profile.get("value_set_candidates", {}).keys())
    # Locator columns that map to property.section/lot/space ARE the grave-identity
    # (the property dedup key) on the standard burial-register shape — drafted as
    # external_id so assemble dedups the property by them (SPEC §7.2).
    locator_fields = {"section", "lot", "space"}
    key_cols = {str(c).lower() for c in (source_key or [])}

    column_drafts: list[ColumnDraft] = []
    value_set_drafts: list[ValueSetDraft] = []
    mapped_fields: set[tuple[str, str]] = set()  # (entity, field) confidently mapped

    for column, cp in cols_profile.items():
        toks = _tokens(column)
        signals = set(cp.get("signals", []))

        # All-blank / export-artifact column -> confident unmapped (recorded default).
        if cp.get("non_null", 0) == 0:
            column_drafts.append(ColumnDraft(
                source=column, action="unmapped", confidence=1.0,
                note="All-blank column — ignored (export artifact).",
            ))
            continue

        # 0) confirmed source_key columns -> external_id (the record/grave identity).
        #    A locator-named key column (section/lot/space) also names the property field
        #    so assemble can both dedup AND write the location; a non-locator key column
        #    (a plain id/account/composite token) is a pure external_id with no target.
        if column in key_cols and primary == "property":
            locator_field = next(
                (lf for lf in locator_fields if toks & _FIELD_TOKEN_ALIASES[lf]), None
            )
            column_drafts.append(ColumnDraft(
                source=column, action="external_id",
                target=(f"property.{locator_field}" if locator_field else None),
                confidence=1.0,
                note=("Source-key locator -> property identity (dedup key + location)."
                      if locator_field else "Source-key column -> property external_id (grave identity)."),
            ))
            if locator_field:
                mapped_fields.add(("property", locator_field))
            continue

        # 1) value-set: a coded column whose name matches a list_option field. The
        #    list_option binding (contract authority) wins over the profiler's
        #    cardinality heuristic — but we still require the column to be low-ish
        #    cardinality (it is a CODE, not free text) to avoid value-mapping a name.
        vs_hit = _value_set_field_for_column(column, toks, entities) if entities else None
        is_codeish = column in value_set_cols or (cp.get("distinct", 1_000_000) <= 50)
        if vs_hit and is_codeish:
            entity, fname, lo_type = vs_hit
            vs_candidate = table_profile.get("value_set_candidates", {}).get(column, {})
            vs_values = vs_candidate.get("values") or _distinct_values(cp)
            vs = _draft_value_set(
                table, column, vs_values, entity, fname, lo_type, reference_data,
                truncated=bool(vs_candidate.get("truncated")),
            )
            value_set_drafts.append(vs)
            n_total = len(vs.resolved) + len(vs.missing)
            conf = (len(vs.resolved) / n_total) if n_total else 0.0
            draft = ColumnDraft(
                source=column, action="value_map", target=f"{entity}.{fname}",
                value_set_ref=f"{table}.{column}", confidence=round(conf, 3),
                note=f"{len(vs.resolved)}/{n_total} values resolved to {lo_type} list_options.",
            )
            # A value-set only settles (records a confident default) when EVERY code
            # resolved EXACTLY and the profiler saw the WHOLE set. Surface a gap when:
            #   - any code did not resolve (unknown/weak code);
            #   - any code resolved ONLY via a non-exact fuzzy ≥90 match (a candidate,
            #     not a certainty — confidence must reflect the fuzzy nature, not 1.0);
            #   - the profiler truncated the value set (codes beyond the cap unseen, so
            #     completeness can't be claimed).
            if vs.missing:
                draft.is_gap = True
                draft.gap_kind = "value_set"
                draft.note += f" Unresolved: {vs.missing}."
            if vs.fuzzy:
                draft.is_gap = True
                draft.gap_kind = "value_set"
                # Cap confidence below 1.0 to reflect the weakest fuzzy match seen.
                fuzz_conf = min(
                    (resolve_list_option._STRONG_MATCH / 100.0 for _ in vs.fuzzy),
                    default=conf,
                )
                draft.confidence = round(min(draft.confidence, fuzz_conf), 3)
                draft.note += f" Fuzzy (non-exact) resolution — confirm: {vs.fuzzy}."
            if vs.truncated:
                draft.is_gap = True
                draft.gap_kind = "value_set"
                draft.note += (
                    " Profiler-TRUNCATED value set — codes beyond the cap were never seen; "
                    "completeness unconfirmed."
                )
            if not draft.is_gap:
                mapped_fields.add((entity, fname))
            column_drafts.append(draft)
            continue

        # 2) split Y/M/D partial-date family.
        if entities:
            date_hit = _match_date_field(toks, entities)
            if date_hit:
                entity, family, part = date_hit
                column_drafts.append(ColumnDraft(
                    source=column, action="map", target=f"{entity}.{family}.{part}",
                    confidence=0.95,
                    note=f"Split-date part -> {entity}.{family} ({part}).",
                ))
                mapped_fields.add((entity, family))
                continue

        # 3) general 1:1 column -> field by alias / fuzzy name match.
        best = _best_field_for_column(column, toks, candidates) if candidates else None
        if best:
            entity, fname, spec, score = best
            # Don't re-map a field already taken by a source-key locator (avoids a
            # plot_no->lot collision when a real `lot` column also exists).
            if (entity, fname) in mapped_fields:
                score = min(score, 0.6)
            draft = ColumnDraft(
                source=column, action="map", target=f"{entity}.{fname}",
                confidence=round(score, 3),
                note=f"Name match -> {entity}.{fname} (score {score:.2f}).",
            )
            if score < _HIGH:
                draft.is_gap = True
                draft.gap_kind = "unmapped"
                draft.note += " Low confidence — confirm in the question round."
            else:
                mapped_fields.add((entity, fname))
            column_drafts.append(draft)
            continue

        # 4) nothing matched -> unmapped, low confidence; flag only if it might feed a
        #    required field (it can't here since it didn't match) -> note + recorded default.
        column_drafts.append(ColumnDraft(
            source=column, action="unmapped", confidence=0.5,
            note="No confident contract field — left unmapped (review).",
        ))

    # Structural gaps: required-on-insert target fields with NO mapped source column.
    # A field with an OBVIOUS default (§9.3) carries a ``default`` so the question round
    # auto-resolves it instead of asking; a genuinely-unknown one stays a question.
    gaps: list[dict[str, Any]] = []
    for entity in entities:
        for fname, spec in contract.entity_fields(entity).items():
            if not spec.get("required_on_insert"):
                continue
            if fname == "external_id" or spec.get("type") in ("ref", "external_id"):
                continue  # external_id + parent refs are produced structurally by assemble
            if (entity, fname) not in mapped_fields:
                default = _DEFAULTABLE_REQUIRED.get((entity, fname))
                gap: dict[str, Any] = {
                    "kind": "missing_required",
                    "entity": entity,
                    "field": fname,
                    "detail": f"{entity}.{fname} is required-on-insert but no source column mapped to it.",
                }
                if default is not None:
                    gap["default"] = default
                    gap["detail"] += f" Obvious default: {default!r}."
                gaps.append(gap)

    # Source-key gap (the structural identity question, §5.1 / §9.2).
    if not source_key or key_status == "deferred":
        gaps.append({
            "kind": "source_key",
            "entity": None,
            "field": None,
            "detail": f"Table {table!r} has no confirmed stable source_key — which column(s) uniquely identify a record?",
            "candidate_keys": [k["columns"] for k in table_profile.get("candidate_keys", [])[:3]],
        })

    # The value_map chain is: source_value --(value_sets.target_value)--> token
    # --(reference_resolution.resolved)--> tenant id. So reference_resolution must be
    # keyed by the SAME slug token value_sets.yaml emits (not the raw source value).
    reference_resolution = [
        {
            "field": vs.target_field,
            "via": "list_options",
            "type": vs.list_option_type,
            "resolved": {_slug(raw): _id for raw, _id in vs.resolved.items()},
            "missing": [_slug(m) for m in vs.missing],
        }
        for vs in value_set_drafts
    ]

    return TableDraft(
        table=table,
        primary_entity=primary,
        secondary_entities=secondaries,
        columns=column_drafts,
        value_sets=value_set_drafts,
        reference_resolution=reference_resolution,
        primary_inferred=inferred,
        gaps=gaps,
    )


# --------------------------------------------------------------------------- #
# YAML serialization (schema-conformant mapping.yaml + value_sets.yaml)         #
# --------------------------------------------------------------------------- #
def _mapping_payload(drafts: list[TableDraft]) -> dict[str, Any]:
    tables = []
    for td in drafts:
        cols = []
        for c in td.columns:
            entry: dict[str, Any] = {"source": c.source, "action": c.action}
            if c.target:
                entry["target"] = c.target
            if c.value_set_ref:
                entry["value_set_ref"] = c.value_set_ref
            entry["confidence"] = c.confidence
            if c.note:
                entry["note"] = c.note
            cols.append(entry)
        block: dict[str, Any] = {
            "source_table": td.table,
            "target_entity": td.primary_entity,
        }
        if td.secondary_entities:
            block["secondary_entities"] = list(td.secondary_entities)
        block["columns"] = cols
        if td.reference_resolution:
            block["reference_resolution"] = td.reference_resolution
        tables.append(block)
    return {"schema_version": 1, "draft": True, "draft_version": VERSION, "tables": tables}


def _value_sets_payload(drafts: list[TableDraft]) -> dict[str, Any]:
    value_sets = []
    for td in drafts:
        for vs in td.value_sets:
            values = []
            # Resolved codes carry the resolved token AS the canonical id is already in
            # reference_resolution; the value_set maps source_value -> a stable token
            # (here the raw, lowercased) so assemble's value_map + reference_resolution
            # chain works. We keep the resolved ones; missing ones are recorded with a
            # null target so the question round fills them.
            for raw in {**{k: v for k, v in vs.resolved.items()}}:
                values.append({"source_value": raw, "target_value": _slug(raw)})
            for raw in vs.missing:
                values.append({"source_value": raw, "target_value": None})
            value_sets.append({
                "table": vs.table,
                "column": vs.column,
                "target_field": vs.target_field,
                "description": f"Drafted {vs.list_option_type} resolution.",
                "values": values,
            })
    return {"schema_version": 1, "draft": True, "value_sets": value_sets}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower()).strip("_")


# --------------------------------------------------------------------------- #
# Review markdown (rendered FROM the drafts)                                   #
# --------------------------------------------------------------------------- #
def render_review(drafts: list[TableDraft]) -> str:
    lines = ["# Mapping draft review (auto-drafted)", ""]
    lines.append("Deterministic best-effort draft (SPEC §8 stage 5). Confident 1:1 mappings + ")
    lines.append("value-set resolutions are recorded; GAPS below are what the question round closes.")
    lines.append("")
    for td in drafts:
        lines.append(f"## Table `{td.table}`")
        routing = f"{td.primary_entity or '(undecided)'}"
        if td.secondary_entities:
            routing += " + " + " + ".join(td.secondary_entities)
        flag = "  ⚠ INFERRED (deferred structural decision — confirm)" if td.primary_inferred else ""
        lines.append(f"- **Entity routing:** {routing}{flag}")
        lines.append("")

        confident = [c for c in td.columns if c.action in ("map", "value_map", "external_id") and not c.is_gap]
        gaps_cols = [c for c in td.columns if c.is_gap]
        ignored = [c for c in td.columns if c.action == "unmapped"]

        lines.append("### Confident mappings")
        if confident:
            for c in confident:
                lines.append(f"- `{c.source}` → `{c.target}` ({c.action}, conf {c.confidence}) — {c.note}")
        else:
            lines.append("- _(none)_")
        lines.append("")

        if td.value_sets:
            lines.append("### Value-set resolutions")
            for vs in td.value_sets:
                lines.append(f"- `{vs.column}` → `{vs.target_field}` ({vs.list_option_type}): "
                             f"resolved {vs.resolved}; unresolved {vs.missing}")
            lines.append("")

        lines.append("### Gaps (→ question round)")
        had_gap = False
        for c in gaps_cols:
            had_gap = True
            lines.append(f"- [{c.gap_kind}] `{c.source}` → `{c.target}` — {c.note}")
        for g in td.gaps:
            had_gap = True
            loc = f"{g.get('entity')}.{g.get('field')}" if g.get("entity") else g.get("kind")
            lines.append(f"- [{g['kind']}] {loc} — {g['detail']}")
        if td.primary_inferred and td.primary_entity:
            had_gap = True
            lines.append(f"- [entity_routing] confirm `{td.table}` is `{td.primary_entity}`"
                         + (f" + {td.secondary_entities}" if td.secondary_entities else ""))
        if not had_gap:
            lines.append("- _(none)_")
        lines.append("")

        if ignored:
            lines.append("### Ignored columns")
            for c in ignored:
                lines.append(f"- `{c.source}` — {c.note}")
            lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class DraftResult:
    drafts: list[TableDraft]
    mapping_path: Path
    value_sets_path: Path
    review_path: Path
    wrote_mapping: bool
    settled_existed: bool


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def compute_drafts(
    project_root: str | Path,
    snapshot: str,
    *,
    sources: Optional[list[dict[str, Any]]] = None,
) -> list[TableDraft]:
    """Compute the per-table drafts (gap analysis) WITHOUT writing any file.

    Used by ``discover`` so it can derive the gap questions without touching a settled
    ledger at all (not even a sidecar).
    """
    root = Path(project_root)
    profile_dir = root / "snapshots" / snapshot / "profile"
    if not (profile_dir / "summary.json").exists():
        raise FileNotFoundError(f"no profile at {profile_dir} — run `migrate profile` first.")
    summary = _load_json(profile_dir / "summary.json")
    reference_data = _load_json(root / "ledger" / "reference_data.json")
    key_by_table = {s["table"]: s for s in (sources or [])}

    drafts: list[TableDraft] = []
    for table in summary.get("tables", {}):
        tp = _load_json(profile_dir / f"{table}.json")
        src = key_by_table.get(table, {})
        drafts.append(draft_table(
            table, tp, reference_data,
            source_key=src.get("source_key"),
            key_status=src.get("key_status", "deferred" if not src else "confirmed"),
        ))
    return drafts


def map_draft(
    project_root: str | Path,
    snapshot: str,
    *,
    sources: Optional[list[dict[str, Any]]] = None,
) -> DraftResult:
    """Draft mapping.yaml + value_sets.yaml + mapping_review.md for a profiled snapshot.

    Never clobbers a settled (non-draft) mapping: if ``ledger/mapping.yaml`` exists and
    is NOT marked ``draft: true``, the draft is written to ``mapping.yaml.draft`` /
    ``value_sets.yaml.draft`` sidecars instead (SPEC §8 stage 5).
    """
    import yaml

    root = Path(project_root)
    drafts = compute_drafts(root, snapshot, sources=sources)

    ledger_dir = root / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    mapping_path = ledger_dir / "mapping.yaml"
    value_sets_path = ledger_dir / "value_sets.yaml"

    settled_existed = False
    if mapping_path.exists():
        existing = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
        if not existing.get("draft"):
            settled_existed = True

    wrote_mapping = True
    if settled_existed:
        mapping_path = ledger_dir / "mapping.yaml.draft"
        value_sets_path = ledger_dir / "value_sets.yaml.draft"

    mapping_path.write_text(
        yaml.safe_dump(_mapping_payload(drafts), sort_keys=False), encoding="utf-8"
    )
    value_sets_path.write_text(
        yaml.safe_dump(_value_sets_payload(drafts), sort_keys=False), encoding="utf-8"
    )

    run_dir = root / "runs" / snapshot
    run_dir.mkdir(parents=True, exist_ok=True)
    review_path = run_dir / "mapping_review.md"
    review_path.write_text(render_review(drafts), encoding="utf-8")

    return DraftResult(
        drafts=drafts,
        mapping_path=mapping_path,
        value_sets_path=value_sets_path,
        review_path=review_path,
        wrote_mapping=wrote_mapping,
        settled_existed=settled_existed,
    )
