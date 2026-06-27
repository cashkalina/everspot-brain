"""Stage 9 — Orion load. Create the canonical graph in the tenant via the Orion REST API.

The **Orion-as-write-path** alternative to the Excel emitter (plan §6): instead of
emitting wave-ordered ``.xlsx`` for a human to upload, this POSTs each canonical record
to its Orion resource in wave order, registers the record's ``external_id`` (the
polymorphic ``external-ids`` resource), resolves every FK through the
``external_id -> internal-id`` map it builds as it loads, and is **idempotent**: it
upserts by external_id (look it up, then PATCH the existing record or POST a new one),
so re-running a wave updates rather than duplicates.

Wave order (RUNBOOK): Wave-0b prerequisites (a cemetery + a property_type) →
property_group → property → customer → interment. A child wave runs only after its
parents, so every FK target already has a tenant internal id by the time it is needed.

Config comes from the project ``target`` block (domain → ``base_url`` + ``/api/v1``,
``token_env_var`` → env, ``user_id_header``). Live writes need the migration user, the
egress IP whitelisted on the tenant, and — for Herd's self-signed cert — ``verify_tls=False``.

This module is GENERAL: entity field maps are declared here against the canonical schema,
never against one client's columns. Property location (section/lot/space) has no first-class
property column in Everspot — it lives in the **Attribute engine** under the area code
``location-property`` (SPEC §7.2, §13.3c). After a property is created/resolved, its location
scalars are written as structured custom-field values via the idempotent
``attribute-values/batch-upsert`` Orion endpoint (matched by attribute ``key`` →
upsert-in-place, so re-running never duplicates). The ``location-property`` area + its
section/lot/space attributes are tenant reference data, resolved once over the Orion read
backbone (like list_options); if they are absent they surface as a Wave-0b reference gap
(``LoadResult.reference_gaps``) — ids are never invented. Location is no longer concatenated
into the free-text property ``description``.

everspot-brain doc that specifies the rules:
    system-wiki/system/imports.md  ·  system-wiki/system/orion-api.md  ·  plan §6
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import contract
import run_state
from external_ids import ExternalIdLedger
from orion_client import OrionClient, OrionError

VERSION = "1.0.0"

# Synthetic cemetery ref the assembler stamps on property_group/property/interment
# (there is no canonical cemetery entity — the cemetery is a Wave-0b prerequisite).
_CEMETERY_REF = "src:cemetery:default"

# Property location → Attribute engine (SPEC §7.2, §13.3c). The area code groups the
# section/lot/space custom fields on the Property model; the keys are the canonical logical
# field names (overlay `attribute_areas.property.logical_fields`). The batch-upsert endpoint
# resolves these by `key`, so the loader sends keys (resolving ids only for the gap check).
_LOCATION_AREA_CODE = "location-property"
_LOCATION_ATTR_KEYS = ("section", "lot", "space")
# Short type name the AttributeValueController maps to Modules\Property\Models\Property.
_ATTR_PROPERTY_TYPE = "property"

# canonical entity -> (Orion resource, polymorphic model_type FQCN)
_ENTITY_TARGET = {
    "property_group": ("property-groups", "Modules\\Property\\Models\\PropertyGroup"),
    "property": ("properties", "Modules\\Property\\Models\\Property"),
    "customer": ("customers", "Modules\\Customer\\Models\\Customer"),
    "interment": ("interments", "Modules\\Interment\\Models\\Interment"),
}

# Load order: parents before children so FK targets resolve.
_WAVE_ORDER = ["property_group", "property", "customer", "interment"]


@dataclass(slots=True)
class LoadResult:
    created: dict[str, int] = field(default_factory=dict)
    updated: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, int] = field(default_factory=dict)
    failed: dict[str, int] = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)
    cemetery_id: Optional[int] = None
    property_type_id: Optional[int] = None
    # Attribute-engine write (SPEC §13.3c): property location → custom fields.
    attribute_values_written: int = 0   # property entities whose location attrs were upserted
    attribute_values_failed: int = 0
    # Wave-0b reference gaps surfaced when the location-property area / its attributes are
    # absent in the tenant (ids are never invented — these are reported, not guessed).
    reference_gaps: list[dict] = field(default_factory=list)


def _chunks(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def _source_id(rec: dict) -> Optional[str]:
    return (rec.get("_provenance") or {}).get("source_id")


def _expand_partial(prefix: str, partial: Optional[dict]) -> dict[str, Any]:
    """Canonical partialDate {year,month,day,estimated} → Orion ``<prefix>_*`` columns."""
    if not partial:
        return {}
    return {
        f"{prefix}_year": partial.get("year"),
        f"{prefix}_month": partial.get("month"),
        f"{prefix}_day": partial.get("day"),
        f"{prefix}_estimated": bool(partial.get("estimated")),
    }


def _interment_date(rec: dict) -> Optional[str]:
    """Compose interment.date (now NULLABLE) from the best available canonical date.

    Returns ``YYYY-MM-DD`` or ``None``. Month/day default to 01 when unknown. C3: a date
    is NEVER fabricated — when the source carries no interment/death date, ``None`` is
    returned and the column is left null (``interments.date`` is now nullable in Everspot).

    Only ``doi`` (date of interment) and ``dod`` (date of death) are real proxies for the
    burial date. ``dob`` (date of BIRTH) is NOT — falling back to it would stamp the
    decedent's birthday as the burial date (SPEC §7.2). So a record with only a dob gets
    ``None``, never the birthday.
    """
    for key in ("doi", "dod"):
        p = rec.get(key)
        if p and p.get("year"):
            y, m, d = p["year"], p.get("month") or 1, p.get("day") or 1
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return None


# --------------------------------------------------------------------------- #
# Pure projection (the loader's canonical → Orion-payload oracle)              #
# --------------------------------------------------------------------------- #
# This is the SINGLE source of truth for "what the loader writes for a canonical
# record". The OrionLoader._payload method delegates here so the load path and the
# field-level reconcile (reconcile.py) project records IDENTICALLY — reconcile diffs
# this projection against the live row. Keep it PURE: no network, no instance state,
# no side effects (the loader's date-sentinel warning is recorded by _payload, the
# caller, not here). `resolve_ref` maps a parent's external_id (`*_ref`) → tenant
# internal id; pass the loader's resolver when loading, or an external_id→internal_id
# map's `.get` when reconciling.
def project_payload(
    entity: str,
    rec: dict,
    *,
    cemetery_id: Optional[int],
    property_type_id: Optional[int],
    resolve_ref: Callable[[Optional[str]], Optional[int]],
) -> dict[str, Any]:
    """Project a canonical record to its Orion model attributes (pure; no I/O)."""
    if entity == "property_group":
        return {"name": rec.get("name") or "Default Section", "cemetery_id": cemetery_id}
    if entity == "property":
        # Location (section/lot/space) is NOT a property column — it is written to the
        # Attribute engine (see project_location / flush_location_attributes), so it is
        # intentionally absent from this scalar payload.
        return {
            "property_type_id": property_type_id,
            "property_group_id": resolve_ref(rec.get("property_group_ref")),
            "cemetery_id": cemetery_id,
        }
    if entity == "customer":
        attrs = rec.get("attributes") or {}
        payload = {
            "status": rec.get("status") or "customer",
            "first_name": rec.get("first_name"),
            "middle_name": rec.get("middle_name"),
            "last_name": rec.get("last_name"),
            "suffix_id": rec.get("suffix_id"),
        }
        if attrs.get("maiden_name"):
            payload["maiden_name"] = attrs["maiden_name"]
        return payload
    if entity == "interment":
        # C3: never fabricate a burial date — compose from doi/dod, else send null
        # (interments.date is now nullable). project_payload is the reconcile oracle, so
        # the live row is expected to carry null too when the source had no date.
        payload = {
            "deceased_id": resolve_ref(rec.get("deceased_ref")),
            "interment_space_id": resolve_ref(rec.get("property_ref")),
            "cemetery_id": cemetery_id,
            "status": rec.get("status") or "completed",
            "date": _interment_date(rec),
            "interment_type_id": rec.get("interment_type_id"),
            # A migrated interment is a historical/manual interment: the platform's
            # `is_manual` flag ("Manual / Enable to enter historical interment") makes
            # `completed` a valid terminal state via the relaxed manual validation (no
            # scheduled event/space required), so the auto stage-progression never demotes
            # it to `awaiting-scheduling`. This is a REAL column, so it is part of the pure
            # projection and is reconciled against the live row.
            "is_manual": True,
        }
        payload.update(_expand_partial("dob", rec.get("dob")))
        payload.update(_expand_partial("dod", rec.get("dod")))
        payload.update(_expand_partial("doi", rec.get("doi")))
        return payload
    raise ValueError(f"no payload builder for entity {entity!r}")


def project_location(rec: dict) -> dict[str, str]:
    """Extract the non-empty section/lot/space scalars from a canonical property record.

    The canonical artifact carries these as top-level logical scalars (overlay
    `attribute_areas.property.logical_fields`); the assembler also folds anything
    non-scalar into `rec['attributes']`, so honor both as a source of the three keys.
    Pure — shared by the loader (queue location writes) and reconcile (compare custom
    fields against live attribute-values).
    """
    attrs = rec.get("attributes") or {}
    out: dict[str, str] = {}
    for key in _LOCATION_ATTR_KEYS:
        val = rec.get(key)
        if val is None:
            val = attrs.get(key)
        if val is not None and str(val).strip() != "":
            out[key] = str(val)
    return out


class OrionLoader:
    """Loads a canonical snapshot into a tenant via Orion, idempotently."""

    def __init__(
        self,
        client: OrionClient,
        ledger: ExternalIdLedger,
        *,
        cemetery_name: str,
        force_update: Optional[set[str]] = None,
        batch_size: int = 100,
    ) -> None:
        self.client = client
        self.ledger = ledger
        self.cemetery_name = cemetery_name
        # source_ids whose row CHANGED (delta) → PATCH in place; every other
        # already-loaded record is left untouched (idempotent re-runs don't churn
        # unchanged records — a v1 re-run only creates what is missing).
        self.force_update = force_update or set()
        self.batch_size = batch_size
        self.id_map: dict[str, int] = {}          # external_id -> tenant internal id
        self.existing: dict[str, int] = {}         # external_id -> model_id (pre-existing)
        self.cemetery_id: Optional[int] = None
        self.property_type_id: Optional[int] = None
        # Resolved once (Wave-0 reference): logical location key -> tenant attribute id.
        # None until resolved; empty/partial map means the area or attrs are missing.
        self.location_attr_ids: Optional[dict[str, int]] = None
        # Pending property-location attribute writes, accumulated as properties load and
        # flushed (batch-upserted) after the property wave: [{property_id, values}].
        self._pending_location: list[dict] = []
        self.result = LoadResult()

    # -- prerequisites ----------------------------------------------------- #
    def ensure_prerequisites(self) -> None:
        """Ensure a cemetery + a property_type exist (create the cemetery if absent)."""
        cems = list(self.client.paginate("cemeteries"))
        match = next((c for c in cems if c.get("name") == self.cemetery_name), None)
        if match is None:
            # The named cemetery is absent. NEVER silently adopt a differently-named
            # existing cemetery (that mis-assigns every migrated record). Create the
            # named one — same as the empty-tenant path. (If other cemeteries exist, note
            # the reference gap for the report; we still create rather than mis-assign.)
            if cems:
                self.result.reference_gaps.append({
                    "kind": "cemetery", "requested_name": self.cemetery_name,
                    "existing": [c.get("name") for c in cems],
                    "detail": (f"Cemetery '{self.cemetery_name}' was absent though "
                               f"{len(cems)} other cemetery(ies) exist; created the named "
                               "cemetery rather than silently assigning records to an "
                               "existing one. Confirm this is the intended cemetery."),
                })
            # attribute_data is a json column and config_data is Spatie schemaless —
            # both expect a JSON *string* over the wire, not a raw array/object.
            match = self.client.create("cemeteries", {
                "name": self.cemetery_name,
                "address_line_one": "Unknown",
                "city": "Unknown",
                "zip_code": "00000",
                "attribute_data": "{}",
                "config_data": "{}",
            })
        self.cemetery_id = match["id"]
        self.result.cemetery_id = self.cemetery_id

        pts = list(self.client.paginate("property-types"))
        if pts:
            self.property_type_id = pts[0]["id"]
        else:
            self.property_type_id = self.client.create("property-types", {"name": "Lot"})["id"]
        self.result.property_type_id = self.property_type_id

    def resolve_location_attributes(self) -> dict[str, int]:
        """Resolve the ``location-property`` area + its section/lot/space attribute ids.

        Tenant reference data, read once over the Orion backbone (like list_options):
        ``attribute-areas`` (filtered to ``location-property``) confirms the area exists for
        the Property model; ``attributes`` supplies each logical key's tenant attribute id.
        Returns ``{key: attribute_id}`` for whichever of section/lot/space resolve. Missing
        pieces are surfaced as Wave-0b reference gaps (``LoadResult.reference_gaps``) — ids
        are NEVER invented. The batch-upsert endpoint matches by key, so the ids are used
        only for the gap check / report (and would seed a creation step if one is added).
        """
        if self.location_attr_ids is not None:
            return self.location_attr_ids

        areas = list(self.client.paginate(
            "attribute-areas",
            filters=[{"field": "code", "operator": "=", "value": _LOCATION_AREA_CODE}],
        ))
        if not areas:
            self.result.reference_gaps.append({
                "kind": "attribute_area", "area_code": _LOCATION_AREA_CODE,
                "detail": (f"Attribute area '{_LOCATION_AREA_CODE}' is absent in the tenant; "
                           "property location (section/lot/space) cannot be written as custom "
                           "fields. Create the area + its section/lot/space attributes "
                           "(Wave-0b) before location can land."),
                "keys": list(_LOCATION_ATTR_KEYS),
            })
            self.location_attr_ids = {}
            return self.location_attr_ids

        by_key = {a.get("key"): a["id"] for a in self.client.paginate("attributes") if a.get("key")}
        resolved: dict[str, int] = {}
        missing: list[str] = []
        for key in _LOCATION_ATTR_KEYS:
            if key in by_key:
                resolved[key] = by_key[key]
            else:
                missing.append(key)
        if missing:
            self.result.reference_gaps.append({
                "kind": "attribute", "area_code": _LOCATION_AREA_CODE, "missing_keys": missing,
                "detail": (f"Location attribute(s) {missing} do not exist in the tenant under "
                           f"'{_LOCATION_AREA_CODE}'. Those values cannot be written as custom "
                           "fields until the attribute(s) are created (Wave-0b)."),
            })
        self.location_attr_ids = resolved
        return resolved

    def prefetch_existing_external_ids(self) -> None:
        """Build the external_id → model_id map from the tenant (for idempotent upsert)."""
        for row in self.client.paginate("external-ids"):
            if row.get("system", "default") == "default" and row.get("external_id"):
                self.existing[row["external_id"]] = row["model_id"]

    # -- FK resolution ----------------------------------------------------- #
    def _resolve_ref(self, ref: Optional[str]) -> Optional[int]:
        if not ref:
            return None
        if ref == _CEMETERY_REF:
            return self.cemetery_id
        return self.id_map.get(ref) or self.existing.get(ref) or self.ledger.everspot_id(ref)

    # -- payload builders (canonical -> Orion model attributes) ------------ #
    def _payload(self, entity: str, rec: dict) -> dict[str, Any]:
        # Contract gate (SPEC §6.4): validate the LOGICAL canonical record BEFORE
        # flattening *_ref -> internal ids and expanding partial dates into
        # <prefix>_year/_month/_day columns. A breach is a LOUD failure here.
        if entity in contract.contract_entities():
            contract.validate_or_raise(entity, rec)
        # C3: no date is no longer fabricated — when the source carries no interment/death
        # date, interment.date is sent as null (the column is nullable). Record a benign
        # note (not an error/warning): this is honest absence, not a data-quality problem.
        if entity == "interment" and _interment_date(rec) is None:
            self.result.errors.append({
                "entity": "interment", "external_id": rec["external_id"],
                "note": "no source interment/death date; interment.date left null",
            })
        payload = project_payload(
            entity, rec,
            cemetery_id=self.cemetery_id,
            property_type_id=self.property_type_id,
            resolve_ref=self._resolve_ref,
        )
        return payload

    def _create_payload(self, entity: str, rec: dict) -> dict[str, Any]:
        """The model payload for a NEW record, carrying the top-level ``external_id``.

        A1: the Orion create/batchStore controller now accepts a top-level ``external_id``
        and registers it atomically (``HasExternalIds``) in the same transaction as the
        insert. So creates send it inline — no separate ``external-ids`` register call,
        no orphan window. ``external_id`` is NOT a model column, so it is intentionally
        absent from :meth:`_payload`/:func:`project_payload` (the PATCH + reconcile oracle)
        and added only here, on the create path.
        """
        return {**self._payload(entity, rec), "external_id": rec["external_id"]}

    @staticmethod
    def _location_values(rec: dict) -> dict[str, str]:
        """Extract the non-empty section/lot/space scalars (delegates to project_location)."""
        return project_location(rec)

    def _queue_location(self, rec: dict) -> None:
        """Queue a property's location attributes for the post-property batch-upsert."""
        property_id = self.id_map.get(rec["external_id"])
        if not property_id:
            return
        values = self._location_values(rec)
        if values:
            self._pending_location.append({"property_id": property_id, "values": values})

    def flush_location_attributes(self) -> None:
        """Write all queued property-location values via the idempotent batch-upsert endpoint.

        Resolves the location attribute reference once (gap-surfacing if absent); then
        POSTs ``attribute-values/batch-upsert`` in chunks. The endpoint matches by `key`
        and upserts in place, so re-running a load updates values rather than duplicating
        them (idempotent). Per-entity errors are recorded; a missing attribute key surfaces
        through the endpoint's key-level errors as well as the Wave-0b gap.
        """
        if not self._pending_location:
            return
        resolved = self.resolve_location_attributes()
        if not resolved:
            # No location attributes available in the tenant — already surfaced as a gap.
            self.result.attribute_values_failed += len(self._pending_location)
            self._pending_location.clear()
            return

        writable_keys = set(resolved)
        entities = []
        for item in self._pending_location:
            attrs = [{"key": k, "value": v} for k, v in item["values"].items() if k in writable_keys]
            if attrs:
                entities.append({
                    "attributable_type": _ATTR_PROPERTY_TYPE,
                    "attributable_id": item["property_id"],
                    "attributes": attrs,
                })

        for chunk in _chunks(entities, self.batch_size):
            try:
                body = self.client.post("attribute-values/batch-upsert", {"entities": chunk})
            except OrionError as exc:
                self.result.attribute_values_failed += len(chunk)
                self.result.errors.append({
                    "entity": "property", "stage": "attribute-values",
                    "error": str(exc)[:300],
                })
                continue
            summary = body.get("summary") or {}
            self.result.attribute_values_written += int(summary.get("successful", 0))
            self.result.attribute_values_failed += int(summary.get("failed", 0))
            for err in (body.get("errors") or []):
                self.result.errors.append({
                    "entity": "property", "stage": "attribute-values",
                    "attributable_id": err.get("attributable_id"), "error": str(err.get("error"))[:200],
                })
            # Key-level failures inside an otherwise-saved entity (e.g. an attribute the
            # tenant doesn't expose for Property) come back per-entity in `data[].errors`.
            for row in (body.get("data") or []):
                for kerr in (row.get("errors") or []):
                    self.result.errors.append({
                        "entity": "property", "stage": "attribute-values",
                        "attributable_id": row.get("attributable_id"),
                        "key": kerr.get("key"), "error": str(kerr.get("error"))[:200],
                    })
        self._pending_location.clear()

    def _record_created(self, pairs: list[tuple[dict, dict]]) -> int:
        """Record (external_id → internal id) for records the SERVER created+registered.

        A1 (atomic create+register): the create/batch payload now carries a top-level
        ``external_id``, which the Orion controller registers via ``HasExternalIds`` in the
        SAME transaction as the row insert. So a successful create response means the
        external_id is already live in the tenant — there is NO separate
        ``external-ids`` registration call and NO orphan window. The id_map is built from
        the create RESPONSE (``made["id"]``). Returns the count recorded.

        Defensive guard: a malformed response row without an ``id`` is skipped (and the
        record left unrecorded → counted as ``failed`` by the caller, then repaired next
        run) rather than crashing the wave.
        """
        recorded = 0
        for rec, made in pairs:
            internal = (made or {}).get("id")
            if internal is None:
                continue
            self.id_map[rec["external_id"]] = internal
            self.existing[rec["external_id"]] = internal
            recorded += 1
        return recorded

    def _register_orphans(self, entity: str, model_type: str, pairs: list[tuple[dict, dict]]) -> int:
        """Belt-and-suspenders external-id registration for ADOPTED orphan rows.

        Unlike the create path (where the server registers atomically), orphan adoption
        deals with rows that already exist in the tenant but were NEVER external-id-linked
        — a legacy row, or a crash mid-transaction before A1's atomic registration landed.
        These need an explicit ``external-ids`` batch register. Returns the count
        SUCCESSFULLY registered; a failed register adds nothing to id_map/existing (the row
        stays an orphan the next run re-adopts) and is not counted.
        """
        ext_rows = []
        for rec, made in pairs:
            ext_rows.append({
                "model_type": model_type, "model_id": made["id"],
                "system": "default", "external_id": rec["external_id"],
            })
        if not ext_rows:
            return 0
        try:
            self.client.batch_store("external-ids", ext_rows)
        except OrionError as exc:
            self.result.errors.append({"entity": entity, "stage": "external-ids", "error": str(exc)[:200]})
            return 0
        for rec, made in pairs:
            self.id_map[rec["external_id"]] = made["id"]
            self.existing[rec["external_id"]] = made["id"]
        return len(pairs)

    def _correct_interment_status(self, resource: str, present: list[dict]) -> int:
        """PATCH already-loaded interments whose live status/is_manual differ from projection.

        Idempotent backfill for the present-and-skipped set: fetches each record's live
        ``status`` and ``is_manual`` and, for any that differ from what the canonical record
        projects (e.g. a row stuck at ``awaiting-scheduling`` that should be ``completed``, or
        an interment loaded before ``is_manual`` was applied), issues a PATCH carrying the
        projected interment payload. Marking an interment manual makes ``completed`` a valid
        terminal status, so the row stays put. Returns the number corrected. Rows already in
        the projected state are left untouched, so a re-run is a no-op.
        """
        if not present:
            return 0

        wanted: dict[int, tuple[dict, str, bool]] = {}
        for rec in present:
            internal = self.existing.get(rec["external_id"])
            if internal is None:
                continue
            projected = self._payload("interment", rec)
            status = projected.get("status")
            if status:
                wanted[internal] = (rec, status, bool(projected.get("is_manual")))
        if not wanted:
            return 0

        # Page the live interments once (the proven-safe pattern reconcile uses) and read
        # back each id's current status + is_manual — no exotic filter operator needed.
        live: dict[int, tuple[Optional[str], Any]] = {}
        for row in self.client.paginate(resource):
            if row["id"] in wanted:
                live[row["id"]] = (row.get("status"), row.get("is_manual"))

        corrected = 0
        for internal, (rec, status, is_manual) in wanted.items():
            live_status, live_manual = live.get(internal, (None, None))
            if live_status == status and bool(live_manual) == is_manual:
                continue
            try:
                self.client.update(resource, internal, self._payload("interment", rec))
                corrected += 1
            except OrionError as exc:
                self.result.errors.append(
                    {"entity": "interment", "external_id": rec["external_id"],
                     "stage": "status-correction", "error": str(exc)[:300]}
                )
        return corrected

    @staticmethod
    def _payload_signature(payload: dict) -> tuple:
        """A hashable, order-independent signature of a projected payload's scalar values.

        Used to match an orphan live row (a model created but never external-id-registered)
        back to the canonical record that would have produced it. Only the loader's own
        projected scalars are compared (general — no client columns), so the match is over
        exactly the attributes the loader writes.
        """
        return tuple(sorted(
            (k, v) for k, v in payload.items()
            if v is not None and not isinstance(v, (dict, list))
        ))

    def _repair_orphans(
        self, entity: str, model_type: str, resource: str, records: list[dict]
    ) -> int:
        """Adopt orphan rows: live models that were created but never external-id-registered.

        For each canonical record NOT already linked to an external_id, compute its projected
        payload signature and look for a matching live row whose external_id is NOT already
        registered. If found, register (external_id → that row's id) so the record is treated
        as already-loaded — a re-run REPAIRS the missing link instead of creating a duplicate.

        General by construction: matching is over the loader's projected scalars only, and the
        already-registered model_ids come from the prefetched external-id map, so a row that is
        already correctly linked is never re-adopted. Returns the number of orphans registered.
        """
        unregistered = [r for r in records if r["external_id"] not in self.existing]
        if not unregistered:
            return 0

        # Live rows already claimed by a registered external_id — never re-adopt these.
        claimed_ids = set(self.existing.values())

        # Build signature → queue of unregistered canonical records (duplicates possible if
        # two records project identically; we adopt at most one live row per record).
        wanted: dict[tuple, list[dict]] = {}
        for rec in unregistered:
            sig = self._payload_signature(self._payload(entity, rec))
            wanted.setdefault(sig, []).append(rec)
        if not wanted:
            return 0

        adopted: list[tuple[dict, dict]] = []
        used_row_ids: set[int] = set()
        for row in self.client.paginate(resource):
            rid = row.get("id")
            if rid is None or rid in claimed_ids or rid in used_row_ids:
                continue
            sig = self._payload_signature(self._row_projection(entity, row))
            queue = wanted.get(sig)
            if queue:
                rec = queue.pop(0)
                used_row_ids.add(rid)
                adopted.append((rec, {"id": rid}))

        if not adopted:
            return 0
        return self._register_orphans(entity, model_type, adopted)

    def _row_projection(self, entity: str, row: dict) -> dict:
        """Project a LIVE Orion row to the same scalar payload shape the loader writes.

        Mirrors :func:`project_payload`'s scalar keys so a live row and a canonical record
        compare on equal footing in :meth:`_repair_orphans`. Only the loader-written scalar
        attributes are read from the live row (general — no client columns).
        """
        keys: tuple[str, ...]
        if entity == "property_group":
            keys = ("name", "cemetery_id")
        elif entity == "property":
            keys = ("property_type_id", "property_group_id", "cemetery_id")
        elif entity == "customer":
            keys = ("status", "first_name", "middle_name", "last_name", "suffix_id", "maiden_name")
        elif entity == "interment":
            keys = ("deceased_id", "interment_space_id", "cemetery_id", "status", "date",
                    "interment_type_id", "is_manual")
        else:
            keys = tuple(row.keys())
        out: dict[str, Any] = {}
        for k in keys:
            if k in row:
                out[k] = row[k]
        return out

    # -- per-entity load --------------------------------------------------- #
    def load_entity(self, entity: str, records: list[dict]) -> None:
        resource, model_type = _ENTITY_TARGET[entity]
        created = updated = skipped = failed = 0

        # Repair pass (idempotency safety): a prior run may have CREATED a model row but
        # failed to register its external_id (register error, or a crash between create and
        # register). Such an orphan is invisible to `existing` (no external_id link), so a
        # naive re-run would create a DUPLICATE. Before deciding what to create, search the
        # live entity for rows matching a still-unregistered canonical record's projected
        # payload and register them in place. `existing` then reflects the repaired links.
        repaired = self._repair_orphans(entity, model_type, resource, records)

        to_create = [r for r in records if r["external_id"] not in self.existing]
        present = [r for r in records if r["external_id"] in self.existing]
        # Already-loaded: PATCH only if the source row CHANGED; otherwise keep the FK
        # in the id_map and skip the write (no needless churn on a re-run).
        to_update = [r for r in present if _source_id(r) in self.force_update]
        for rec in present:
            self.id_map[rec["external_id"]] = self.existing[rec["external_id"]]
        skipped = len(present) - len(to_update)

        for rec in to_update:
            internal = self.existing[rec["external_id"]]
            try:
                self.client.update(resource, internal, self._payload(entity, rec))
                updated += 1
            except OrionError as exc:
                failed += 1
                self.result.errors.append({"entity": entity, "external_id": rec["external_id"], "error": str(exc)[:300]})

        # New → batch create. A1: each create payload carries its own top-level
        # ``external_id``, which the Orion controller registers ATOMICALLY (HasExternalIds)
        # in the same transaction as the insert — so there is ONE round-trip per create, no
        # separate ``external-ids`` register call, and no orphan window. The id_map is built
        # from the create RESPONSE. Orion batch is all-or-nothing per request, so one bad
        # record (e.g. an impossible source date) would sink its whole chunk; on a chunk
        # error we retry record-by-record so the good records still load and only the
        # genuinely-bad ones fail and are pinpointed. A create whose response lacks an id
        # is not counted as created (`_record_created` skips it → marked failed/for-retry,
        # and the next run's repair pass adopts any resulting orphan).
        for chunk in _chunks(to_create, self.batch_size):
            payloads = [self._create_payload(entity, r) for r in chunk]
            try:
                made = self.client.batch_store(resource, payloads)
            except OrionError:
                made = None
            if made is not None and len(made) == len(chunk):
                recorded = self._record_created(list(zip(chunk, made)))
                created += recorded
                failed += len(chunk) - recorded
                continue
            # Fallback: per-record create to isolate the failure.
            for rec in chunk:
                try:
                    one = self.client.create(resource, self._create_payload(entity, rec))
                    recorded = self._record_created([(rec, one)])
                    created += recorded
                    failed += 1 - recorded
                except OrionError as exc:
                    failed += 1
                    self.result.errors.append({"entity": entity, "external_id": rec["external_id"], "error": str(exc)[:200]})

        # Interment status correction (idempotent): an interment that is already loaded
        # and otherwise-unchanged is normally skipped — but its live `status`/`is_manual`
        # may be wrong (a historical burial that landed as `awaiting-scheduling`, or that
        # was loaded before `is_manual` was applied). For every present-and-skipped
        # interment, compare the live status + is_manual against the projection and PATCH
        # only the ones that differ. A re-run finds none to fix, so it never churns rows.
        if entity == "interment":
            corrected = self._correct_interment_status(
                resource,
                [r for r in present if _source_id(r) not in self.force_update],
            )
            updated += corrected
            skipped -= corrected

        self.result.created[entity] = created
        self.result.updated[entity] = updated
        self.result.skipped[entity] = skipped
        self.result.failed[entity] = failed

        # Property location → Attribute engine (SPEC §13.3c). Queue every property whose
        # internal id is now known (created OR already-present) so a re-run re-asserts the
        # location idempotently. The actual upsert is flushed after the property wave.
        if entity == "property":
            for rec in records:
                self._queue_location(rec)

        # Persist everspot ids into the durable ledger (post-load harvest).
        self.ledger.attach_everspot_ids({k: v for k, v in self.id_map.items()})


