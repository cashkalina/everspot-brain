"""Idempotency tests (SPEC §9.5).

A subject with an existing ledger answer is NOT re-asked — its status is carried, not
reset to open. Also proves a fully-settled mapping yields zero open questions. Synthetic.
"""

from __future__ import annotations

import json
from pathlib import Path

import discover as discover_mod


def _open_ids(result):
    return {q["id"] for q in result.questions if q["status"] == "open"}


def test_answered_subject_is_not_reasked(fresh_acme, project_sources):
    sources = project_sources(fresh_acme)
    first = discover_mod.discover(fresh_acme, "v1", sources=sources)
    # Pick an open question and record an answer in the ledger directly.
    open_q = next(q for q in first.questions if q["status"] == "open")
    qdir = fresh_acme / "ledger" / "questions"
    qdir.mkdir(parents=True, exist_ok=True)
    record = dict(open_q)
    record["status"] = "answered"
    record["answer"] = "operator-chosen-value"
    record["answered_by"] = "tester@everspot.io"
    (qdir / f"{open_q['id']}.json").write_text(json.dumps(record), encoding="utf-8")

    # Re-discover: that subject must carry its answered status, not be re-asked.
    second = discover_mod.discover(fresh_acme, "v1", sources=sources)
    carried = next(q for q in second.questions if q["id"] == open_q["id"])
    assert carried["status"] == "answered"
    assert carried["answer"] == "operator-chosen-value"
    assert open_q["id"] not in _open_ids(second)


def test_settled_mapping_yields_zero_open(fresh_acme, project_sources):
    """A fully-settled (non-draft) mapping/value_sets -> 0 open questions (§9.5)."""
    import answer as answer_mod

    sources = project_sources(fresh_acme)
    # Draft + accept-all everything that has a proposed default, then mark the mapping
    # settled (drop the draft flag) — re-discovery must surface no OPEN questions.
    discover_mod.discover(fresh_acme, "v1", sources=sources)
    answer_mod.apply_answers(fresh_acme, "v1", accept_all=True)

    # Flip the drafted mapping from draft -> settled.
    import yaml
    mp = fresh_acme / "ledger" / "mapping.yaml"
    m = yaml.safe_load(mp.read_text(encoding="utf-8"))
    m.pop("draft", None)
    m.pop("draft_version", None)
    mp.write_text(yaml.safe_dump(m, sort_keys=False), encoding="utf-8")
    vsp = fresh_acme / "ledger" / "value_sets.yaml"
    if vsp.exists():
        vs = yaml.safe_load(vsp.read_text(encoding="utf-8"))
        vs.pop("draft", None)
        vsp.write_text(yaml.safe_dump(vs, sort_keys=False), encoding="utf-8")

    result = discover_mod.discover(fresh_acme, "v1", sources=sources)
    assert result.open_count == 0, f"settled ledger must yield 0 open, got {_open_ids(result)}"
    assert result.any_open is False
