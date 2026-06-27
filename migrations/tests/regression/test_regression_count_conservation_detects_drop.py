"""Regression (H1 / L7) — count conservation must DETECT a real source-row drop.

Before this fix, conservation derived the "source" count from
``_provenance.source_id`` stamped on the canonical records THEMSELVES. A dropped
source row leaves no record → no provenance → no count, so ``dropped`` was pinned
at 0 and "✅ Conserved" printed even after real data loss. The manifest (the true
per-table row totals) was never read.

The fix accounts for EVERY source row with a *disposition* (produced / deduped_into
/ skipped_out_of_scope / errored) and compares the manifest's total_rows against the
sum of accounted rows. An unexplained drop (a manifest row with no disposition, or a
disposition that produced nothing) is BLOCKING. Legitimate fan-in / dedup / out-of-
scope is informational.

Two synthetic fixtures (NO client data):
  1. ``test_unexplained_drop_fails_conservation`` — a source table whose target_entity
     the assembler does not build (the ``else: pass`` arm) → every row produces
     nothing and is never deduped/skipped/errored. Conservation MUST FAIL with
     ``unexplained_dropped >= 1``. (Against the OLD code this falsely passes — the
     records-derived source count is 0 == 0 canonical.)
  2. ``test_fan_in_and_dedup_passes_conservation`` — the acme flat register: one row
     fans out to property+customer+interment, and two rows sharing a plot dedupe to
     ONE property. Conservation MUST PASS (accounted == manifest.total_rows,
     unexplained_dropped == 0) even though canonical property count < source rows.
"""

from __future__ import annotations

import shutil
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import assemble as assemble_mod  # noqa: E402
import report as report_mod  # noqa: E402
import validate as validate_mod  # noqa: E402
from snapshot import SourceTableConfig, ingest_snapshot  # noqa: E402

GOLDEN_FIXTURES = Path(__file__).resolve().parents[1] / "golden" / "fixtures"


def _source_configs(project_dir: Path) -> list[SourceTableConfig]:
    py = yaml.safe_load((project_dir / "project.yaml").read_text(encoding="utf-8"))
    return [
        SourceTableConfig(
            table=s["table"],
            source_key=s.get("source_key"),
            key_status=s.get("key_status", "confirmed"),
        )
        for s in py.get("sources", [])
    ]


def _run_assemble(project: Path, snapshot: str = "v1"):
    ingest_snapshot(project / "snapshots" / snapshot, _source_configs(project))
    return assemble_mod.assemble(project, snapshot, use_cache=False, scoped=False)


