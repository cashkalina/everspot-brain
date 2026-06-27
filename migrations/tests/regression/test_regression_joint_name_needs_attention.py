"""Regression — LESSONS.md #7: silent joint-name collapse.

THE BUG: a cell holding two people (``"Robert & Phyllis"``) was collapsed to one
person with NO flag; ``assemble`` emitted 0 needs-attention items for it, so a large
1→N record-count gap was invisible at the question round.

THE FIX: a first-class ``needs_attention`` category — ``assemble._Builder._apply``
flags EVERY ``needs_llm`` cell (predicate = the explicit ``cell.needs_llm`` flag),
carrying column / transform / reason but NO raw value (PII-safe);
``summarize_needs_attention`` groups them so structural cases (two_people) surface.

A reversion (silently accepting a ``needs_llm`` cell) fails this: no item is flagged.
"""

from assemble import (
    NeedsAttention,
    _Builder,
    _Transformer,
    summarize_needs_attention,
)
from external_ids import ExternalIdLedger
from ledger import Ledger, MappingSpec


def _builder(tmp_path):
    ledger = Ledger(ledger_dir=tmp_path)
    ext_ids = ExternalIdLedger(tmp_path / "external_ids.json")
    transformer = _Transformer(cache=None)
    return _Builder(ledger, ext_ids, transformer)


def test_regression_joint_name_needs_attention(tmp_path):
    builder = _builder(tmp_path)
    spec = MappingSpec(source_table="BURIALS", target_entity="interment")

    # A two-people-in-one-cell name routes to needs_llm in parse_name → assemble
    # must flag it (not silently collapse to one person).
    cell = builder._apply("parse_name", "Robert & Phyllis", spec, "BURIALS:48213", "DECEDENT_NAME")

    assert cell.needs_llm is True
    assert len(builder.needs_attention) == 1
    na = builder.needs_attention[0]
    assert isinstance(na, NeedsAttention)
    assert na.kind == "needs_llm"
    assert na.table == "BURIALS"
    assert na.source_id == "BURIALS:48213"
    assert na.context["column"] == "DECEDENT_NAME"
    assert na.context["transform"] == "parse_name"
    assert na.context["reason"] == "two-people-in-one-cell"

    # PII-safe: the raw cell value is NOT carried in the flag.
    assert "Robert" not in na.detail
    assert "Robert" not in str(na.context)


def test_confident_single_name_does_not_flag(tmp_path):
    builder = _builder(tmp_path)
    spec = MappingSpec(source_table="BURIALS", target_entity="interment")
    cell = builder._apply("parse_name", "John Smith", spec, "BURIALS:1", "DECEDENT_NAME")
    assert cell.needs_llm is False
    assert builder.needs_attention == []


def test_summary_groups_two_people_by_reason(tmp_path):
    builder = _builder(tmp_path)
    spec = MappingSpec(source_table="BURIALS", target_entity="interment")
    builder._apply("parse_name", "Robert & Phyllis", spec, "BURIALS:1", "DECEDENT_NAME")
    builder._apply("parse_name", "John and Mary", spec, "BURIALS:2", "DECEDENT_NAME")

    summary = summarize_needs_attention(builder.needs_attention)
    assert summary["total"] == 2
    assert summary["by_kind"]["needs_llm"] == 2
    assert summary["needs_llm_by_reason"]["parse_name/two-people-in-one-cell"] == 2
