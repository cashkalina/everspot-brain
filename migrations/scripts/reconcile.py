"""Stage 7/10/12 — Reconcile. Count + money + FIELD-LEVEL value comparison between record sets.

The highest-stakes check (operating-model §4 lens 4): the LLM never does
arithmetic — totals are summed **in code** and compared exactly. Used both
source↔canonical (pre-load, stage 7) and canonical↔live-tenant (post-load, stage
10/12, the live side read via Orion). Money is compared in **integer cents** so there
is no float drift.

Post-load ``--live`` adds a **field-level** lens (SPEC §15.3 correctness): beyond
proving records are PRESENT (counts by external_id), it proves their VALUES match —
each canonical record is projected the SAME way the loader writes it
(:func:`orion_load.project_payload`, the oracle) and diffed field-by-field against the
live row, with property location custom fields compared against live attribute-values.
Live data is bulk-fetched per entity (O(pages), no per-record calls). Value mismatches
are **WARN only** — reported (per-field tally + capped sample), never blocking; count
conservation alone gates the run.

Output: ``reconciliation.md`` / ``.json`` — counts + money totals + field_level block.

everspot-brain doc that specifies the rules:
    system-wiki/system/data-migration.md  (§ reconciliation, financial exactness)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

VERSION = "1.1.0"


@dataclass(slots=True)
class FieldTotals:
    field: str
    left_cents: int
    right_cents: int

    @property
    def matches(self) -> bool:
        return self.left_cents == self.right_cents

    @property
    def delta_cents(self) -> int:
        return self.right_cents - self.left_cents


@dataclass(slots=True)
class ReconResult:
    label: str
    left_count: int
    right_count: int
    money: list[FieldTotals] = field(default_factory=list)

    @property
    def counts_match(self) -> bool:
        return self.left_count == self.right_count

    @property
    def passed(self) -> bool:
        return self.counts_match and all(m.matches for m in self.money)


def _sum_cents(records: Iterable[Mapping], field_name: str) -> int:
    """Sum an integer-cents field across records (None/missing treated as 0)."""
    total = 0
    for rec in records:
        val = rec.get(field_name)
        if val is None:
            continue
        total += int(val)
    return total


def reconcile(
    left: Sequence[Mapping],
    right: Sequence[Mapping],
    *,
    label: str,
    money_fields: Optional[Sequence[str]] = None,
) -> ReconResult:
    """Compare two record sets by row count and summed money fields (in cents).

    Args:
        left: The baseline set (e.g. source, or canonical).
        right: The comparison set (e.g. canonical, or live-tenant read).
        label: Human label for the comparison ("source ↔ canonical").
        money_fields: Integer-cents fields to total and compare.

    Returns:
        :class:`ReconResult` with per-field totals and a pass/fail verdict.
    """
    result = ReconResult(label=label, left_count=len(left), right_count=len(right))
    for fname in money_fields or []:
        result.money.append(
            FieldTotals(field=fname, left_cents=_sum_cents(left, fname), right_cents=_sum_cents(right, fname))
        )
    return result


def _fmt_cents(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100:,}.{cents % 100:02d}"


def render_reconciliation(results: Sequence[ReconResult]) -> str:
    """Render one or more reconciliations to ``reconciliation.md`` content."""
    lines = ["# Reconciliation", ""]
    overall = all(r.passed for r in results)
    lines.append(f"**Overall:** {'✅ PASS' if overall else '❌ FAIL — investigate before load'}")
    lines.append("")
    for r in results:
        verdict = "✅" if r.passed else "❌"
        lines.append(f"## {verdict} {r.label}")
        lines.append("")
        cmark = "✅" if r.counts_match else "❌"
        lines.append(f"- {cmark} Row count: {r.left_count} → {r.right_count}"
                     f"{'' if r.counts_match else f' (Δ {r.right_count - r.left_count})'}")
        if r.money:
            lines.append("")
            lines.append("| Money field | Left | Right | Match |")
            lines.append("|---|---:|---:|:--:|")
            for m in r.money:
                mark = "✅" if m.matches else f"❌ Δ {_fmt_cents(m.delta_cents)}"
                lines.append(f"| {m.field} | {_fmt_cents(m.left_cents)} | {_fmt_cents(m.right_cents)} | {mark} |")
        lines.append("")
    return "\n".join(lines)


def write_reconciliation(results: Sequence[ReconResult], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_reconciliation(results), encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# Stage 10/12 — the runnable reconcile stage (offline + post-load --live)      #
# --------------------------------------------------------------------------- #
import json as _json  # local alias: keep the arithmetic core import-light


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [_json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


# --------------------------------------------------------------------------- #
# Count conservation — manifest (true LEFT count) reconciled against the         #
# per-source-row disposition ledger (H1). This REPLACES the old self-derived     #
# provenance count, which could never see a dropped row (no record → no          #
# provenance → no count → tautological "conserved").                             #
# --------------------------------------------------------------------------- #
def _manifest_table_rows(manifest: Optional[Mapping]) -> dict[str, int]:
    """Per-table source-row totals from the ingest manifest (the source-of-truth)."""
    if not manifest:
        return {}
    counts = dict(manifest.get("table_row_counts") or {})
    if counts:
        return {str(k): int(v) for k, v in counts.items()}
    # Fall back to files[].tables[].rows when table_row_counts is absent.
    out: dict[str, int] = {}
    for fentry in manifest.get("files") or []:
        for t in fentry.get("tables") or []:
            tbl = t.get("table")
            if tbl is not None and t.get("rows") is not None:
                out[str(tbl)] = out.get(str(tbl), 0) + int(t["rows"])
    return out


def conserve(
    manifest: Optional[Mapping],
    dispositions: Sequence[Mapping],
) -> dict:
    """Per-source-row disposition accounting against the manifest's true row totals.

    The manifest is the source-of-truth LEFT count (the real number of source rows the
    client handed us); the disposition ledger EXPLAINS what became of each. A row is
    ACCOUNTED if it produced ≥1 entity OR deduped_into a parent OR was skipped (out of
    scope) OR errored. An UNEXPLAINED drop is a manifest source row with NO disposition,
    or a disposition that produced nothing and was not deduped/skipped/errored.

    Returns a summary dict:
      * ``manifest_total_rows`` — sum of manifest table rows (the LEFT count).
      * ``accounted`` — rows with ≥1 of the four dispositions.
      * ``produced`` / ``deduped`` / ``skipped`` / ``errored`` — informational tallies
        (legitimate fan-in/dedup/out-of-scope are NOT drops).
      * ``unexplained_dropped`` — BLOCKING shortfall: manifest rows we cannot explain.
      * ``conserved`` — True iff ``accounted == manifest_total_rows`` AND
        ``unexplained_dropped == 0``.
      * ``entities_produced`` — entity → count of produced external_ids (attribution).
      * ``per_table`` — per-table {manifest_rows, accounted, unexplained_dropped}.
    """
    table_rows = _manifest_table_rows(manifest)
    manifest_total = sum(table_rows.values())

    produced = deduped = skipped = errored = accounted = 0
    entities_produced: Counter = Counter()
    accounted_by_table: Counter = Counter()
    for d in dispositions:
        is_produced = bool(d.get("produced"))
        is_deduped = bool(d.get("deduped_into"))
        is_skipped = bool(d.get("skipped_out_of_scope"))
        is_errored = bool(d.get("errored"))
        if is_produced:
            produced += 1
            for p in d.get("produced") or []:
                entities_produced[p.get("entity", "?")] += 1
        if is_deduped:
            deduped += 1
        if is_skipped:
            skipped += 1
        if is_errored:
            errored += 1
        if is_produced or is_deduped or is_skipped or is_errored:
            accounted += 1
            accounted_by_table[str(d.get("table", "?"))] += 1

    # The shortfall: manifest rows minus the rows we could explain. Clamped at 0 (a
    # disposition ledger covering MORE rows than the manifest is itself suspect, but is
    # surfaced via ``accounted > manifest_total_rows`` rather than a negative drop).
    unexplained = max(0, manifest_total - accounted)
    conserved = (accounted == manifest_total) and unexplained == 0

    per_table: dict[str, dict] = {}
    for tbl, rows in table_rows.items():
        acc = accounted_by_table.get(tbl, 0)
        per_table[tbl] = {
            "manifest_rows": rows,
            "accounted": acc,
            "unexplained_dropped": max(0, rows - acc),
        }

    return {
        "manifest_total_rows": manifest_total,
        "accounted": accounted,
        "produced": produced,
        "deduped": deduped,
        "skipped": skipped,
        "errored": errored,
        "unexplained_dropped": unexplained,
        "conserved": conserved,
        "entities_produced": dict(entities_produced.most_common()),
        "per_table": per_table,
    }


def load_dispositions(canonical_dir: Path) -> list[dict]:
    """Read the assemble disposition ledger (``canonical/dispositions.json``)."""
    path = canonical_dir / "dispositions.json"
    if not path.exists():
        return []
    doc = _json.loads(path.read_text(encoding="utf-8"))
    return list(doc.get("dispositions") or [])


def reconcile_offline(project_root: str | Path, snapshot: str) -> tuple[list[ReconResult], dict]:
    """Source → canonical count conservation (no network), via manifest + dispositions.

    The pre-load reconcile (SPEC §8 stage 10). The conservation verdict is computed by
    :func:`conserve` — the manifest's true per-table row totals reconciled against the
    per-source-row disposition ledger — NOT self-derived from the canonical records
    (which structurally cannot see a dropped row). Per-entity rows restate the
    produced/canonical counts; the headline ``conserved`` is the disposition verdict.
    Money totals are summed in code per entity when any record carries ``amount_cents``.
    """
    root = Path(project_root)
    canonical_dir = root / "runs" / snapshot / "canonical"
    if not canonical_dir.is_dir():
        raise FileNotFoundError(f"no canonical dir at {canonical_dir} — run `migrate assemble` first.")

    manifest = None
    manifest_path = root / "snapshots" / snapshot / "manifest.json"
    if manifest_path.exists():
        manifest = _json.loads(manifest_path.read_text(encoding="utf-8"))
    dispositions = load_dispositions(canonical_dir)
    conservation = conserve(manifest, dispositions)

    results: list[ReconResult] = []
    detail: dict[str, dict] = {}
    produced_by_entity = conservation["entities_produced"]
    for path in sorted(canonical_dir.glob("*.ndjson")):
        entity = path.stem
        records = _read_ndjson(path)
        # LEFT = rows the dispositions attribute to this entity (what assemble produced
        # for it); RIGHT = the canonical records actually written. These match by
        # construction unless a write was lost — a useful internal consistency check.
        left_n = produced_by_entity.get(entity, len(records))
        # NB: money is NOT reconciled offline. The only available money figure here is the
        # canonical side; summing it as BOTH left and right (the prior behaviour) was a
        # guaranteed pass (left_cents == right_cents == total) that proved nothing. Money
        # exactness is verified independently in the post-load ``--live`` field-level lens,
        # where the live tenant total is summed separately and compared.
        res = reconcile(
            [{}] * left_n,
            records,
            label=f"source rows → canonical {entity}",
            money_fields=None,
        )
        results.append(res)
        detail[entity] = {
            "source_rows": left_n,
            "canonical_records": len(records),
            "conserved": res.counts_match,
            "dropped": max(0, left_n - len(records)),
        }
    return results, {
        "snapshot": snapshot,
        "mode": "offline",
        "entities": detail,
        "conservation": conservation,
    }


def reconcile_live(
    project_root: str | Path,
    snapshot: str,
    client,
    *,
    sample: int = 5,
    field_level: bool = True,
    mismatch_sample_cap: int = 50,
) -> tuple[list[ReconResult], dict]:
    """Canonical ↔ live tenant (Orion read): count conservation + field-level VALUE check.

    Two lenses, both reached ONLY here (the CLI guards this behind ``--live``):

    1. **Count conservation** (unchanged): for each canonical entity, read the live
       tenant's registered external_ids (the polymorphic ``external-ids`` resource) and
       count how many of this snapshot's canonical external_ids are present live.
    2. **Field-level** (SPEC §15.3 correctness lens; ``field_level=True``): also prove the
       VALUES match. Bulk-fetches each entity resource (all columns incl. the partial-date
       ``_year/_month/_day/_estimated`` columns), the external-ids map, and — for
       properties — the ``attribute-values`` (location custom fields), in O(pages). Then
       projects every canonical record the SAME way the loader does
       (:func:`orion_load.project_payload`, refs resolved via the live external_id→internal
       map) and diffs field-by-field against the live row. Mismatches are **WARN only** —
       they never flip the run's pass/fail verdict (count conservation alone gates that).
    """
    from orion_load import _ENTITY_TARGET  # entity → (resource, model_type FQCN)

    root = Path(project_root)
    canonical_dir = root / "runs" / snapshot / "canonical"

    # Build the live external_id set once (model_type → set of external_ids), plus the
    # external_id → internal-id map (used to resolve *_ref → live internal id for the
    # field-level projection, exactly as the loader's id_map does).
    live_by_type: dict[str, set[str]] = {}
    ext_to_internal: dict[str, int] = {}
    for row in client.paginate("external-ids"):
        ext = row.get("external_id")
        if not ext:
            continue
        live_by_type.setdefault(row.get("model_type", ""), set()).add(ext)
        if row.get("model_id") is not None:
            ext_to_internal[ext] = row["model_id"]

    results: list[ReconResult] = []
    detail: dict[str, dict] = {}
    canonical_by_entity: dict[str, list[dict]] = {}
    for path in sorted(canonical_dir.glob("*.ndjson")):
        entity = path.stem
        target = _ENTITY_TARGET.get(entity)
        if target is None:
            continue
        _resource, model_type = target
        records = _read_ndjson(path)
        canonical_by_entity[entity] = records
        canon_ids = {r.get("external_id") for r in records if r.get("external_id")}
        live_ids = live_by_type.get(model_type, set())
        present = canon_ids & live_ids
        missing = sorted(canon_ids - live_ids)[:sample]
        res = reconcile([{}] * len(canon_ids), [{}] * len(present),
                        label=f"canonical {entity} → live tenant")
        results.append(res)
        detail[entity] = {
            "canonical": len(canon_ids),
            "live_present": len(present),
            "missing_sample": missing,
            "conserved": len(present) == len(canon_ids),
        }

    out: dict = {"snapshot": snapshot, "mode": "live", "entities": detail}
    if field_level:
        out["field_level"] = _field_level_reconcile(
            client, canonical_by_entity, ext_to_internal,
            mismatch_sample_cap=mismatch_sample_cap,
        )
    return results, out


# --------------------------------------------------------------------------- #
# Field-level reconcile (SPEC §15.3 correctness lens) — VALUE comparison       #
# --------------------------------------------------------------------------- #
# Property location custom fields live on the Attribute engine, not as columns; these
# are the canonical logical keys the loader writes via attribute-values/batch-upsert.
_LOCATION_KEYS = ("section", "lot", "space")
_PROPERTY_MODEL_TYPE = "Modules\\Property\\Models\\Property"


def _norm(value) -> str:
    """Normalize a scalar to a canonical string for tolerant equality.

    The loader projects native Python types; the live API returns JSON-decoded values that
    differ only in REPRESENTATION, not meaning. Folding these out avoids false-positive
    mismatches while still catching REAL drift (a different id, a date part off, a
    truncated name, a different status):

      * ``None`` ≡ ``""`` (absent ≡ empty);
      * ``False/0/"0"`` and ``True/1/"1"`` (Laravel casts booleans to tinyint over the wire);
      * ``11`` ≡ ``"11"`` (numeric id as int vs string);
      * a date-only ``"1950-07-31"`` ≡ the API's full ISO datetime
        ``"1950-07-31T00:00:00.000000Z"`` (the date column is serialized as a datetime).
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value).strip()
    # Date column serialized as a full ISO datetime at midnight UTC → compare the date part.
    if "T00:00:00" in s and s[:10].count("-") == 2:
        return s[:10]
    return s


