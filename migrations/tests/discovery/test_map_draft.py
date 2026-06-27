"""Auto-draft mapping tests (SPEC §8 stage 5).

A synthetic flat-register table → asserts confident 1:1 mappings + a value-set
resolution + that an unmapped-required field becomes a gap. All synthetic.
"""

from __future__ import annotations

import map_draft


def _drafts(project, project_sources):
    return map_draft.compute_drafts(project, "v1", sources=project_sources(project))


def test_confident_one_to_one_mappings(fresh_acme, project_sources):
    drafts = _drafts(fresh_acme, project_sources)
    assert len(drafts) == 1
    td = drafts[0]
    by_source = {c.source: c for c in td.columns}

    # Clear name columns map confidently to the right entity.field.
    assert by_source["first"].action == "map"
    assert by_source["first"].target == "customer.first_name"
    assert by_source["first"].confidence >= 0.85
    assert by_source["last"].target == "customer.last_name"

    # Split Y/M/D families compose into the partial-date logical field.
    assert by_source["birth_year"].target == "customer.dob.year"
    assert by_source["death_year"].target == "interment.dod.year"


def test_source_key_columns_become_external_id(fresh_acme, project_sources):
    drafts = _drafts(fresh_acme, project_sources)
    by_source = {c.source: c for c in drafts[0].columns}
    # plot_no is the confirmed source_key -> external_id (the grave identity / dedup key).
    assert by_source["plot_no"].action == "external_id"


def test_value_set_resolution_against_reference_data(fresh_acme, project_sources):
    drafts = _drafts(fresh_acme, project_sources)
    td = drafts[0]
    # ITYPE is a coded column matching the interment_type list_option binding.
    itype = next(c for c in td.columns if c.source == "itype")
    assert itype.action == "value_map"
    assert itype.target == "interment.interment_type_id"

    vs = next(v for v in td.value_sets if v.column == "itype")
    # Both codes resolve cleanly to a REAL tenant list_option id (no invented ids).
    assert vs.resolved == {"BUR": 11, "CRE": 12}
    assert vs.missing == []


def test_unmapped_required_field_becomes_a_gap(fresh_acme, project_sources):
    drafts = _drafts(fresh_acme, project_sources)
    td = drafts[0]
    gap_kinds = {g["kind"] for g in td.gaps}
    # `status` (customer + interment) is required-on-insert but has no source column.
    missing_required = [g for g in td.gaps if g["kind"] == "missing_required"]
    fields = {(g["entity"], g["field"]) for g in missing_required}
    assert ("customer", "status") in fields or ("interment", "status") in fields
    # And the structural routing is DEFERRED (inferred), not silently decided.
    assert td.primary_inferred is True


def test_value_set_with_unresolvable_code_is_flagged(fresh_acme, project_sources):
    # An UNRESOLVABLE code does not get an invented id — it becomes a gap (§9.2).
    import json

    # Poison the reference data so CRE no longer resolves.
    ref = fresh_acme / "ledger" / "reference_data.json"
    ref.write_text(json.dumps({"list_options": {"interment_type": [
        {"id": 11, "name": "Burial", "key": "interment-type-burial"},
    ]}}), encoding="utf-8")

    drafts = map_draft.compute_drafts(fresh_acme, "v1", sources=project_sources(fresh_acme))
    vs = next(v for v in drafts[0].value_sets if v.column == "itype")
    assert vs.resolved == {"BUR": 11}
    assert "CRE" in vs.missing


def test_never_clobbers_a_settled_ledger(fresh_acme, project_sources):
    import yaml

    # Write a SETTLED (non-draft) mapping; map_draft must write a sidecar, not clobber it.
    settled = {"schema_version": 1, "tables": [{"source_table": "register",
               "target_entity": "property", "columns": []}]}
    mapping_path = fresh_acme / "ledger" / "mapping.yaml"
    mapping_path.write_text(yaml.safe_dump(settled), encoding="utf-8")
    before = mapping_path.read_text(encoding="utf-8")

    result = map_draft.map_draft(fresh_acme, "v1", sources=project_sources(fresh_acme))

    assert result.settled_existed is True
    assert mapping_path.read_text(encoding="utf-8") == before  # untouched
    assert result.mapping_path.name == "mapping.yaml.draft"
    assert result.mapping_path.exists()
