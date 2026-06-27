"""Answer / accept-all application tests (SPEC §9.5).

Applying answers updates the ledger (persisted question records + mapping/value_sets
write-back), and a subsequent assemble reflects them. Synthetic.
"""

from __future__ import annotations

import json

import yaml

import answer as answer_mod
import discover as discover_mod


def test_accept_all_persists_and_resolves(fresh_acme, project_sources):
    sources = project_sources(fresh_acme)
    discover_mod.discover(fresh_acme, "v1", sources=sources)
    result = answer_mod.apply_answers(fresh_acme, "v1", accept_all=True)

    # Every answerable question got persisted to the ledger.
    qdir = fresh_acme / "ledger" / "questions"
    assert qdir.is_dir()
    persisted = list(qdir.glob("q_*.json"))
    assert persisted, "accept-all must persist question records"
    # The auto-resolved value-set was applied so assemble can read it.
    assert result.applied_value_sets >= 1


def test_accept_all_writes_back_value_set_ids(fresh_acme, project_sources):
    sources = project_sources(fresh_acme)
    discover_mod.discover(fresh_acme, "v1", sources=sources)
    answer_mod.apply_answers(fresh_acme, "v1", accept_all=True)

    # value_sets.yaml now carries resolved target tokens; mapping reference_resolution
    # carries the real tenant ids — so assemble produces canonical records.
    mapping = yaml.safe_load((fresh_acme / "ledger" / "mapping.yaml").read_text(encoding="utf-8"))
    rr = mapping["tables"][0].get("reference_resolution", [])
    itype_rr = next((r for r in rr if r["field"] == "interment_type_id"), None)
    assert itype_rr is not None
    assert set(itype_rr["resolved"].values()) == {11, 12}


def test_assemble_after_accept_all_produces_records(fresh_acme, project_sources):
    import assemble as assemble_mod

    sources = project_sources(fresh_acme)
    discover_mod.discover(fresh_acme, "v1", sources=sources)
    answer_mod.apply_answers(fresh_acme, "v1", accept_all=True)

    res = assemble_mod.assemble(fresh_acme, "v1", use_cache=False, scoped=False)
    # The synthetic register yields 4 properties / 3 customers / 3 interments.
    assert res.entity_counts.get("property") == 4
    assert res.entity_counts.get("customer") == 3
    assert res.entity_counts.get("interment") == 3

    # The interment_type id resolved (no unresolved-ref for it in the canonical records).
    interments = [
        json.loads(line)
        for line in (res.canonical_dir / "interment.ndjson").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    typed = [i for i in interments if i.get("interment_type_id") in (11, 12)]
    assert typed, "value-set ids should land on the canonical interment records"


def test_explicit_answers_file_resolves_open_questions(fresh_acme, project_sources):
    sources = project_sources(fresh_acme)
    result = discover_mod.discover(fresh_acme, "v1", sources=sources)
    open_q = [q for q in result.questions if q["status"] == "open"]
    assert open_q

    # Answer each open question with its proposed answer (or a stub for null proposals).
    answers = {q["id"]: (q["proposed_answer"] if q["proposed_answer"] is not None else "x")
               for q in open_q}
    res = answer_mod.apply_answers(fresh_acme, "v1", answers=answers)
    assert res.still_open == 0
    assert res.any_open is False
