"""Stage 10 — Validate. Schema + contract + referential integrity + count conservation.

The "correctness" review lens (SPEC §15.3). Reads the run's canonical NDJSON
(``runs/<v>/canonical/*.ndjson``) and answers, deterministically and offline:

  1. **schema + contract conformance** — every canonical record validates against
     ``schemas/canonical-record.schema.json`` AND ``contract.validate_record(entity, rec)``.
  2. **referential integrity** — every ``*_ref`` resolves to an existing record of the
     RIGHT entity within the canonical set (``deceased_ref`` → a customer external_id,
     ``property_ref`` → a property, ``*_group_ref`` → a property_group). A dangling FK is
     a BLOCKING failure. (``cemetery_ref`` points at the Wave-0b cemetery prerequisite,
     not a canonical entity, so it is verified for shape but never counted as dangling.)
  3. **required-field / unresolved-reference** — required_on_insert fields present;
     value-set ``*_id`` fields resolved (not raw codes / null where required).
  4. **count conservation** — the manifest's TRUE per-table source-row totals reconciled
     against the per-source-row disposition ledger (``canonical/dispositions.json``) via
     :func:`reconcile.conserve`. An UNEXPLAINED drop (a manifest row with no disposition —
     real data loss) is BLOCKING; legitimate fan-in / dedup / out-of-scope is not. This
     replaces the old self-derived provenance count, which could never see a dropped row.
  5. **field-level sampling** — a sample of low-``_confidence`` / ``needs_attention``
     records surfaced for review (warning, not blocking).

Gate semantics (SPEC §15.3 / §9.2-3):
  - **BLOCKING (FAIL)**: contract violation, schema violation, dangling FK, a missing
    required field that data cannot fill.
  - **WARNING (PASS-with-warnings)**: low-confidence cells, unresolved value-set refs
    queued for Wave-0b creation, cosmetic data-quality flags.

Writes ``runs/<v>/validation/{validation_summary.json, failures.jsonl}`` and returns a
PASS/FAIL gate. GENERAL — no client column names; everything keys off the canonical
schema + the committed contract.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import contract
import reconcile as reconcile_mod

VERSION = "1.0.0"

# A *_ref whose target entity is one of these is a Wave-0b PREREQUISITE (created by the
# reference-reconcile stage), NOT a member of the canonical record set — so a ref to it
# is verified for external_id shape but is never counted as a dangling FK.
_PREREQUISITE_REF_ENTITIES = {"cemetery", "list_option", "property_type"}

# Field-name → the canonical entity the FK must point at. Most ``<x>_ref`` fields target
# entity ``<x>``; these are the documented aliases where the name differs from the entity
# (SPEC §7.2: decedents/next-of-kin/owners ARE customers; a *_group_ref is a
# property_group). Used to catch a ref pointing at the WRONG kind of record.
_REF_FIELD_ENTITY = {
    "deceased_ref": "customer",
    "next_of_kin_ref": "customer",
    "owner_ref": "customer",
    "parent_ref": "customer",
    "property_group_ref": "property_group",
    "owner_file_ref": "owner_file",
}


def _expected_ref_entity(field: str) -> Optional[str]:
    """The canonical entity a ``<x>_ref`` field must point at (None = derive from value)."""
    if field in _REF_FIELD_ENTITY:
        return _REF_FIELD_ENTITY[field]
    if field.endswith("_ref"):
        return field[: -len("_ref")]
    return None

# Confidence below this surfaces a record in the field-level sample (warning lens).
_LOW_CONFIDENCE = 0.7
_SAMPLE_CAP = 25


def _ref_entity(ref: str) -> Optional[str]:
    """Parse the target entity out of a ``src:<entity>:<token>`` external_id ref."""
    if not isinstance(ref, str) or not ref.startswith("src:"):
        return None
    parts = ref.split(":", 2)
    return parts[1] if len(parts) >= 2 else None


@dataclass(slots=True)
class Failure:
    entity: str
    external_id: Optional[str]
    kind: str  # contract | schema | dangling_ref | missing_required | unresolved_ref | count_conservation
    field: Optional[str]
    detail: str
    blocking: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity,
            "external_id": self.external_id,
            "kind": self.kind,
            "field": self.field,
            "detail": self.detail,
            "blocking": self.blocking,
        }


@dataclass(slots=True)
class ValidationResult:
    snapshot: str
    gate: str = "PASS"
    failures: list[Failure] = field(default_factory=list)
    entity_counts: dict[str, int] = field(default_factory=dict)
    conservation: list[dict[str, Any]] = field(default_factory=list)
    conservation_summary: dict[str, Any] = field(default_factory=dict)
    low_confidence_sample: list[dict[str, Any]] = field(default_factory=list)
    warnings: dict[str, int] = field(default_factory=dict)

    @property
    def blocking_failures(self) -> list[Failure]:
        return [f for f in self.failures if f.blocking]

    @property
    def passed(self) -> bool:
        return not self.blocking_failures


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def _load_canonical(canonical_dir: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for path in sorted(canonical_dir.glob("*.ndjson")):
        out[path.stem] = _read_ndjson(path)
    return out


def _ext_ledger_index(ledger_path: Path) -> dict[str, str]:
    """``{external_id: entity}`` from ``ledger/external_ids.json`` (empty if absent).

    Every already-minted/loaded record the tenant holds — including parents an
    out-of-scope row produced on an earlier drop. Used (scoped runs only) to satisfy a
    ref pointing at a record this delta did not re-emit. The entity is recorded on each
    ledger entry, so a ref to the WRONG kind of record is still caught as dangling.
    """
    data = _read_json(ledger_path) or {}
    index: dict[str, str] = {}
    for rec in (data.get("entries") or {}).values():
        ext = rec.get("external_id")
        entity = rec.get("entity")
        if ext and entity:
            index[ext] = entity
    return index


# --------------------------------------------------------------------------- #
# Schema validation (canonical-record.schema.json, if jsonschema available)    #
# --------------------------------------------------------------------------- #
def _make_ref_validator(jsonschema, schema: dict, entity: str):
    """Build a Draft202012 validator for the ``$defs/<entity>`` sub-schema.

    Its ``$ref``s (``#/$defs/partialDate``, ``#/$defs/externalId``, …) must resolve
    against the FULL document, not the sub-schema. Prefers the modern ``referencing``
    library (the replacement for the deprecated ``jsonschema.RefResolver``, which a future
    jsonschema will REMOVE): the whole schema document is registered as a Resource under a
    stable id and the validator's own schema is a one-line ``{"$ref": "<id>#/$defs/<entity>"}``
    pointer, so same-document ``#/$defs/…`` refs resolve at the ROOT (not relative to the
    sub). Falls back to the legacy ``RefResolver`` only when ``referencing`` is unavailable;
    if NEITHER is available the caller's broadened guard degrades safely. GENERAL — no
    client knowledge, pure schema plumbing.
    """
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012

        root_id = schema.get("$id") or "urn:canonical-record-schema"
        resource = Resource(contents=schema, specification=DRAFT202012)
        registry: Registry = Registry().with_resource(uri=root_id, resource=resource)
        ref_schema = {"$ref": f"{root_id}#/$defs/{entity}"}
        return jsonschema.Draft202012Validator(ref_schema, registry=registry)
    except ImportError:  # pragma: no cover - exercised only without `referencing`
        resolver = jsonschema.RefResolver.from_schema(schema)
        return jsonschema.Draft202012Validator(schema["$defs"][entity], resolver=resolver)


def _schema_validator(schema_path: Path):
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return None
    if not schema_path.exists():
        return None
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    defs = schema.get("$defs", {})

    def validate(entity: str, record: dict) -> list[str]:
        if entity not in defs:
            return []
        try:
            validator = _make_ref_validator(jsonschema, schema, entity)
        except AttributeError:  # pragma: no cover - RefResolver removed AND no referencing
            return []
        return [e.message for e in validator.iter_errors(record)]

    return validate


# --------------------------------------------------------------------------- #
# Core validation                                                              #
# --------------------------------------------------------------------------- #
def validate_canonical(
    canonical: dict[str, list[dict]],
    *,
    snapshot: str,
    conservation: Optional[dict[str, Any]] = None,
    schema_validator=None,
    scoped: bool = False,
    ext_ledger_index: Optional[dict[str, str]] = None,
) -> ValidationResult:
    """Validate an in-memory canonical record set; the pure core (no I/O).

    ``conservation`` is the disposition-vs-manifest summary from
    :func:`reconcile.conserve` (manifest = true source-row count, disposition ledger =
    what became of each row). An ``unexplained_dropped`` shortfall is a BLOCKING
    count-conservation failure; legitimate fan-in / dedup / out-of-scope is not.

    ``scoped`` + ``ext_ledger_index`` close the M2 gap: on a scoped (CHANGED + NEW)
    run only in-scope records are emitted, so an in-scope child whose UNCHANGED parent
    was not re-emitted would otherwise dangle. The parent already exists in the tenant —
    its external_id is in ``ledger/external_ids.json``. ``ext_ledger_index`` is that
    ledger's ``{external_id: entity}`` map; when ``scoped`` is True it SEEDS the
    resolution index in addition to the in-run canonical, so a ref to an already-minted/
    loaded external_id is SATISFIED, not dangling. A FULL run (``scoped`` False) ignores
    the ledger so a genuinely-missing parent is still flagged.
    """
    result = ValidationResult(snapshot=snapshot)
    contract_entities = set(contract.contract_entities())

    # Build the external_id → entity index across the whole canonical set, so a *_ref can
    # be resolved to an existing record of the RIGHT entity. On a scoped run, seed it FIRST
    # from the external_id ledger (already-minted/loaded records the tenant holds but this
    # delta did not re-emit) so an in-scope ref to an unchanged parent is not dangling; the
    # in-run canonical then overlays it (a re-emitted record's entity always wins).
    ext_to_entity: dict[str, str] = {}
    if scoped and ext_ledger_index:
        ext_to_entity.update(ext_ledger_index)
    for entity, records in canonical.items():
        for rec in records:
            ext = rec.get("external_id")
            if ext:
                ext_to_entity[ext] = entity

    for entity, records in canonical.items():
        result.entity_counts[entity] = len(records)
        for rec in records:
            ext = rec.get("external_id")

            # 1) contract conformance (BLOCKING).
            if entity in contract_entities:
                for v in contract.validate_record(entity, rec):
                    result.failures.append(Failure(
                        entity, ext, "contract", v.field, str(v), blocking=True,
                    ))

            # 2) schema conformance (BLOCKING).
            if schema_validator is not None:
                for msg in schema_validator(entity, rec):
                    result.failures.append(Failure(
                        entity, ext, "schema", None, msg, blocking=True,
                    ))

            # 3) referential integrity: every *_ref resolves (BLOCKING for dangling).
            for fname, value in rec.items():
                if not fname.endswith("_ref") or value is None:
                    continue
                target_entity = _ref_entity(value)
                if target_entity in _PREREQUISITE_REF_ENTITIES:
                    continue  # Wave-0b prerequisite, not a canonical member
                if value not in ext_to_entity:
                    result.failures.append(Failure(
                        entity, ext, "dangling_ref", fname,
                        f"{fname}={value!r} resolves to no canonical record", blocking=True,
                    ))
                    continue
                actual = ext_to_entity[value]
                # The ref must point at the entity the FIELD NAME implies (deceased_ref →
                # customer, property_ref → property, *_group_ref → property_group). A ref to
                # the wrong kind of record is a dangling FK even if the id exists.
                expected = _expected_ref_entity(fname)
                if expected is not None and expected not in _PREREQUISITE_REF_ENTITIES and actual != expected:
                    result.failures.append(Failure(
                        entity, ext, "dangling_ref", fname,
                        f"{fname}={value!r} points at a {actual}, expected {expected}",
                        blocking=True,
                    ))

            # 4) unresolved value-set *_id fields (WARNING — Wave-0b will create them).
            #    A raw, non-integer code left in an *_id field means the value-set did not
            #    resolve to a tenant list_option id.
            for fname, value in rec.items():
                if fname in ("external_id",) or fname.endswith("_ref"):
                    continue  # the record's own id / FK external_ids are not value-set ids
                if fname.endswith("_id") and value is not None and not isinstance(value, int):
                    result.failures.append(Failure(
                        entity, ext, "unresolved_ref", fname,
                        f"{fname}={value!r} is not a resolved tenant id (Wave-0b create)",
                        blocking=False,
                    ))

            # 5) field-level sample of low-confidence records (WARNING).
            conf = rec.get("_confidence")
            if isinstance(conf, (int, float)) and conf < _LOW_CONFIDENCE:
                if len(result.low_confidence_sample) < _SAMPLE_CAP:
                    result.low_confidence_sample.append({
                        "entity": entity, "external_id": ext, "_confidence": conf,
                    })

    # 6) count conservation — disposition ledger vs the manifest's TRUE row totals.
    #    An UNEXPLAINED drop (a manifest source row with no disposition) is BLOCKING:
    #    real data loss. Legitimate fan-in/dedup/out-of-scope is informational. Each
    #    per-entity row restates produced→canonical for the §15.2 surface; the headline
    #    verdict is the disposition summary (which alone can SEE a dropped row).
    if conservation:
        result.conservation_summary = conservation
        produced_by_entity = conservation.get("entities_produced", {})
        for entity in sorted(set(produced_by_entity) | set(result.entity_counts)):
            src_n = produced_by_entity.get(entity, result.entity_counts.get(entity, 0))
            canon_n = result.entity_counts.get(entity, 0)
            result.conservation.append({
                "entity": entity,
                "source_rows": src_n,
                "canonical_records": canon_n,
                "conserved": src_n == canon_n,
                "dropped": max(0, src_n - canon_n),
            })
        unexplained = int(conservation.get("unexplained_dropped", 0))
        if unexplained > 0:
            total = conservation.get("manifest_total_rows", "?")
            accounted = conservation.get("accounted", "?")
            result.failures.append(Failure(
                entity="*", external_id=None, kind="count_conservation", field=None,
                detail=(
                    f"{unexplained} source row(s) UNEXPLAINED — manifest has {total} row(s), "
                    f"only {accounted} accounted (produced/deduped/skipped/errored). "
                    "Likely an unmapped/unhandled source table or rows that produced nothing."
                ),
                blocking=True,
            ))

    # Roll up warning counts by kind.
    warn = {}
    for f in result.failures:
        if not f.blocking:
            warn[f.kind] = warn.get(f.kind, 0) + 1
    result.warnings = warn
    result.gate = "PASS" if result.passed else "FAIL"
    return result


# --------------------------------------------------------------------------- #
# Run-level orchestration (reads the canonical dir + writes the artifacts)      #
# --------------------------------------------------------------------------- #
def validate_run(project_root: str | Path, snapshot: str) -> ValidationResult:
    root = Path(project_root)
    canonical_dir = root / "runs" / snapshot / "canonical"
    if not canonical_dir.is_dir():
        raise FileNotFoundError(f"no canonical dir at {canonical_dir} — run `migrate assemble` first.")
    out_dir = root / "runs" / snapshot / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    canonical = _load_canonical(canonical_dir)

    # Count conservation: reconcile the per-source-row disposition ledger (what assemble
    # recorded happened to each row) against the manifest's TRUE per-table row totals
    # (the real number of source rows the client handed us). This is general — it keys off
    # the manifest + dispositions, never a client column — and, unlike the old
    # self-derived provenance count, it can SEE a dropped row (a manifest row with no
    # disposition). A shortfall is a BLOCKING count-conservation failure.
    manifest = _read_json(root / "snapshots" / snapshot / "manifest.json")
    dispositions = reconcile_mod.load_dispositions(canonical_dir)
    conservation = reconcile_mod.conserve(manifest, dispositions)

    # A run is SCOPED when this snapshot carries a delta.json (the CHANGED + NEW filter
    # assemble applied). On a scoped run an in-scope child can reference an UNCHANGED
    # parent the delta did not re-emit; that parent already exists in the tenant, so we
    # let the external_id ledger satisfy the ref (M2). A full run (no delta) ignores it.
    scoped = (root / "snapshots" / snapshot / "delta.json").exists()
    ext_ledger_index = (
        _ext_ledger_index(root / "ledger" / "external_ids.json") if scoped else None
    )

    schema_path = (
        Path(__file__).resolve().parent.parent / "schemas" / "canonical-record.schema.json"
    )
    result = validate_canonical(
        canonical, snapshot=snapshot, conservation=conservation,
        schema_validator=_schema_validator(schema_path),
        scoped=scoped, ext_ledger_index=ext_ledger_index,
    )

    # failures.jsonl — every failure row (blocking + warning), one per line.
    failures_path = out_dir / "failures.jsonl"
    with failures_path.open("w", encoding="utf-8") as fh:
        for f in result.failures:
            fh.write(json.dumps(f.to_dict()) + "\n")

    summary = {
        "validation_version": VERSION,
        "snapshot": snapshot,
        "gate": result.gate,
        "entity_counts": result.entity_counts,
        "blocking": _count_blocking_by_kind(result),
        "warnings": result.warnings,
        "count_conservation": result.conservation,
        "conservation_summary": result.conservation_summary,
        "low_confidence_sample": result.low_confidence_sample,
    }
    (out_dir / "validation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return result


def _count_blocking_by_kind(result: ValidationResult) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in result.blocking_failures:
        out[f.kind] = out.get(f.kind, 0) + 1
    # Always surface dangling_ref + count_conservation as keys (0 when clean) — both are
    # headline metrics for the §15.2 review surface.
    out.setdefault("dangling_ref", 0)
    out.setdefault("count_conservation", 0)
    return out


def render_gate_line(result: ValidationResult) -> str:
    n_block = len(result.blocking_failures)
    n_warn = sum(result.warnings.values())
    if result.passed:
        return f"GATE: PASS ({n_warn} warning(s), 0 blocking)"
    return f"GATE: FAIL ({n_block} blocking failure(s), {n_warn} warning(s))"
