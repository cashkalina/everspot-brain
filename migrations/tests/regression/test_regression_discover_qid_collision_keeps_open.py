"""Regression (L5): discover dedupe must not let an auto-resolved question mask a
same-id OPEN one when the two are genuinely DIFFERENT subjects.

The dedupe keeps the higher-rank status per id (auto-resolved > open). When two
questions share an id because they are the SAME subject computed by two stages, that
is correct. But if two GENUINELY DIFFERENT subjects slug to the same ``_qid``, the
old code silently dropped the OPEN one in favour of the auto-resolved one — hiding a
real gap. The fix raises a loud collision instead of silently dropping.

Same-subject dedupe (the common, legitimate case) must still collapse quietly and
keep the higher-rank status.
"""

from __future__ import annotations

import pytest

import discover as discover_mod
from discover import Question, _dedupe_by_id


def _q(qid: str, *, status: str, kind: str = "validation",
       entity=None, field_=None, table=None, column=None,
       question: str = "q") -> Question:
    return Question(
        id=qid, gate="exception", kind=kind, question=question,
        proposed_answer=None, status=status,
        entity=entity, field_=field_, table=table, column=column,
    )


def test_same_subject_dedupes_to_higher_rank():
    # Same subject (identical kind/entity/field/table/column) seen twice -> collapse,
    # keep the higher-rank (auto-resolved) one. No collision.
    a = _q("q_validation__interment.doi", status="open",
           entity="interment", field_="doi")
    b = _q("q_validation__interment.doi", status="auto-resolved",
           entity="interment", field_="doi")
    deduped = _dedupe_by_id([a, b])
    assert len(deduped) == 1
    assert deduped[0].status == "auto-resolved"


def test_distinct_subjects_same_id_raise_collision():
    # Two GENUINELY different subjects that collide on the same id: the OPEN one must
    # NOT be silently dropped — a loud collision is raised instead.
    open_q = _q("q_validation__x", status="open",
                entity="interment", field_="cemetery_id", question="real open gap")
    auto_q = _q("q_validation__x", status="auto-resolved",
                entity="customer", field_="email", question="unrelated auto-resolved")
    with pytest.raises(ValueError, match="collision"):
        _dedupe_by_id([open_q, auto_q])


def test_open_subject_never_dropped_for_auto_resolved_collision():
    # The specific failure mode from L5: order-independent (auto first, then open).
    auto_q = _q("q_validation__x", status="auto-resolved",
                entity="customer", field_="email")
    open_q = _q("q_validation__x", status="open",
                entity="interment", field_="cemetery_id")
    with pytest.raises(ValueError, match="collision"):
        _dedupe_by_id([auto_q, open_q])