def load(
    project_root: str | Path,
    snapshot: str,
    client: OrionClient,
    *,
    cemetery_name: str,
    scoped: bool = True,
) -> LoadResult:
    """Load the canonical graph for one snapshot into the tenant via Orion.

    On v2+, restrict to the delta-scoped (CHANGED + NEW) records via ``delta.json``;
    FK targets may point at unchanged records already loaded (resolved via the ledger).
    """
    root = Path(project_root)
    run_dir = root / "runs" / snapshot
    canonical = run_dir / "canonical"
    ledger = ExternalIdLedger(root / "ledger" / "external_ids.json")

    # Resume support (SPEC §17) — WAVE-LEVEL: if an incomplete load checkpoint exists, skip
    # the WAVES already completed and continue from the next wave. Resume granularity is the
    # wave, NOT mid-wave: a wave that was interrupted is simply re-run in full, which is safe
    # because the loader is idempotent (upsert-by-external_id + the prefetched
    # existing-external-ids map + the H2 orphan-repair pass), so re-POSTing an
    # already-partially-loaded wave repairs/updates rather than duplicating. A `complete`
    # checkpoint means a prior load finished cleanly; we restart it fresh (a normal re-run,
    # which the idempotent upsert turns into no-ops / delta updates).
    checkpoint = run_state.get_load_checkpoint(run_dir)
    resuming = bool(checkpoint) and not checkpoint.get("complete")
    waves_done: list[str] = list(checkpoint.get("waves_done", [])) if resuming else []

    scope: Optional[set[str]] = None
    changed: set[str] = set()
    delta_path = root / "snapshots" / snapshot / "delta.json"
    if delta_path.exists():
        data = json.loads(delta_path.read_text(encoding="utf-8"))
        all_changed_new: set[str] = set()
        for td in (data.get("tables") or {}).values():
            all_changed_new.update(td.get("new") or [])
            all_changed_new.update(td.get("changed") or [])
            changed.update(td.get("changed") or [])
        if scoped:
            scope = all_changed_new

    # CHANGED rows get PATCHed in place; NEW rows get created; everything already
    # loaded and unchanged is skipped (idempotent re-run without churn).
    loader = OrionLoader(client, ledger, cemetery_name=cemetery_name,
                         force_update=changed)
    loader.ensure_prerequisites()
    loader.prefetch_existing_external_ids()

    def _read(entity: str) -> list[dict]:
        path = canonical / f"{entity}.ndjson"
        if not path.exists():
            return []
        recs = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        if scope is None:
            return recs
        # property_group has no source_id-scoped delta; always (re)load it.
        if entity == "property_group":
            return recs
        return [r for r in recs if _provenance_in_scope(r, scope)]

    # Initialize / refresh the checkpoint at load start (idempotent — preserves an
    # in-progress waves_done set on resume; resets `complete`).
    run_state.set_load_checkpoint(run_dir, waves_done=waves_done, complete=False)

    for entity in _WAVE_ORDER:
        if entity in waves_done:
            # Already loaded in a prior (crashed) run — skip it, but keep its
            # external_id → internal-id mappings live via the prefetched `existing` map.
            continue
        run_state.set_load_checkpoint(run_dir, current_wave=entity)
        loader.load_entity(entity, _read(entity))
        # Flush property location to the Attribute engine right after the property wave,
        # once every property has a tenant internal id (SPEC §13.3c).
        if entity == "property":
            loader.flush_location_attributes()
        waves_done.append(entity)
        run_state.set_load_checkpoint(run_dir, waves_done=waves_done, current_wave=None)

    # Clean completion — finalize the checkpoint so the next run starts fresh.
    run_state.set_load_checkpoint(run_dir, waves_done=waves_done, complete=True)

    ledger.save()
    report = {
        "load_version": VERSION, "snapshot": snapshot, "scoped": scope is not None,
        "cemetery_id": loader.result.cemetery_id, "property_type_id": loader.result.property_type_id,
        "created": loader.result.created, "updated": loader.result.updated,
        "skipped": loader.result.skipped, "failed": loader.result.failed,
        "attribute_values_written": loader.result.attribute_values_written,
        "attribute_values_failed": loader.result.attribute_values_failed,
        "reference_gaps": loader.result.reference_gaps,
        "errors": loader.result.errors[:50],
    }
    (canonical / "load_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return loader.result


def _provenance_in_scope(rec: dict, scope: set[str]) -> bool:
    """A canonical record is in delta scope if its source row is NEW/CHANGED.

    The decedent/interment external_ids derive from the row source_id; the property
    external_id derives from the grave key, so it is matched by its provenance source_id.
    """
    sid = (rec.get("_provenance") or {}).get("source_id")
    return sid in scope if sid else True