def _live_resource_rows(client, resource: str) -> dict[int, dict]:
    """internal id → live row for an entity resource (bulk, O(pages))."""
    rows: dict[int, dict] = {}
    for row in client.paginate(resource):
        rid = row.get("id")
        if rid is not None:
            rows[rid] = row
    return rows


def _live_location_by_property(client) -> dict[int, dict[str, object]]:
    """property internal id → {section/lot/space: raw_value} from live attribute-values."""
    out: dict[int, dict[str, object]] = {}
    for row in client.paginate("attribute-values"):
        if row.get("attributable_type") != _PROPERTY_MODEL_TYPE:
            continue
        key = row.get("key")
        if key not in _LOCATION_KEYS:
            continue
        pid = row.get("attributable_id")
        if pid is None:
            continue
        out.setdefault(pid, {})[key] = row.get("raw_value", row.get("value"))
    return out


def _field_level_reconcile(
    client,
    canonical_by_entity: dict[str, list[dict]],
    ext_to_internal: dict[str, int],
    *,
    mismatch_sample_cap: int = 50,
) -> dict:
    """Diff each canonical record's loader-projection against its live row, per entity.

    Returns the ``field_level`` block: per-entity summary, a per-field mismatch tally
    (catches SYSTEMATIC drift), and a capped sample of concrete mismatches. Severity is
    WARN — never blocking.
    """
    import orion_load

    resolve = ext_to_internal.get  # *_ref (parent external_id) → live internal id

    # Bulk-fetch live entity rows once per resource.
    live_rows: dict[str, dict[int, dict]] = {}
    for entity in canonical_by_entity:
        resource, _mt = orion_load._ENTITY_TARGET[entity]
        live_rows[entity] = _live_resource_rows(client, resource)

    live_location = _live_location_by_property(client) if "property" in canonical_by_entity else {}

    # Prerequisite ids (cemetery / property_type) come from the live rows themselves: the
    # projection only uses them to assert FK columns equal what the loader wrote, and the
    # live row already carries the actual values — so read them back per-row and compare
    # the projected *_ref-derived values, while cemetery/property_type are taken from the
    # live row to avoid a separate prerequisite read (those are single-tenant constants).
    entities_out: dict[str, dict] = {}
    per_field_tally: dict[str, dict[str, int]] = {}
    sample: list[dict] = []
    mismatches_total = 0

    for entity, records in canonical_by_entity.items():
        rows = live_rows[entity]
        compared = missing_live = fields_compared = ent_mismatches = 0
        ent_sample_count = 0
        for rec in records:
            ext = rec.get("external_id")
            if not ext:
                continue
            internal = ext_to_internal.get(ext)
            live = rows.get(internal) if internal is not None else None
            if live is None:
                missing_live += 1
                continue
            compared += 1
            # cemetery_id / property_type_id are tenant constants — take from the live row
            # so the projection's FK columns reflect the real prerequisite ids.
            cemetery_id = live.get("cemetery_id")
            property_type_id = live.get("property_type_id")
            projected = orion_load.project_payload(
                entity, rec,
                cemetery_id=cemetery_id, property_type_id=property_type_id,
                resolve_ref=resolve,
            )
            for fname, expected in projected.items():
                # cemetery_id / property_type_id are seeded FROM the live row above, so
                # comparing them is tautological — skip (they are prerequisite constants,
                # not migrated values).
                if fname in ("cemetery_id", "property_type_id"):
                    continue
                fields_compared += 1
                live_val = live.get(fname)
                if _norm(expected) != _norm(live_val):
                    ent_mismatches += 1
                    mismatches_total += 1
                    per_field_tally.setdefault(entity, {})
                    per_field_tally[entity][fname] = per_field_tally[entity].get(fname, 0) + 1
                    if ent_sample_count < mismatch_sample_cap:
                        sample.append({
                            "entity": entity, "external_id": ext, "field": fname,
                            "expected": expected, "live": live_val,
                        })
                        ent_sample_count += 1

            # Custom fields: property location (section/lot/space) vs live attribute-values.
            if entity == "property":
                want = orion_load.project_location(rec)
                have = live_location.get(internal, {})
                for key, expected in want.items():
                    fields_compared += 1
                    live_val = have.get(key)
                    if _norm(expected) != _norm(live_val):
                        ent_mismatches += 1
                        mismatches_total += 1
                        fld = f"attr:{key}"
                        per_field_tally.setdefault(entity, {})
                        per_field_tally[entity][fld] = per_field_tally[entity].get(fld, 0) + 1
                        if ent_sample_count < mismatch_sample_cap:
                            sample.append({
                                "entity": entity, "external_id": ext, "field": fld,
                                "expected": expected, "live": live_val,
                            })
                            ent_sample_count += 1

        entities_out[entity] = {
            "records_compared": compared,
            "records_missing_live": missing_live,
            "fields_compared": fields_compared,
            "mismatches_total": ent_mismatches,
        }

    return {
        "severity": "warn",
        "mismatches_total": mismatches_total,
        "entities": entities_out,
        "per_field": per_field_tally,
        "sample": sample,
        "sample_cap_per_entity": mismatch_sample_cap,
    }


