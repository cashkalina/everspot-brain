"""The Target Contract loader (SPEC §6.4) — one validator, three call sites.

Loads ``contract/target_schema.json`` (the codebase-derived LOGICAL definition of
every target entity, produced by ``php artisan migration:generate-contract``) and
exposes :func:`validate_record`. ``assemble.py``, ``emit_excel.py`` and
``orion_load.py`` all call it, so an unknown field, a missing required field/FK, a
type mismatch, an FK that is not a ``*_ref`` external_id string, or a malformed
partial-date object becomes a LOUD build/load-time failure instead of a silent drop.

It validates the canonical record as it stands in the NDJSON artifact (§7.1) —
i.e. BEFORE ``orion_load``/``emit`` flatten ``*_ref`` -> internal ids or expand
partial-date objects into ``_year/_month/_day/_estimated`` columns. That keeps a
single schema: the same logical record is the contract everywhere.

This module is GENERAL — it reads the committed contract; it carries no client
column names (those live in each project's mapping.yaml).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

_CONTRACT_PATH = (
    Path(__file__).resolve().parent.parent / "contract" / "target_schema.json"
)

_PARTIAL_DATE_KEYS = {"year", "month", "day", "estimated"}
_EXTERNAL_ID_PREFIX = "src:"

# Logical type -> the python types a non-null canonical value may take.
_PY_TYPES: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "object": (dict,),
}


@dataclass(frozen=True)
class Violation:
    """A single contract breach. Callers choose to raise (build/load) vs flag."""

    entity: str
    field: Optional[str]
    kind: str  # unknown_field | missing_required | type_mismatch | bad_ref | bad_partial_date | unknown_entity
    detail: str

    def __str__(self) -> str:
        loc = f"{self.entity}.{self.field}" if self.field else self.entity
        return f"[contract:{self.kind}] {loc}: {self.detail}"


class ContractViolation(Exception):
    """Raised when a record breaches the Target Contract (used by build/load paths)."""

    def __init__(self, violations: list[Violation]) -> None:
        self.violations = violations
        super().__init__(
            f"{len(violations)} contract violation(s):\n  "
            + "\n  ".join(str(v) for v in violations)
        )


class _Contract:
    """Lazily-loaded, cached view of the committed target_schema.json."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: Optional[dict[str, Any]] = None

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            if not self._path.exists():
                raise FileNotFoundError(
                    f"Target Contract not found at {self._path}. "
                    "Run `php artisan migration:generate-contract` first."
                )
            self._data = json.loads(self._path.read_text(encoding="utf-8"))
        return self._data

    def entity(self, entity: str) -> Optional[dict[str, Any]]:
        return self.data.get("entities", {}).get(entity)


_CONTRACT = _Contract(_CONTRACT_PATH)


def _is_external_id(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(_EXTERNAL_ID_PREFIX)


def _check_partial_date(entity: str, field: str, value: Any) -> list[Violation]:
    if not isinstance(value, dict):
        return [Violation(entity, field, "bad_partial_date",
                          f"expected a partial-date object, got {type(value).__name__}")]
    out: list[Violation] = []
    extra = set(value.keys()) - _PARTIAL_DATE_KEYS
    if extra:
        out.append(Violation(entity, field, "bad_partial_date",
                             f"unexpected keys {sorted(extra)} (allowed: year/month/day/estimated)"))
    for part in ("year", "month", "day"):
        pv = value.get(part)
        if pv is not None and not isinstance(pv, int):
            out.append(Violation(entity, field, "bad_partial_date",
                                 f"{part} must be int or null, got {type(pv).__name__}"))
    if "estimated" in value and not isinstance(value["estimated"], bool):
        out.append(Violation(entity, field, "bad_partial_date",
                             f"estimated must be bool, got {type(value['estimated']).__name__}"))
    return out


def _check_type(entity: str, field: str, spec: dict[str, Any], value: Any) -> list[Violation]:
    ftype = spec.get("type", "string")

    if ftype in ("ref", "external_id"):
        if not _is_external_id(value):
            return [Violation(entity, field, "bad_ref",
                              f"FK/ref must be a 'src:...' external_id string, got {value!r}")]
        return []

    if ftype == "partial_date":
        return _check_partial_date(entity, field, value)

    py_types = _PY_TYPES.get(ftype, (str,))
    # bool is a subclass of int in python — guard integer/number against bools.
    if ftype in ("integer", "number") and isinstance(value, bool):
        return [Violation(entity, field, "type_mismatch",
                          f"expected {ftype}, got boolean")]
    if not isinstance(value, py_types):
        return [Violation(entity, field, "type_mismatch",
                          f"expected {ftype}, got {type(value).__name__}")]
    return []


def validate_record(entity: str, record: dict[str, Any]) -> list[Violation]:
    """Validate one LOGICAL canonical record against the Target Contract.

    Returns a (possibly empty) list of :class:`Violation`. Callers decide whether
    to raise (build/load-time) or flag (data-quality surfacing). Detects:
    unknown field, missing required_on_insert field/FK, type mismatch, an FK that
    is not a ``*_ref`` external_id string, and partial-date shape errors.

    Envelope/provenance keys are accepted on every entity. ``None`` values are
    allowed on any nullable field and skip type-checking.
    """
    entity_def = _CONTRACT.entity(entity)
    if entity_def is None:
        return [Violation(entity, None, "unknown_entity",
                          f"entity {entity!r} is not in the Target Contract")]

    fields: dict[str, Any] = entity_def["fields"]
    out: list[Violation] = []

    # 1) unknown fields (the contract is closed — additionalProperties:false).
    for key in record:
        if key not in fields:
            out.append(Violation(entity, key, "unknown_field",
                                 f"field not in contract for {entity} (silent-drop guard)"))

    # 2) per-field: required + type.
    for name, spec in fields.items():
        present = name in record
        value = record.get(name)

        if spec.get("required_on_insert") and (not present or value is None):
            out.append(Violation(entity, name, "missing_required",
                                 "required-on-insert field is absent or null"))
            continue

        if not present or value is None:
            continue

        out.extend(_check_type(entity, name, spec, value))

    return out


def validate_or_raise(entity: str, record: dict[str, Any]) -> None:
    """Validate and raise :class:`ContractViolation` on any breach (build/load path)."""
    violations = validate_record(entity, record)
    if violations:
        raise ContractViolation(violations)


def contract_entities() -> list[str]:
    """The entity names the contract covers (for callers that iterate/guard)."""
    return list(_CONTRACT.data.get("entities", {}).keys())


def entity_fields(entity: str) -> dict[str, dict[str, Any]]:
    """The LOGICAL field specs for an entity (`{field: {type, nullable, ...}}`).

    Used by the auto-draft mapper (SPEC §8 stage 5) to know each target field's
    type / required_on_insert / fk_target / list_option_type / partial-date columns
    WITHOUT re-reading the raw schema. Returns ``{}`` for an unknown entity.
    """
    entity_def = _CONTRACT.entity(entity)
    return dict(entity_def["fields"]) if entity_def else {}


def list_option_fields(entity: str) -> dict[str, str]:
    """``{field: list_option_type}`` for an entity's value-set fields (overlay-bound)."""
    return {
        name: spec["list_option_type"]
        for name, spec in entity_fields(entity).items()
        if spec.get("list_option_type")
    }


def reload_contract() -> None:
    """Drop the cached contract (used by tests after regeneration)."""
    _CONTRACT._data = None
