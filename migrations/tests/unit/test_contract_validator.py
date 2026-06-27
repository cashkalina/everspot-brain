"""Unit tests for the Target Contract validator (``contract.py``, SPEC §6.4).

The single validator behind three call sites (assemble / emit / orion_load). These
tests lock its silent-drop guards: unknown field, missing required field/FK, type
mismatch, a non-external-id ref, a malformed partial-date object, and unknown entity.
"""

import contract


def _valid_property_group():
    return {
        "external_id": "src:property_group:G1",
        "name": "Default Section",
        "cemetery_ref": "src:cemetery:default",
        "_provenance": {"table": "PLOTS", "row": 1},
        "_confidence": 1.0,
    }


def test_valid_record_has_no_violations():
    assert contract.validate_record("property_group", _valid_property_group()) == []


def test_unknown_field_is_a_silent_drop_guard_violation():
    rec = _valid_property_group()
    rec["bogus_column"] = "x"
    violations = contract.validate_record("property_group", rec)
    assert any(v.kind == "unknown_field" and v.field == "bogus_column" for v in violations)


def test_missing_required_field_is_flagged():
    rec = _valid_property_group()
    del rec["name"]
    violations = contract.validate_record("property_group", rec)
    assert any(v.kind == "missing_required" and v.field == "name" for v in violations)


def test_null_required_field_is_flagged():
    rec = _valid_property_group()
    rec["cemetery_ref"] = None
    violations = contract.validate_record("property_group", rec)
    assert any(v.kind == "missing_required" and v.field == "cemetery_ref" for v in violations)


def test_fk_must_be_an_external_id_string():
    rec = _valid_property_group()
    rec["cemetery_ref"] = 42  # an internal id, not a 'src:...' ref
    violations = contract.validate_record("property_group", rec)
    assert any(v.kind == "bad_ref" and v.field == "cemetery_ref" for v in violations)


def test_type_mismatch_is_flagged():
    rec = _valid_property_group()
    rec["name"] = 123  # should be a string
    violations = contract.validate_record("property_group", rec)
    assert any(v.kind == "type_mismatch" and v.field == "name" for v in violations)


def test_boolean_is_not_accepted_as_integer():
    # bool is a subclass of int in python — the contract must guard against it.
    rec = {
        "external_id": "src:interment:1",
        "deceased_ref": "src:customer:1",
        "status": "completed",
        "age": True,
        "_provenance": {"table": "B", "row": 1},
        "_confidence": 1.0,
    }
    violations = contract.validate_record("interment", rec)
    assert any(v.kind == "type_mismatch" and v.field == "age" for v in violations)


def test_malformed_partial_date_is_flagged():
    rec = {
        "external_id": "src:interment:1",
        "deceased_ref": "src:customer:1",
        "status": "completed",
        "dob": {"year": "1923"},  # year must be int, and missing keys/extra shape
        "_provenance": {"table": "B", "row": 1},
        "_confidence": 1.0,
    }
    violations = contract.validate_record("interment", rec)
    assert any(v.kind == "bad_partial_date" and v.field == "dob" for v in violations)


def test_well_formed_partial_date_passes():
    rec = {
        "external_id": "src:interment:1",
        "deceased_ref": "src:customer:1",
        "status": "completed",
        "dob": {"year": 1923, "month": 4, "day": None, "estimated": True},
        "_provenance": {"table": "B", "row": 1},
        "_confidence": 1.0,
    }
    assert contract.validate_record("interment", rec) == []


def test_unknown_entity_is_flagged():
    violations = contract.validate_record("not_an_entity", {"external_id": "src:x:1"})
    assert len(violations) == 1
    assert violations[0].kind == "unknown_entity"


def test_validate_or_raise_raises_on_breach():
    rec = _valid_property_group()
    del rec["name"]
    try:
        contract.validate_or_raise("property_group", rec)
        raise AssertionError("expected ContractViolation")
    except contract.ContractViolation as exc:
        assert exc.violations
