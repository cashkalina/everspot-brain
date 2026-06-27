"""Stage 8 — Emit. Canonical NDJSON → wave-ordered Everspot import ``.xlsx`` files.

Reads the canonical, external-id-keyed artifact (one NDJSON file per entity,
plan §4.2) and writes one ``.xlsx`` per importer, columns matching each importer's
**documented schema** (the header keys its ``onRow()`` mapping + ``rules()`` read,
snake_cased the way Laravel-Excel's ``WithHeadingRow`` normalizes them).

Files are numbered by **wave dependency order** (plan §3.1 / operating-model §3) so
the operator uploads them in sequence. **V1 scope is the NON-FINANCIAL core only:**

    Wave 1  property_group → property        |  customer        (parallel)
    Wave 2  property_commitment / owner_file_line  ;  interment   ← V1 core ends here
    Wave 3+ order, order_line, payment_plan, …      (v1.1 — financial, NOT in v1)

The financial importers (Wave 3-4) are intentionally left as ``# v1.1`` stubs below
and are **excluded from the default emit** (see :data:`V1_IMPORTERS`).

FK resolution across waves (operating-model §2, §5.4; external_ids.py)
---------------------------------------------------------------------
The importers reference Everspot **internal ids** for foreign keys, but the canonical
artifact carries **external_id refs** (the ``*_ref`` fields, plan §4.2). Internal ids
only exist *after* a record's wave is loaded, so we resolve FKs **between waves** via
the External-IDs harvest (Stage 9). Concretely, each FK importer-column ``X_id`` is
backed by a canonical ``X_ref`` field and the emitter does, per row:

  * If an ``id_map`` (``{external_id -> everspot internal id}``, harvested between
    waves) resolves the ref → write the **internal id** into the importer's ``X_id``.
  * Otherwise (first emit, parent wave not yet loaded) → leave ``X_id`` blank and
    write the external_id into a **companion ``X_ref`` column** so the operator can
    resolve it after the harvest. The RUNBOOK spells out this harvest step.

This keeps a single emit codepath whether or not ids are resolved yet, and stays
consistent with the wave/ID-harvest design in the operating model.

everspot-brain doc that specifies the rules:
    system-wiki/system/imports.md  + the per-importer column docs
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from openpyxl import Workbook

import contract

VERSION = "2.0.0"

# Control characters the OOXML/xlsx format forbids (everything < 0x20 except tab,
# newline, carriage return, plus DEL). openpyxl raises IllegalCharacterError on these,
# so any dirty source value that survives into a canonical string would crash the
# emitter. We strip them defensively at the write boundary — they are never legitimate
# content — so one stray byte in one cell can't fail an entire wave export.
_ILLEGAL_XLSX_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _xlsx_safe(value: Any) -> Any:
    """Strip xlsx-illegal control characters from string cell values (pass-through else)."""
    if isinstance(value, str):
        return _ILLEGAL_XLSX_CHARS.sub("", value)
    return value


# --------------------------------------------------------------------------- #
# Column-source descriptors                                                    #
# --------------------------------------------------------------------------- #
@dataclass(slots=True, frozen=True)
class FK:
    """A foreign-key importer column backed by a canonical ``*_ref`` field.

    ``id_column`` is the importer's internal-id column (e.g. ``property_id``);
    ``ref_field`` is the canonical external_id ref it draws from (e.g.
    ``property_ref``). When the ref resolves via the ``id_map`` we emit the
    internal id; otherwise we leave the id column blank and surface the raw ref
    in a companion ``<id_column>_ref`` column.
    """

    ref_field: str


@dataclass(slots=True, frozen=True)
class PartialDate:
    """One component (``year``/``month``/``day``/``estimated``) of a canonical
    partial-date object ``{year, month, day, estimated}`` (plan §4.2)."""

    field: str
    part: str  # "year" | "month" | "day" | "estimated"


# A column source is one of:
#   str          -> a plain canonical field name copied through
#   FK           -> an external_id ref resolved to an internal id (or companion ref)
#   PartialDate  -> one component of a partial-date object
#   Callable     -> derived value ``(record) -> value``
ColumnSource = str | FK | PartialDate | Callable[[dict], Any]


@dataclass(slots=True)
class ImporterSpec:
    """One Everspot importer: its wave, source NDJSON entity, and column map."""

    importer: str
    wave: int
    entity: str  # canonical NDJSON file stem, e.g. "customer"
    columns: dict[str, ColumnSource] = field(default_factory=dict)
    sheet_name: Optional[str] = None
    in_v1: bool = True
    note: str = ""

    @property
    def filename_stem(self) -> str:
        return f"wave{self.wave}_{self.importer}"


def _pd_component(record: dict, field_name: str, part: str) -> Any:
    """Pull one component out of a partial-date field ``{year,month,day,estimated}``."""
    val = record.get(field_name)
    if isinstance(val, dict):
        return val.get(part)
    return None


# --------------------------------------------------------------------------- #
# Importer column maps — GROUND-TRUTHED against the importer source files.      #
#                                                                              #
#   customer            modules/Customer/Imports/CustomerImport.php            #
#   property_group      modules/Property/Imports/PropertyGroupImport.php       #
#   property            modules/Property/Imports/PropertyImport.php            #
#   property_commitment modules/Property/Imports/PropertyCommitmentImport.php  #
#   owner_file_line     modules/Common/Imports/OwnerFileLineImport.php         #
#   interment           modules/Interment/Imports/IntermentImport.php          #
#                                                                              #
# Keys below are the exact heading keys each importer reads (WithHeadingRow    #
# snake_cases them); values map to the canonical NDJSON field they draw from.  #
# --------------------------------------------------------------------------- #
IMPORTERS: list[ImporterSpec] = [
    # ----- Wave 1 — Customer (parallel with property tree) -------------------
    ImporterSpec(
        importer="customer",
        wave=1,
        entity="customer",
        columns={
            "external_id": "external_id",
            "status": "status",
            "model_no": "model_no",
            "type_id": "type_id",
            "title_id": "title_id",
            "first_name": "first_name",
            "middle_name": "middle_name",
            "last_name": "last_name",
            "maiden_name": "maiden_name",
            "suffix_id": "suffix_id",
            "company_name": "company_name",
            "contact_email": "contact_email",
            "contact_phone": "contact_phone",  # canonical: already digits-only
            "parent_id": FK("parent_ref"),  # customer -> customer (self-ref)
            # Address block — only consumed when has_address is truthy.
            # state = code (e.g. "CA"), country = name (e.g. "United States").
            "has_address": "has_address",
            "address_external_id": "address_external_id",
            "line_one": "line_one",
            "line_two": "line_two",
            "line_three": "line_three",
            "city": "city",
            "state": "state",
            "zip_code": "zip_code",
            "country": "country",
            "shipping": "shipping",
            "billing": "billing",
        },
    ),
    # ----- Wave 1 — Property tree (group before property) --------------------
    ImporterSpec(
        importer="property_group",
        wave=1,
        entity="property_group",
        columns={
            "external_id": "external_id",
            "name": "name",
            "cemetery_id": FK("cemetery_ref"),
            "product_id": FK("product_ref"),
            "property_group_id": FK("parent_ref"),  # parent group (self-ref)
            "trusting_schedule_group_id": FK("trusting_schedule_group_ref"),
            "sale_price": "sale_price",
            "cost_price": "cost_price",
        },
    ),
    ImporterSpec(
        importer="property",
        wave=1,
        entity="property",
        columns={
            "external_id": "external_id",
            "property_type_id": FK("property_type_ref"),
            "property_group_id": FK("property_group_ref"),
            "cemetery_id": FK("cemetery_ref"),
            "model_no": "model_no",
            "description": "description",
            "trusting_schedule_group_id": FK("trusting_schedule_group_ref"),
            "sale_price": "sale_price",
            "cost_price": "cost_price",
            # Dynamic attribute columns drive the property name (section/lot/space
            # etc.); the importer reads any attribute-keyed column verbatim via
            # saveAttributeValuesForModel(). The canonical record carries them
            # under an "attributes" object; expanded by build_row().
            # Map placement (optional): add_to_map=1 + map_id + center/bounds.
        },
    ),
    # ----- Wave 2 — Commitments / owner-file lines ; interments --------------
    ImporterSpec(
        importer="property_commitment",
        wave=2,
        entity="property_commitment",
        columns={
            "external_id": "external_id",
            "property_id": FK("property_ref"),
            "type": "type",
            "is_manual": "is_manual",
            "reason": "reason",
            "committed_at": "committed_at",
            "uncommitted_at": "uncommitted_at",
            "expires_at": "expires_at",
            "created_by": FK("created_by_ref"),
            # Reserved (primary) owners: customer_1..5 -> customer internal ids.
            "customer_1": FK("customer_1_ref"),
            "customer_2": FK("customer_2_ref"),
            "customer_3": FK("customer_3_ref"),
            "customer_4": FK("customer_4_ref"),
            "customer_5": FK("customer_5_ref"),
            # Assigned owners: assigned_1..5 -> customer internal ids.
            "assigned_1": FK("assigned_1_ref"),
            "assigned_2": FK("assigned_2_ref"),
            "assigned_3": FK("assigned_3_ref"),
            "assigned_4": FK("assigned_4_ref"),
            "assigned_5": FK("assigned_5_ref"),
        },
    ),
    ImporterSpec(
        importer="owner_file_line",
        wave=2,
        entity="owner_file_line",
        columns={
            # Creates/updates a PropertyCommitment, then writes sale/deed info onto
            # the auto-created OwnerFileLine.config_data.
            "external_id": "external_id",
            "property_id": FK("property_ref"),
            "type": "type",
            "is_manual": "is_manual",
            "reason": "reason",
            "committed_at": "committed_at",
            "uncommitted_at": "uncommitted_at",
            "expires_at": "expires_at",
            "created_by": FK("created_by_ref"),
            "owner_file_id": FK("owner_file_ref"),
            "customer_1": FK("customer_1_ref"),
            "customer_2": FK("customer_2_ref"),
            "customer_3": FK("customer_3_ref"),
            "customer_4": FK("customer_4_ref"),
            "customer_5": FK("customer_5_ref"),
            "assigned_1": FK("assigned_1_ref"),
            "assigned_2": FK("assigned_2_ref"),
            "assigned_3": FK("assigned_3_ref"),
            "assigned_4": FK("assigned_4_ref"),
            "assigned_5": FK("assigned_5_ref"),
            # OwnerFileLine.config_data (sale/deed):
            "sale_date": "sale_date",
            "sale_price": "sale_price",  # canonical: integer cents
            "deed_date": "deed_date",
            "deed_number": "deed_number",
        },
    ),
    ImporterSpec(
        importer="interment",
        wave=2,
        entity="interment",
        columns={
            "external_id": "external_id",
            "date": "date",
            "model_no": "model_no",
            "deceased_id": FK("deceased_ref"),
            "cemetery_id": FK("cemetery_ref"),
            "nok_id": FK("nok_ref"),
            "funeral_home_id": FK("funeral_home_ref"),
            "funeral_director_id": FK("funeral_director_ref"),
            "nok_relation_id": "nok_relation_id",
            "status": "status",
            "first_name": "first_name",
            "middle_name": "middle_name",
            "last_name": "last_name",
            "suffix_id": "suffix_id",
            "nickname": "nickname",
            "sex_id": "sex_id",
            "interment_type_id": "interment_type_id",
            "service_type_id": "service_type_id",
            "interment_space": "interment_space",
            "interment_space_id": FK("property_ref"),  # canonical interment.property_ref -> property internal id
            "deed_number": "deed_number",
            "certificate_id": FK("certificate_ref"),
            "property_owner": "property_owner",
            "external_comments": "external_comments",
            "internal_comments": "internal_comments",
            "is_manual": "is_manual",
            # Partial dates: dob / dod / doi -> year/month/day/estimated columns.
            "dob_year": PartialDate("dob", "year"),
            "dob_month": PartialDate("dob", "month"),
            "dob_day": PartialDate("dob", "day"),
            "dob_estimated": PartialDate("dob", "estimated"),
            "dod_year": PartialDate("dod", "year"),
            "dod_month": PartialDate("dod", "month"),
            "dod_day": PartialDate("dod", "day"),
            "dod_estimated": PartialDate("dod", "estimated"),
            "doi_year": PartialDate("doi", "year"),
            "doi_month": PartialDate("doi", "month"),
            "doi_day": PartialDate("doi", "day"),
            "doi_estimated": PartialDate("doi", "estimated"),
        },
    ),
    # ----- v1.1 — financial, NOT in v1 (plan §3.1 waves 3-4). Stubs only. ----
    # Column maps are intentionally left unpopulated and excluded from the
    # default emit (V1_IMPORTERS). Wire these up in v1.1.
    ImporterSpec(importer="order", wave=3, entity="order", in_v1=False, note="v1.1 — financial, not in v1", columns={"external_id": "external_id"}),
    ImporterSpec(importer="order_line", wave=3, entity="order_line", in_v1=False, note="v1.1 — financial, not in v1", columns={"external_id": "external_id"}),
    ImporterSpec(importer="payment_plan", wave=3, entity="payment_plan", in_v1=False, note="v1.1 — financial, not in v1", columns={"external_id": "external_id"}),
    ImporterSpec(importer="certificate_line", wave=3, entity="certificate_line", in_v1=False, note="v1.1 — financial, not in v1", columns={"external_id": "external_id"}),
    ImporterSpec(importer="delivery", wave=3, entity="delivery", in_v1=False, note="v1.1 — financial, not in v1", columns={"external_id": "external_id"}),
    ImporterSpec(importer="payment", wave=4, entity="payment", in_v1=False, note="v1.1 — financial, not in v1", columns={"external_id": "external_id"}),
]

# Default emit set: the V1 NON-FINANCIAL core only.
V1_IMPORTERS: list[ImporterSpec] = [s for s in IMPORTERS if s.in_v1]


# --------------------------------------------------------------------------- #
# NDJSON → rows → xlsx                                                          #
# --------------------------------------------------------------------------- #
def _read_ndjson(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _resolve_ref(ref: Any, id_map: dict[str, int]) -> tuple[Any, Any]:
    """Resolve one external_id ref against the harvested id map.

    Returns ``(id_value, companion_ref_value)``:
        - resolved  -> ``(internal_id, None)``  — fill the importer id column
        - unresolved-> ``(None, ref)``          — surface the ref in the companion
        - empty ref -> ``(None, None)``
    """
    if ref in (None, ""):
        return None, None
    internal = id_map.get(ref)
    if internal is not None:
        return internal, None
    return None, ref


def build_header(spec: ImporterSpec) -> list[str]:
    """The importer's exact column order, with a companion ``*_ref`` column
    appended immediately after every FK id column (for unresolved refs)."""
    header: list[str] = []
    for col, source in spec.columns.items():
        header.append(col)
        if isinstance(source, FK):
            header.append(f"{col}_ref")
    return header


def build_row(record: dict, spec: ImporterSpec, id_map: dict[str, int]) -> dict[str, Any]:
    """Project one canonical record to a ``{column: value}`` dict for ``spec``.

    The canonical record is validated against the Target Contract (SPEC §6.4)
    BEFORE it is flattened (refs -> ids / partial dates -> components), so a
    contract breach is a LOUD failure here rather than a silently-misshaped row.
    """
    if spec.entity in contract.contract_entities():
        contract.validate_or_raise(spec.entity, record)
    row: dict[str, Any] = {}
    for col, source in spec.columns.items():
        if isinstance(source, FK):
            id_value, ref_value = _resolve_ref(record.get(source.ref_field), id_map)
            row[col] = id_value
            row[f"{col}_ref"] = ref_value
        elif isinstance(source, PartialDate):
            row[col] = _pd_component(record, source.field, source.part)
        elif callable(source):
            row[col] = source(record)
        else:
            row[col] = record.get(source)

    # Property uses dynamic attribute columns (section/lot/space/...) read
    # verbatim by saveAttributeValuesForModel(). They live under "attributes"
    # in the canonical record; expand each into its own column.
    attributes = record.get("attributes")
    if isinstance(attributes, dict):
        for attr_key, attr_val in attributes.items():
            row.setdefault(attr_key, attr_val)
    return row


def emit(
    canonical_dir: str | Path,
    output_dir: str | Path,
    *,
    id_map: Optional[dict[str, int]] = None,
    scoped_external_ids: Optional[set[str]] = None,
    importers: Optional[list[ImporterSpec]] = None,
) -> list[Path]:
    """Emit wave-ordered ``.xlsx`` files from the canonical NDJSON directory.

    Args:
        canonical_dir: Holds ``<entity>.ndjson`` files (plan §4.2).
        output_dir: Where the ``waveN_<importer>.xlsx`` files are written.
        id_map: Optional ``{external_id -> everspot internal id}`` resolution map
            harvested between waves (Stage 9). FK columns whose ref resolves are
            emitted as internal ids; unresolved refs are surfaced in companion
            ``*_ref`` columns. Defaults to empty (first emit — nothing resolved).
        scoped_external_ids: When given (delta-scoped emit, operating-model §5.4),
            only records whose ``external_id`` is in this set are emitted.
        importers: Override the importer set. **Defaults to** :data:`V1_IMPORTERS`
            (the NON-FINANCIAL core); financial importers are excluded by default.

    Returns:
        The written file paths, in wave order.
    """
    canonical = Path(canonical_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ids = id_map or {}
    specs = sorted(importers or V1_IMPORTERS, key=lambda s: (s.wave, s.importer))

    written: list[Path] = []
    for spec in specs:
        nd_path = canonical / f"{spec.entity}.ndjson"
        if not nd_path.exists():
            continue
        records = _read_ndjson(nd_path)
        if scoped_external_ids is not None:
            records = [r for r in records if r.get("external_id") in scoped_external_ids]
        if not records:
            continue

        header = build_header(spec)
        # A row may introduce dynamic attribute columns not in the static header;
        # collect them across all rows so every row is column-aligned.
        rows = [build_row(rec, spec, ids) for rec in records]
        extra_cols: list[str] = []
        seen = set(header)
        for r in rows:
            for k in r:
                if k not in seen:
                    seen.add(k)
                    extra_cols.append(k)
        full_header = header + extra_cols

        wb = Workbook()
        ws = wb.active
        ws.title = (spec.sheet_name or spec.importer)[:31]
        ws.append(full_header)
        for r in rows:
            ws.append([_xlsx_safe(r.get(col)) for col in full_header])

        xlsx_path = out / f"{spec.filename_stem}.xlsx"
        wb.save(xlsx_path)
        written.append(xlsx_path)

    _write_runbook(out, specs, written, id_map=ids)
    return written


def _write_runbook(
    out: Path,
    specs: list[ImporterSpec],
    written: list[Path],
    *,
    id_map: dict[str, int],
) -> None:
    """The operator's upload checklist in wave order (operating-model §3 stage 8)."""
    written_names = {p.name for p in written}
    resolved_note = (
        "FKs resolved from the supplied id_map; any unresolved ref is surfaced in a "
        "companion `*_ref` column."
        if id_map
        else "First emit — no id_map supplied, so **all FK id columns are blank** and "
        "each carries its external_id in a companion `*_ref` column."
    )

    lines = [
        "# Upload runbook (wave order)",
        "",
        "Generated by `emit_excel.py` (Stage 8). **V1 NON-FINANCIAL core only** — the",
        "financial importers (order/order_line/payment_plan/payment/certificate_line/",
        "delivery) are out of scope for V1.",
        "",
        "## Upload order",
        "Upload each wave **fully** before starting the next. Within Wave 1, load",
        "`property_group` before `property` (property FKs the group). `customer` loads",
        "in parallel with the property tree.",
        "",
        "```",
        "Wave 1:  property_group  →  property        |  customer   (parallel)",
        "Wave 2:  property_commitment / owner_file_line  ;  interment",
        "```",
        "",
        "## Between-wave External-IDs harvest (resolves FK columns)",
        "Importer FK columns reference Everspot **internal ids**, which only exist",
        "*after* a record's wave is loaded. " + resolved_note,
        "",
        "After each wave loads, harvest `external_id -> everspot internal id`",
        "(External-IDs Excel export, or the Orion `external-ids` read — see",
        "`external_ids.py::attach_everspot_ids`) and re-run `emit` with that map as",
        "`id_map=`. On re-emit, every resolved ref fills its `*_id` column and the",
        "companion `*_ref` column goes blank. Repeat until no `*_ref` column carries",
        "a value. Loads upsert by `external_id`, so re-emitting/re-loading is",
        "idempotent (operating-model §5.4).",
        "",
        "## Files",
    ]

    current_wave = None
    for spec in specs:
        fname = f"{spec.filename_stem}.xlsx"
        if fname not in written_names:
            continue
        if spec.wave != current_wave:
            current_wave = spec.wave
            lines.append(f"### Wave {spec.wave}")
        lines.append(f"- [ ] `{fname}` → {spec.importer} importer")

    (out / "RUNBOOK.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
