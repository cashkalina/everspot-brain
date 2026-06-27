"""Schema-conformance tests (SPEC §12).

Two guarantees over the golden-fixture run:
  1. every canonical record validates against ``canonical-record.schema.json``;
  2. every canonical record validates against the **target contract** (§6) via
     ``contract.validate_record`` (the same gate assemble / emit / orion_load apply).

The canonical schema is a ``oneOf`` over property_group/property/customer/interment;
we validate each entity's records against its named ``$defs/<entity>`` subschema so a
failure pinpoints the entity + field.
"""

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import contract

GOLDEN = Path(__file__).resolve().parent.parent / "golden"
sys.path.insert(0, str(GOLDEN))

from spine import run_spine  # noqa: E402

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent / "schemas" / "canonical-record.schema.json"
)
ENTITIES = ["property_group", "property", "customer", "interment"]


@pytest.fixture(scope="module")
def canonical_records(tmp_path_factory):
    dest = tmp_path_factory.mktemp("conformance")
    art = run_spine("acme_synth", dest)
    out = {}
    for entity in ENTITIES:
        path = art["canonical_dir"] / f"{entity}.ndjson"
        out[entity] = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return out


@pytest.fixture(scope="module")
def canonical_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _entity_validator(schema: dict, entity: str) -> Draft202012Validator:
    """A validator bound to the entity's ``$defs/<entity>`` subschema (keeps $defs/$ref)."""
    subschema = {**schema["$defs"][entity], "$defs": schema["$defs"]}
    return Draft202012Validator(subschema)


@pytest.mark.parametrize("entity", ENTITIES)
def test_every_canonical_record_matches_canonical_schema(canonical_records, canonical_schema, entity):
    validator = _entity_validator(canonical_schema, entity)
    for rec in canonical_records[entity]:
        errors = sorted(validator.iter_errors(rec), key=str)
        assert not errors, f"{entity} record {rec.get('external_id')}: {[e.message for e in errors]}"


@pytest.mark.parametrize("entity", ENTITIES)
def test_every_canonical_record_passes_the_target_contract(canonical_records, entity):
    for rec in canonical_records[entity]:
        violations = contract.validate_record(entity, rec)
        assert not violations, f"{entity} {rec.get('external_id')}: {[str(v) for v in violations]}"


def test_at_least_one_record_per_entity(canonical_records):
    for entity in ENTITIES:
        assert canonical_records[entity], f"no {entity} records produced — fixture regressed"
