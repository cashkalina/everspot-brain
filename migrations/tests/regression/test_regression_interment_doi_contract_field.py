"""Regression — LESSONS.md #8: standalone interment builder emitted a non-contract field.

THE BUG: ``assemble._build_interment_table`` (the standalone BURIALS-only path, used
when an interment table declares NO ``secondary_entities``) wrote the interment date
into a scalar field ``interment_date`` that does NOT exist in the Target Contract. The
contract gate in ``_emit`` (``validate_or_raise``) therefore raised a
``ContractViolation`` ("unknown_field interment.interment_date") on EVERY such row →
the entire standalone-interment path was dead.

THE FIX: the interment date is the canonical partial-date field ``doi`` (date of
interment). ``normalize_date`` already returns a ``{year,month,day,estimated}`` object,
so it drops straight into ``doi`` and validates against the contract.

A reversion (back to ``interment_date``) fails this: ``build_table`` raises
``ContractViolation`` instead of emitting a valid interment.
"""

import tempfile
from pathlib import Path

import pandas as pd

from assemble import _Builder, _Transformer
from external_ids import ExternalIdLedger
from ledger import ColumnMapping, Ledger, MappingSpec


def _standalone_interment_builder():
    tmp = Path(tempfile.mkdtemp())
    return _Builder(Ledger(ledger_dir=tmp), ExternalIdLedger(tmp / "e.json"), _Transformer(None))


def _spec():
    return MappingSpec(
        source_table="BURIALS",
        target_entity="interment",  # NO secondary_entities → standalone builder path
        columns=[
            ColumnMapping(source="name", action="split_name",
                          targets=["first_name", "last_name"], transform="parse_name"),
            ColumnMapping(source="dod", action="map", target="interment_date",
                          transform="normalize_date"),
        ],
    )


def _df():
    return pd.DataFrame({
        "name": ["John Smith"],
        "dod": ["1981-11-02"],
        "source_id": ["BURIALS:1"],
        "row_hash": ["x"],
    })


def test_regression_interment_doi_contract_field():
    builder = _standalone_interment_builder()
    # Must NOT raise a ContractViolation (the bug raised on every row).
    builder.build_table(_spec(), _df(), None)

    interment = builder.records["interment"][0]
    # The date lands on the contract field `doi` as a partial-date object ...
    assert interment["doi"] == {"year": 1981, "month": 11, "day": 2, "estimated": False}
    # ... and the non-contract `interment_date` field is gone.
    assert "interment_date" not in interment
    # deceased_ref is still required + non-null.
    assert interment["deceased_ref"] is not None


def test_standalone_interment_passes_the_contract():
    import contract

    builder = _standalone_interment_builder()
    builder.build_table(_spec(), _df(), None)
    interment = builder.records["interment"][0]
    assert contract.validate_record("interment", interment) == []
