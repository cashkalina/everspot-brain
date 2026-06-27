"""Tests (SPEC §12) — the runnable `validate` (§8 stage 10) + `reconcile` stages.

Runs the deterministic spine on the SYNTHETIC ``acme_synth`` fixture, then:
  - validate PASSES the clean golden canonical set with 0 dangling refs;
  - validate FAILS when a dangling ref OR a contract violation is injected, and the
    offending failure row is reported as BLOCKING;
  - reconcile's count-conservation arithmetic is correct over the golden set.

No client data, no network, no LLM.
"""

import sys
from pathlib import Path

import pytest

GOLDEN = Path(__file__).resolve().parent
sys.path.insert(0, str(GOLDEN))

from spine import run_spine  # noqa: E402

import reconcile as reconcile_mod  # noqa: E402
import validate as validate_mod  # noqa: E402


@pytest.fixture(scope="module")
def spine(tmp_path_factory):
    dest = tmp_path_factory.mktemp("validate_recon")
    return run_spine("acme_synth", dest)


# --------------------------------------------------------------------------- #
# validate — passing case                                                      #
# --------------------------------------------------------------------------- #
def test_validate_passes_clean_golden(spine):
    result = validate_mod.validate_run(spine["project"], "v1")
    assert result.gate == "PASS"
    assert result.passed is True
    dangling = [f for f in result.blocking_failures if f.kind == "dangling_ref"]
    assert dangling == []


def test_validate_writes_artifacts(spine):
    validate_mod.validate_run(spine["project"], "v1")
    out = spine["project"] / "runs" / "v1" / "validation"
    assert (out / "validation_summary.json").exists()
    assert (out / "failures.jsonl").exists()


def test_validate_counts_match_canonical(spine):
    result = validate_mod.validate_run(spine["project"], "v1")
    assert result.entity_counts == {
        "property_group": 1, "property": 3, "customer": 3, "interment": 3,
    }


# --------------------------------------------------------------------------- #
# validate — failing cases (the pure core, with injected records)              #
# --------------------------------------------------------------------------- #
def _good_set() -> dict:
    return {
        "property_group": [{
            "external_id": "src:property_group:G1", "name": "Sec A",
            "cemetery_ref": "src:cemetery:default", "_provenance": {"table": "t", "row": 1}, "_confidence": 1.0,
        }],
        "property": [{
            "external_id": "src:property:P1", "property_group_ref": "src:property_group:G1",
            "cemetery_ref": "src:cemetery:default", "_provenance": {"table": "t", "row": 1}, "_confidence": 1.0,
        }],
        "customer": [{
            "external_id": "src:customer:C1", "status": "customer", "last_name": "SMITH",
            "_provenance": {"table": "t", "row": 1}, "_confidence": 1.0,
        }],
        "interment": [{
            "external_id": "src:interment:I1", "status": "completed", "deceased_ref": "src:customer:C1",
            "property_ref": "src:property:P1", "_provenance": {"table": "t", "row": 1}, "_confidence": 1.0,
        }],
    }


def test_validate_detects_dangling_ref():
    data = _good_set()
    # Point the interment at a customer that does not exist → dangling FK.
    data["interment"][0]["deceased_ref"] = "src:customer:DOES_NOT_EXIST"
    result = validate_mod.validate_canonical(data, snapshot="v1")
    assert result.gate == "FAIL"
    dangling = [f for f in result.blocking_failures if f.kind == "dangling_ref"]
    assert len(dangling) == 1
    assert dangling[0].field == "deceased_ref"
    assert "DOES_NOT_EXIST" in dangling[0].detail


def test_validate_detects_contract_violation():
    data = _good_set()
    # Drop the required-on-insert deceased_ref → a contract missing_required violation.
    del data["interment"][0]["deceased_ref"]
    result = validate_mod.validate_canonical(data, snapshot="v1")
    assert result.gate == "FAIL"
    contract_fails = [f for f in result.blocking_failures if f.kind == "contract"]
    assert any(f.field == "deceased_ref" for f in contract_fails)


def test_validate_ref_to_wrong_entity_is_dangling():
    data = _good_set()
    # property_ref pointing at a customer external_id → wrong-entity dangling.
    data["interment"][0]["property_ref"] = "src:customer:C1"
    result = validate_mod.validate_canonical(data, snapshot="v1")
    assert result.gate == "FAIL"
    assert any(f.kind == "dangling_ref" and f.field == "property_ref"
               for f in result.blocking_failures)


def test_cemetery_ref_prerequisite_not_dangling():
    """cemetery_ref points at the Wave-0b cemetery prereq — never counted as dangling."""
    data = _good_set()
    result = validate_mod.validate_canonical(data, snapshot="v1")
    assert not any(f.field == "cemetery_ref" for f in result.blocking_failures)


# --------------------------------------------------------------------------- #
# reconcile — count conservation arithmetic                                    #
# --------------------------------------------------------------------------- #
def test_reconcile_offline_conserves_golden_counts(spine):
    results, detail = reconcile_mod.reconcile_offline(spine["project"], "v1")
    assert detail["mode"] == "offline"
    by_entity = {r.label.split()[-1]: r for r in results}
    # 3 register rows produced 3 interments + 3 customers; 3 distinct graves; 1 group.
    assert by_entity["interment"].left_count == 3
    assert by_entity["interment"].right_count == 3
    assert by_entity["customer"].counts_match
    assert by_entity["property"].right_count == 3
    assert all(d["conserved"] for d in detail["entities"].values())
    assert all(d["dropped"] == 0 for d in detail["entities"].values())


def test_reconcile_writes_markdown_and_json(spine):
    results, detail = reconcile_mod.reconcile_offline(spine["project"], "v1")
    md, js = reconcile_mod.write_reconcile_stage(spine["project"], "v1", results, detail)
    assert md.exists() and js.exists()
    text = md.read_text()
    assert "Count conservation" in text and "PASS" in text


def test_reconcile_dropped_records_surface():
    """A canonical entity with fewer records than source rows reports the drop."""
    # Direct arithmetic check via the reconcile core (no I/O).
    res = reconcile_mod.reconcile([{}] * 10, [{}] * 7, label="source rows → canonical x")
    assert res.counts_match is False
    assert res.right_count - res.left_count == -3
