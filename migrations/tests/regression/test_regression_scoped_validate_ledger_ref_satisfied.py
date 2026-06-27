"""Regression (M2) — a scoped v2 delta with an UNCHANGED parent must validate PASS.

On a scoped (CHANGED + NEW) run the assembler emits ONLY in-scope records. An
in-scope burial whose grave is an UNCHANGED property links to that property via
``property_ref``, but the property itself is NOT re-emitted into this run's canonical
(assemble: ``if not in_scope: continue``). The property already exists in the tenant —
its external_id is in ``ledger/external_ids.json``.

Before this fix, validate resolved ``*_ref`` ONLY within the current canonical set, so
the ref to the already-minted/loaded property was reported as a BLOCKING
``dangling_ref`` — a clean v2 delta FAILED validation.

The fix: in scoped validation, seed the ext→entity index from the external_id ledger
IN ADDITION to the in-run canonical, so a ref pointing at an already-minted external_id
is SATISFIED, not dangling. A FULL run must still flag a genuinely-missing parent.

Two synthetic scenarios (NO client data):
  1. ``test_scoped_unchanged_parent_ref_is_satisfied`` — interment.property_ref points at
     a property that lives only in the ledger (not the run's canonical); scoped → PASS.
  2. ``test_full_run_genuinely_missing_ref_still_fails`` — same shape but a FULL run with
     no ledger-backed parent → the dangling ref is still BLOCKING.
  3. ``test_scoped_ledger_ref_to_wrong_entity_still_dangling`` — a ledger entry of the
     WRONG entity does not satisfy the ref (still BLOCKING) even when scoped.
  4. ``test_scoped_end_to_end_v2_delta_passes`` — a real v1-full → v2-scoped assemble of a
     separate property/interment fixture where the parent property is unchanged
     (out-of-scope) and only a new interment is in scope: validate PASS, no dangling_ref.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import assemble as assemble_mod  # noqa: E402
import validate as validate_mod  # noqa: E402
from external_ids import ExternalIdLedger  # noqa: E402
from snapshot import SourceTableConfig, ingest_snapshot  # noqa: E402


# --------------------------------------------------------------------------- #
# Core-level scenarios (validate_canonical with an external_id ledger index)    #
# --------------------------------------------------------------------------- #
def _interment_only_canonical(property_ext: str) -> dict[str, list[dict]]:
    """An in-scope interment + its decedent customer; the property is NOT in the set."""
    prov = {"table": "register", "row": 1, "source_id": "register:NEW-1"}
    return {
        "customer": [{
            "external_id": "src:customer:DECEDENT-register-NEW-1",
            "status": "customer", "first_name": "Jane", "last_name": "New",
            "_provenance": prov, "_confidence": 1.0,
        }],
        "interment": [{
            "external_id": "src:interment:register-NEW-1",
            "deceased_ref": "src:customer:DECEDENT-register-NEW-1",
            "property_ref": property_ext,
            "status": "completed",
            "_provenance": prov, "_confidence": 1.0,
        }],
    }


def _ext_index_with_property(property_ext: str) -> dict[str, str]:
    """An external_id → entity index as the ledger would yield: the property exists."""
    return {property_ext: "property"}


def test_scoped_unchanged_parent_ref_is_satisfied():
    property_ext = "src:property:register-A-12-1"
    canonical = _interment_only_canonical(property_ext)

    # Scoped run: the ledger says the property already exists → ref is SATISFIED.
    result = validate_mod.validate_canonical(
        canonical, snapshot="v2", scoped=True,
        ext_ledger_index=_ext_index_with_property(property_ext),
    )
    dangling = [f for f in result.failures if f.kind == "dangling_ref"]
    assert dangling == [], f"scoped ref to a ledger-resolved parent must not dangle: {dangling}"
    assert result.passed


def test_full_run_genuinely_missing_ref_still_fails():
    property_ext = "src:property:register-A-12-1"
    canonical = _interment_only_canonical(property_ext)

    # FULL run: no ledger index is consulted → a missing parent is still BLOCKING.
    result = validate_mod.validate_canonical(
        canonical, snapshot="v1", scoped=False,
        ext_ledger_index=_ext_index_with_property(property_ext),
    )
    dangling = [f for f in result.failures if f.kind == "dangling_ref" and f.blocking]
    assert dangling, "a full run must still flag a genuinely-missing parent ref"
    assert not result.passed


def test_scoped_ledger_ref_to_wrong_entity_still_dangling():
    property_ext = "src:property:register-A-12-1"
    canonical = _interment_only_canonical(property_ext)

    # The ledger has the id but as the WRONG kind of record (a customer, not a property)
    # — a ref to the wrong entity is dangling even when scoped + ledger-resolved.
    result = validate_mod.validate_canonical(
        canonical, snapshot="v2", scoped=True,
        ext_ledger_index={property_ext: "customer"},
    )
    dangling = [f for f in result.failures if f.kind == "dangling_ref" and f.blocking]
    assert dangling, "a ledger entry of the wrong entity must not satisfy the ref"


# --------------------------------------------------------------------------- #
# End-to-end: v1 full → v2 scoped assemble of a separate property/interment set #
# --------------------------------------------------------------------------- #
def _build_separate_table_project(dest: Path) -> Path:
    """A project with a standalone PLOTS (property) table + a BURIALS (interment) table.

    Distinct tables (not the combined flat register) so a scoped v2 can add a NEW
    burial into an UNCHANGED grave: the property table row is out-of-scope (skipped,
    its external_id stays only in the ledger) while the new interment is in scope and
    links to it via property_ref.
    """
    project = dest / "sep"
    for snap in ("v1", "v2"):
        (project / "snapshots" / snap / "raw").mkdir(parents=True, exist_ok=True)

    # v1: one grave, one burial.
    (project / "snapshots" / "v1" / "raw" / "plots.csv").write_text(
        textwrap.dedent("""\
            PLOT_NO,SECTION,LOT,SPACE
            A-12-1,A,12,1
            """), encoding="utf-8")
    (project / "snapshots" / "v1" / "raw" / "burials.csv").write_text(
        textwrap.dedent("""\
            BURIAL_ID,PLOT_NO,FIRST,LAST
            B1,A-12-1,John,Smith
            """), encoding="utf-8")

    # v2: SAME grave (unchanged), a NEW second burial in it.
    (project / "snapshots" / "v2" / "raw" / "plots.csv").write_text(
        textwrap.dedent("""\
            PLOT_NO,SECTION,LOT,SPACE
            A-12-1,A,12,1
            """), encoding="utf-8")
    (project / "snapshots" / "v2" / "raw" / "burials.csv").write_text(
        textwrap.dedent("""\
            BURIAL_ID,PLOT_NO,FIRST,LAST
            B1,A-12-1,John,Smith
            B2,A-12-1,Mary,Smith
            """), encoding="utf-8")

    (project / "project.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "client": {"slug": "sep", "name": "Separate-Table Synthetic"},
        "sources": [
            {"table": "plots", "source_key": ["PLOT_NO"], "key_status": "confirmed"},
            {"table": "burials", "source_key": ["BURIAL_ID"], "key_status": "confirmed"},
        ],
        "snapshots": [
            {"id": "v1", "files": ["plots.csv", "burials.csv"]},
            {"id": "v2", "files": ["plots.csv", "burials.csv"]},
        ],
    }), encoding="utf-8")

    ledger = project / "ledger"
    ledger.mkdir(parents=True, exist_ok=True)
    (ledger / "mapping.yaml").write_text(yaml.safe_dump({
        "schema_version": 1,
        "tables": [
            {
                "source_table": "plots",
                "target_entity": "property",
                "columns": [
                    {"source": "plot_no", "action": "external_id", "confidence": 1.0},
                    {"source": "section", "action": "map", "target": "section", "confidence": 0.95},
                    {"source": "lot", "action": "map", "target": "lot", "confidence": 0.95},
                    {"source": "space", "action": "map", "target": "space", "confidence": 0.95},
                ],
            },
            {
                "source_table": "burials",
                "target_entity": "interment",
                "columns": [
                    {"source": "burial_id", "action": "external_id", "confidence": 1.0},
                    {"source": "plot_no", "action": "derive", "targets": ["property_ref"],
                     "confidence": 1.0},
                    {"source": "last", "action": "split_name", "confidence": 0.95},
                ],
            },
        ],
    }), encoding="utf-8")
    (ledger / "value_sets.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "value_sets": []}), encoding="utf-8")
    return project


def _source_configs(project: Path) -> list[SourceTableConfig]:
    py = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8"))
    return [SourceTableConfig(table=s["table"], source_key=s.get("source_key"),
                              key_status=s.get("key_status", "confirmed"))
            for s in py.get("sources", [])]


def test_scoped_end_to_end_v2_delta_passes(tmp_path):
    project = _build_separate_table_project(tmp_path)
    cfgs = _source_configs(project)

    # v1 full — mints the property + first burial into ledger/external_ids.json.
    ingest_snapshot(project / "snapshots" / "v1", cfgs)
    assemble_mod.assemble(project, "v1", use_cache=False, scoped=False)

    # v2 scoped — only the NEW burial B2 is in scope; the grave (plots) is unchanged.
    ingest_snapshot(project / "snapshots" / "v2", cfgs)
    (project / "snapshots" / "v2" / "delta.json").write_text(
        json.dumps({
            "tables": {
                "burials": {"new": ["burials:B2"], "changed": [], "unchanged": ["burials:B1"], "removed": []},
                "plots": {"new": [], "changed": [], "unchanged": ["plots:A-12-1"], "removed": []},
            }
        }), encoding="utf-8")
    assemble_mod.assemble(project, "v2", use_cache=False, scoped=True)

    # The property is NOT in v2's canonical (out-of-scope), but IS in the ledger.
    ledger = ExternalIdLedger(project / "ledger" / "external_ids.json")
    prop_ext = ledger.lookup_by_source("plots:A-12-1")
    assert prop_ext is not None, "v1 must have minted the property into the ledger"

    result = validate_mod.validate_run(project, "v2")
    dangling = [f for f in result.failures if f.kind == "dangling_ref"]
    assert dangling == [], f"scoped v2 with an unchanged ledger-backed parent must not dangle: {dangling}"
    assert result.passed, f"scoped v2 delta must PASS: {[f.to_dict() for f in result.blocking_failures]}"