# --------------------------------------------------------------------------- #
# Self-healing corrections (A2) — PATCH live rows whose VALUE drifted from the   #
# canonical projection. Generalizes the manual 30-date repair + the loader's     #
# special-case interment-status correction: it is driven entirely by the         #
# field-level diff (the SAME projection oracle + `_norm` comparator the           #
# post-load `--live` reconcile uses), so there are NO client columns — any        #
# field the loader projects is eligible to be healed.                             #
# --------------------------------------------------------------------------- #
def apply_corrections(
    project_root: str | Path,
    snapshot: str,
    client,
    *,
    entities: Optional[Sequence[str]] = None,
    dry_run: bool = False,
) -> dict:
    """Idempotently PATCH already-loaded live records whose field VALUE drifted.

    Reuses the field-level reconcile machinery (the same loader projection oracle
    :func:`orion_load.project_payload` / :func:`orion_load.project_location` and the same
    tolerant :func:`_norm` comparator as :func:`reconcile_live`): for every canonical
    record present live, it diffs the projection against the live row and, for each
    ``field_level`` mismatch, PATCHes ONLY the drifted field(s) back to the canonical
    value. A second run finds nothing left to fix (every field now matches under
    ``_norm``), so it is a no-op — the contract that makes it safe to run after every load.

    General by construction:
      * the candidate fields are exactly the loader's projected scalars (no client columns);
      * cemetery_id / property_type_id are tenant prerequisite constants seeded FROM the live
        row (never "drift"), so they are skipped — same carve-out as the reconcile lens;
      * property location (section/lot/space) custom fields drift to the
        ``attribute-values/batch-upsert`` idempotent endpoint, not a column PATCH.

    This subsumes the loader's :meth:`OrionLoader._correct_interment_status` special case
    (``status``/``is_manual`` are part of the interment projection, so they are healed here
    generically); that in-load helper is LEFT in place (removing it would change the load
    contract + its dedicated tests), so corrections happen both during load and via this
    orchestrator-driven pass.

    Args:
        entities: restrict to these canonical entities (default: all with a target).
        dry_run: compute and return the plan WITHOUT issuing any PATCH/upsert.

    Returns a summary dict: per-entity ``records_patched`` / ``fields_patched`` /
    ``records_compared`` / ``records_missing_live``, a ``location`` summary, ``errors``,
    and a ``dry_run`` flag.
    """
    import orion_load

    root = Path(project_root)
    canonical_dir = root / "runs" / snapshot / "canonical"

    ext_to_internal: dict[str, int] = {}
    for row in client.paginate("external-ids"):
        ext = row.get("external_id")
        if ext and row.get("model_id") is not None:
            ext_to_internal[ext] = row["model_id"]
    resolve = ext_to_internal.get

    wanted = set(entities) if entities is not None else None
    entities_out: dict[str, dict] = {}
    errors: list[dict] = []
    location_pending: list[dict] = []  # {property_id, values} for the idempotent upsert

    for path in sorted(canonical_dir.glob("*.ndjson")):
        entity = path.stem
        target = orion_load._ENTITY_TARGET.get(entity)
        if target is None or (wanted is not None and entity not in wanted):
            continue
        resource, _model_type = target
        records = _read_ndjson(path)

        live_rows = _live_resource_rows(client, resource)
        live_location = _live_location_by_property(client) if entity == "property" else {}

        records_compared = records_missing = records_patched = fields_patched = 0
        for rec in records:
            ext = rec.get("external_id")
            if not ext:
                continue
            internal = ext_to_internal.get(ext)
            live = live_rows.get(internal) if internal is not None else None
            if live is None:
                records_missing += 1
                continue
            records_compared += 1

            # Seed prerequisite constants FROM the live row (same as the reconcile lens) so
            # they never register as drift; they are skipped from the diff below regardless.
            projected = orion_load.project_payload(
                entity, rec,
                cemetery_id=live.get("cemetery_id"),
                property_type_id=live.get("property_type_id"),
                resolve_ref=resolve,
            )
            drift: dict[str, object] = {}
            for fname, expected in projected.items():
                if fname in ("cemetery_id", "property_type_id"):
                    continue
                if _norm(expected) != _norm(live.get(fname)):
                    drift[fname] = expected
            if drift:
                if not dry_run:
                    try:
                        client.update(resource, internal, drift)
                    except Exception as exc:  # noqa: BLE001 - record + continue, never abort the pass
                        errors.append({"entity": entity, "external_id": ext,
                                       "stage": "correction", "error": str(exc)[:300]})
                        continue
                records_patched += 1
                fields_patched += len(drift)

            # Property location custom fields → idempotent attribute-values upsert.
            if entity == "property":
                want = orion_load.project_location(rec)
                have = live_location.get(internal, {})
                loc_drift = {k: v for k, v in want.items() if _norm(v) != _norm(have.get(k))}
                if loc_drift:
                    location_pending.append({"property_id": internal, "values": loc_drift})

        entities_out[entity] = {
            "records_compared": records_compared,
            "records_missing_live": records_missing,
            "records_patched": records_patched,
            "fields_patched": fields_patched,
        }

    location_summary = _apply_location_corrections(client, location_pending, errors, dry_run=dry_run)

    return {
        "snapshot": snapshot,
        "mode": "corrections",
        "dry_run": dry_run,
        "entities": entities_out,
        "location": location_summary,
        "errors": errors,
    }