# --------------------------------------------------------------------------- #
# Fixture 1 — a silent drop (unhandled target entity → rows produce nothing)   #
# --------------------------------------------------------------------------- #
def _build_dropping_fixture(dest: Path) -> Path:
    """A 3-row source table mapped to a target entity the assembler can't build.

    ``build_table`` falls through its ``else: pass`` arm for a primary entity with no
    handler and no secondaries, so NONE of the rows produce a canonical record — a
    genuine, silent source-row drop that conservation must catch.
    """
    project = dest / "dropping"
    raw = project / "snapshots" / "v1" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "widgets.csv").write_text(
        textwrap.dedent(
            """\
            WIDGET_ID,NAME
            W1,Alpha
            W2,Beta
            W3,Gamma
            """
        ),
        encoding="utf-8",
    )
    (project / "project.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "client": {"slug": "dropping", "name": "Dropping Synthetic"},
                "sources": [
                    {"table": "widgets", "source_key": ["WIDGET_ID"], "key_status": "confirmed"}
                ],
                "snapshots": [{"id": "v1", "files": ["widgets.csv"]}],
            }
        ),
        encoding="utf-8",
    )
    ledger = project / "ledger"
    ledger.mkdir(parents=True, exist_ok=True)
    # target_entity "owner_file" has no builder and no secondaries → build_table hits
    # the `else: pass` arm and every row silently vanishes.
    (ledger / "mapping.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "tables": [
                    {
                        "source_table": "widgets",
                        "target_entity": "owner_file",
                        "columns": [
                            {"source": "widget_id", "action": "external_id", "confidence": 1.0},
                            {"source": "name", "action": "map", "target": "name", "confidence": 0.9},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ledger / "value_sets.yaml").write_text(
        yaml.safe_dump({"schema_version": 1, "value_sets": []}), encoding="utf-8"
    )
    return project


def test_unexplained_drop_fails_conservation(tmp_path):
    project = _build_dropping_fixture(tmp_path)
    result = _run_assemble(project)

    # Sanity: nothing was produced for the unhandled table.
    assert sum(result.entity_counts.values()) == 0

    vres = validate_mod.validate_run(project, "v1")
    cons = vres.conservation_summary

    assert cons["manifest_total_rows"] == 3
    assert cons["unexplained_dropped"] >= 1, (
        "a source row that produced nothing must be an UNEXPLAINED drop "
        "(this is the bug: old code derived source count from the records themselves "
        "and reported 0 == 0 → falsely conserved)"
    )
    assert cons["conserved"] is False
    # The drop is BLOCKING — the validate gate must FAIL.
    assert not vres.passed
    assert any(f.kind == "count_conservation" and f.blocking for f in vres.failures)


# --------------------------------------------------------------------------- #
# Fixture 2 — legitimate fan-in + dedup must NOT false-positive                 #
# --------------------------------------------------------------------------- #
def test_fan_in_and_dedup_passes_conservation(tmp_path):
    project = tmp_path / "acme_synth"
    shutil.copytree(GOLDEN_FIXTURES / "acme_synth", project)
    result = _run_assemble(project)

    # Fan-in/dedup shape (see golden test): 4 rows → 3 properties (A-12-1 dedup),
    # 3 customers, 3 interments (A-13-1 empty grave is property-only).
    assert result.entity_counts == {
        "property_group": 1, "property": 3, "customer": 3, "interment": 3,
    }

    vres = validate_mod.validate_run(project, "v1")
    cons = vres.conservation_summary

    assert cons["manifest_total_rows"] == 4
    assert cons["accounted"] == 4, "every source row must be accounted"
    assert cons["unexplained_dropped"] == 0, "legitimate fan-in/dedup is NOT a drop"
    assert cons["conserved"] is True
    # Dedup is surfaced as informational, never blocking.
    assert cons["deduped"] >= 1
    assert vres.passed
    assert not any(f.kind == "count_conservation" and f.blocking for f in vres.failures)


# --------------------------------------------------------------------------- #
# L7 — report load aggregation must not let a shortfall hide                    #
# --------------------------------------------------------------------------- #
def test_report_folds_failed_and_unknown_load_actions(tmp_path):
    """A failed load + an UNRECOGNIZED action must surface (not be silently dropped).

    Old behaviour: ``loaded = created+updated+skipped`` (excludes failed) and an
    unrecognized action vanished — so a load shortfall could print "✅ Conserved".
    The fix folds failed/unknown into the verdict so the shortfall always shows.
    """
    run_dir = tmp_path / "runs" / "v1"
    (run_dir / "load").mkdir(parents=True, exist_ok=True)
    (run_dir / "load" / "results.jsonl").write_text(
        "\n".join(
            [
                '{"entity": "customer", "action": "created"}',
                '{"entity": "customer", "action": "failed"}',
                '{"entity": "customer", "action": "quantum_teleported"}',  # unknown → failed
            ]
        ),
        encoding="utf-8",
    )

    agg, source = report_mod._load_results(run_dir, run_dir / "canonical")
    assert source == "load/results.jsonl"
    cust = agg["customer"]
    # The unrecognized action is folded into failed — nothing is silently dropped.
    assert cust["created"] == 1
    assert cust["failed"] == 2
    assert cust["created"] + cust["updated"] + cust["skipped"] + cust["failed"] == 3

    # In the conservation table, a failure flips the per-entity conserved mark so the
    # shortfall (loaded < canonical) cannot hide behind a ✅.
    text = report_mod.render_report(
        snapshot="v1",
        manifest={"total_rows": 1, "total_tables": 1},
        canonical_counts={"customer": 1},
        conservation={"customer": {"source_rows": 1, "canonical_records": 1,
                                   "conserved": True, "dropped": 0}},
        load_agg=agg,
        load_source="load/results.jsonl",
        questions={"by_status": {}, "items": [], "total": 0},
        needs_attention_grouped={},
        validation={"gate": "PASS"},
        reconcile=None,
    )
    # customer: canonical 1, loaded 1 created but 2 failed → conserved must be ❌.
    cust_line = next(l for l in text.splitlines() if l.startswith("| customer |"))
    assert "❌" in cust_line, cust_line
