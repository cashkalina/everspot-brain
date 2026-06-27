"""Regression — LESSONS.md #6: canonical↔emit FK name mismatch dropped the link.

THE BUG: the emitter wrote the interment's property FK from a non-existent canonical
field (``interment_space_ref``) while the canonical artifact carries ``property_ref``.
The names didn't match → the property→interment link was silently dropped at emit (the
importer's ``interment_space_id`` column came out blank even though the canonical
record knew the property).

THE FIX: ``emit_excel.py``'s interment importer maps the ``interment_space_id`` column
from the canonical ``property_ref`` field (``FK("property_ref")``); the contract is the
single name authority.

A reversion (FK back to ``interment_space_ref``) fails this: the link is dropped.
"""

import emit_excel
from emit_excel import FK


def _interment_spec():
    return next(s for s in emit_excel.IMPORTERS if s.importer == "interment")


def test_regression_interment_property_ref_name_maps_from_property_ref():
    spec = _interment_spec()
    fk = spec.columns["interment_space_id"]
    assert isinstance(fk, FK)
    assert fk.ref_field == "property_ref", (
        "interment_space_id must resolve from canonical 'property_ref' "
        "(LESSONS #6 — the FK-name-mismatch silent drop)"
    )


def test_property_link_survives_emit_to_internal_id():
    spec = _interment_spec()
    record = {
        "external_id": "src:interment:1",
        "deceased_ref": "src:customer:1",
        "property_ref": "src:property:PLOT-7",
        "status": "completed",
        "dod": {"year": 1981, "month": 11, "day": 2, "estimated": False},
        "_provenance": {"table": "BURIALS", "row": 1},
        "_confidence": 0.9,
    }
    # The property has already been loaded → its external_id resolves to internal id 555.
    id_map = {"src:property:PLOT-7": 555, "src:customer:1": 99}

    row = emit_excel.build_row(record, spec, id_map)

    # The link is carried into the importer's interment_space_id column (NOT dropped).
    assert row["interment_space_id"] == 555
    # The companion *_ref column is blank because the ref resolved.
    assert row["interment_space_id_ref"] is None


def test_unresolved_property_ref_surfaces_in_companion_column_not_dropped():
    spec = _interment_spec()
    record = {
        "external_id": "src:interment:2",
        "deceased_ref": "src:customer:2",
        "property_ref": "src:property:PLOT-9",
        "status": "completed",
        "_provenance": {"table": "BURIALS", "row": 2},
        "_confidence": 0.9,
    }
    row = emit_excel.build_row(record, spec, id_map={})  # nothing resolved yet
    # Unresolved: id column blank, but the ref is preserved in the companion column —
    # the link is never silently lost.
    assert row["interment_space_id"] is None
    assert row["interment_space_id_ref"] == "src:property:PLOT-9"