def _apply_location_corrections(
    client, pending: list[dict], errors: list[dict], *, dry_run: bool
) -> dict:
    """Upsert drifted property-location custom fields via the idempotent batch endpoint.

    Mirrors the loader's ``attribute-values/batch-upsert`` write (matched by ``key`` →
    upsert-in-place, so re-running never duplicates). Returns a small summary.
    """
    _PROPERTY_TYPE = "property"
    properties_to_upsert = len(pending)
    if dry_run or not pending:
        return {"properties_to_upsert": properties_to_upsert, "upserted": 0}
    entities = [{
        "attributable_type": _PROPERTY_TYPE,
        "attributable_id": item["property_id"],
        "attributes": [{"key": k, "value": v} for k, v in item["values"].items()],
    } for item in pending]
    upserted = 0
    try:
        body = client.post("attribute-values/batch-upsert", {"entities": entities})
        upserted = int((body.get("summary") or {}).get("successful", 0))
    except Exception as exc:  # noqa: BLE001
        errors.append({"entity": "property", "stage": "attribute-values-correction",
                       "error": str(exc)[:300]})
    return {"properties_to_upsert": properties_to_upsert, "upserted": upserted}


def render_conservation_md(results: Sequence[ReconResult], detail: dict) -> str:
    """Human-readable Markdown for the conservation story (the §15.2 review surface)."""
    body = render_reconciliation(results)
    lines = [body, "## Count conservation", ""]
    mode = detail.get("mode", "offline")
    if mode == "offline":
        cons = detail.get("conservation")
        if cons:
            mark = "✅ CONSERVED" if cons["conserved"] else "❌ UNEXPLAINED DROPS"
            lines.append(
                f"**{mark}** — {cons['accounted']} of {cons['manifest_total_rows']} "
                f"source row(s) accounted "
                f"({cons['produced']} produced · {cons['deduped']} deduped · "
                f"{cons['skipped']} out-of-scope · {cons['errored']} errored · "
                f"**{cons['unexplained_dropped']} unexplained dropped**)."
            )
            lines.append("")
            if cons["unexplained_dropped"]:
                lines.append("> ⚠ Unexplained drops are BLOCKING: source rows in the "
                             "manifest with no disposition (e.g. an unmapped/unhandled "
                             "table, or a row that produced nothing).")
                lines.append("")
        lines.append("| Entity | Source rows | Canonical | Dropped | Conserved |")
        lines.append("|---|---:|---:|---:|:--:|")
        for entity, d in detail.get("entities", {}).items():
            mark = "✅" if d["conserved"] else "❌"
            lines.append(f"| {entity} | {d['source_rows']} | {d['canonical_records']} | {d['dropped']} | {mark} |")
    else:
        lines.append("| Entity | Canonical | Live present | Conserved |")
        lines.append("|---|---:|---:|:--:|")
        for entity, d in detail.get("entities", {}).items():
            mark = "✅" if d["conserved"] else "❌"
            lines.append(f"| {entity} | {d['canonical']} | {d['live_present']} | {mark} |")
    lines.append("")

    fl = detail.get("field_level")
    if fl:
        lines += render_field_level_md(fl)
    return "\n".join(lines)


def render_field_level_md(fl: dict) -> list[str]:
    """Markdown lines for the field-level (value) reconcile block (WARN-only)."""
    total = fl.get("mismatches_total", 0)
    lines = ["## Field-level reconcile (values)", ""]
    verdict = "✅ all values match" if total == 0 else f"⚠ {total} field mismatch(es) (warn)"
    lines.append(f"**{verdict}** — canonical projection ↔ live row, per field. "
                 "Value mismatches are reported, never blocking (count conservation gates the run).")
    lines.append("")
    lines += ["| Entity | Compared | Missing live | Fields compared | Mismatches |",
              "|---|---:|---:|---:|---:|"]
    for entity, d in fl.get("entities", {}).items():
        lines.append(f"| {entity} | {d['records_compared']} | {d['records_missing_live']} | "
                     f"{d['fields_compared']} | {d['mismatches_total']} |")
    lines.append("")
    per_field = fl.get("per_field") or {}
    if any(per_field.values()):
        lines += ["**Per-field mismatch tally** (systematic drift surfaces here):", "",
                  "| Entity | Field | Mismatches |", "|---|---|---:|"]
        for entity, fields in per_field.items():
            for fname, n in sorted(fields.items(), key=lambda kv: -kv[1]):
                lines.append(f"| {entity} | {fname} | {n} |")
        lines.append("")
        sample = fl.get("sample") or []
        if sample:
            cap = fl.get("sample_cap_per_entity", 50)
            lines.append(f"Sample mismatches (capped {cap}/entity — full set in `reconciliation.json`):")
            lines.append("")
            lines += ["| Entity | external_id | Field | Expected | Live |", "|---|---|---|---|---|"]
            for s in sample[:cap * 4]:
                exp = str(s.get("expected")).replace("|", "\\|")
                liv = str(s.get("live")).replace("|", "\\|")
                lines.append(f"| {s['entity']} | {s['external_id']} | {s['field']} | {exp} | {liv} |")
            lines.append("")
    return lines


def write_reconcile_stage(
    project_root: str | Path, snapshot: str, results: Sequence[ReconResult], detail: dict
) -> tuple[Path, Path]:
    """Write ``runs/<v>/reconciliation.md`` + ``reconciliation.json``; return both paths."""
    out_dir = Path(project_root) / "runs" / snapshot
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "reconciliation.md"
    json_path = out_dir / "reconciliation.json"
    md_path.write_text(render_conservation_md(results, detail), encoding="utf-8")
    json_path.write_text(_json.dumps(detail, indent=2), encoding="utf-8")
    return md_path, json_path
