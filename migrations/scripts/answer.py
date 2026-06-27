"""THE QUESTION ROUND — answer application (SPEC §9.5).

Reads an ``answers.json`` (``{id: chosen_answer}``, or the special ``"accept-all"``
which takes every question's ``proposed_answer``), then:

  1. persists each resolved question to ``ledger/questions/<id>.json`` (status
     answered / auto-resolved / skipped + a rationale) — the durable, diffable audit
     trail that makes v2 cheap (a settled subject is never re-asked);
  2. APPLIES the answers back into ``ledger/mapping.yaml`` / ``value_sets.yaml`` so the
     next ``assemble`` picks them up. value_set answers write resolved ids into the
     mapping's ``reference_resolution`` + the value_sets ``values``; source_key answers
     update the project source declaration; unmapped/missing_required/entity_merge
     answers are recorded (and surfaced for the AI/manual mapping edit when free-form).

The orchestrator gate (SPEC §9.5): ``answer`` (and ``discover``) expose an ``any_open``
signal so the orchestrator refuses to proceed while any question is still ``open``.

This module is GENERAL — it operates on the project's own question records + ledger.

Design references: SPEC §9.4 (record shape), §9.5 (persistence + idempotency + gate).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

VERSION = "1.0.0"

ACCEPT_ALL = "accept-all"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


BLOCKING_KINDS = frozenset({"missing_required", "validation"})


@dataclass(slots=True)
class AnswerResult:
    answered: int = 0
    auto_accepted: int = 0
    skipped: int = 0
    skipped_blocking: int = 0
    still_open: int = 0
    applied_value_sets: int = 0
    applied_source_keys: int = 0
    recorded_other: int = 0
    persisted: list[str] = field(default_factory=list)

    @property
    def any_open(self) -> bool:
        return self.still_open > 0

    @property
    def gate_clear(self) -> bool:
        """The orchestrator may proceed only when nothing is open AND no BLOCKING
        question was skipped (a skipped blocking question is a known, un-fixed gap)."""
        return not self.any_open and self.skipped_blocking == 0


# --------------------------------------------------------------------------- #
# Persist a resolved question to the ledger                                    #
# --------------------------------------------------------------------------- #
def _persist_question(ledger_dir: Path, record: dict[str, Any]) -> Path:
    qdir = ledger_dir / "questions"
    qdir.mkdir(parents=True, exist_ok=True)
    path = qdir / f"{record['id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Apply answers back into the ledger artifacts                                 #
# --------------------------------------------------------------------------- #
def _slug(text: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower()).strip("_") or "x"


_NOT_A_SKIP = object()


def _skip_rationale(chosen: Any) -> Any:
    """Classify a chosen answer as a skip directive and extract its rationale.

    Returns ``_NOT_A_SKIP`` when ``chosen`` is not a skip. For a skip, returns the
    rationale string (possibly empty — an empty/missing rationale means the skip must
    be REJECTED). Accepted skip forms:

      - ``"skip"`` (bare string) -> rationale "" (rejected: no reason given).
      - ``{"action": "skip", "rationale": "..."}`` -> the rationale.
      - ``{"skip": "..."}`` -> the rationale value.
    """
    if chosen == "skip":
        return ""
    if isinstance(chosen, dict):
        if chosen.get("action") == "skip":
            return str(chosen.get("rationale") or "").strip()
        if "skip" in chosen and len(chosen) == 1:
            return str(chosen.get("skip") or "").strip()
    return _NOT_A_SKIP


def _apply_value_set_answer(
    mapping: dict[str, Any], value_sets: dict[str, Any], q: dict[str, Any], answer: Any
) -> bool:
    """Write a value_set answer (``{source_value: list_option_id}``) into both files.

    The value_map chain is ``source_value --(value_sets.target_value token)-->
    --(reference_resolution.resolved[token])--> tenant id``. So we key the mapping's
    ``reference_resolution.resolved`` by the value_sets ``target_value`` TOKEN (the slug),
    not the raw source value — otherwise assemble can't resolve the token to an id.
    """
    if not isinstance(answer, dict):
        return False
    table = q.get("table")
    column = q.get("column")
    field_name = q.get("field")
    applied = False

    # 1) value_sets.yaml: ensure each source_value has a stable target token; collect
    #    the source_value -> token map (so reference_resolution can be token-keyed).
    sv_to_token: dict[str, str] = {}
    for vs in value_sets.get("value_sets", []):
        if vs.get("table") == table and vs.get("column") == column:
            existing = {v["source_value"]: v for v in vs.get("values", [])}
            for sv in answer:
                token = (existing.get(sv, {}).get("target_value")) or _slug(sv)
                sv_to_token[sv] = token
                if sv in existing:
                    existing[sv]["target_value"] = token
                else:
                    vs.setdefault("values", []).append({"source_value": sv, "target_value": token})
            applied = True
    if not sv_to_token:
        sv_to_token = {sv: _slug(sv) for sv in answer}

    # 2) mapping reference_resolution: token -> id; clear/track the unresolved set.
    for block in mapping.get("tables", []):
        for rr in block.get("reference_resolution", []):
            if rr.get("field") == field_name:
                resolved = dict(rr.get("resolved") or {})
                missing: list[str] = []
                for sv, _id in answer.items():
                    token = sv_to_token.get(sv, _slug(sv))
                    if _id is not None:
                        resolved[token] = _id
                    else:
                        missing.append(token)
                rr["resolved"] = resolved
                rr["missing"] = missing
                applied = True
    return applied


def _apply_source_key_answer(project: dict[str, Any], q: dict[str, Any], answer: Any) -> bool:
    """Write a source_key answer (column list) into the project source declaration."""
    table = q.get("table")
    if not table or not answer:
        return False
    cols = answer if isinstance(answer, list) else [answer]
    for s in project.get("sources", []):
        if s.get("table") == table:
            s["source_key"] = cols
            s["key_status"] = "confirmed"
            return True
    return False


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #
def apply_answers(
    project_root: str | Path,
    snapshot: str,
    *,
    answers: Optional[dict[str, Any]] = None,
    accept_all: bool = False,
    answered_by: str = "operator",
) -> AnswerResult:
    """Apply answers to a discovered question set; persist + write back to the ledger.

    Args:
        answers: ``{question_id: chosen_answer}``. An id mapped to the string
            ``"skip"`` is recorded as ``skipped``. Ignored when ``accept_all``.
        accept_all: take every question's ``proposed_answer`` as its answer.
        answered_by: recorded on each answered question.
    """
    import yaml

    root = Path(project_root)
    ledger_dir = root / "ledger"
    run_dir = root / "runs" / snapshot
    questions_path = run_dir / "questions.json"
    if not questions_path.exists():
        raise FileNotFoundError(f"no questions.json at {questions_path} — run `migrate discover` first.")

    records: list[dict[str, Any]] = _read_json(questions_path, [])
    answers = answers or {}

    mapping_path = ledger_dir / "mapping.yaml"
    value_sets_path = ledger_dir / "value_sets.yaml"
    project_path = root / "project.yaml"
    mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) if mapping_path.exists() else {"tables": []}
    value_sets = yaml.safe_load(value_sets_path.read_text(encoding="utf-8")) if value_sets_path.exists() else {"value_sets": []}
    project = yaml.safe_load(project_path.read_text(encoding="utf-8")) if project_path.exists() else {}

    res = AnswerResult()

    for q in records:
        qid = q["id"]
        status = q.get("status", "open")

        # Already auto-resolved/answered (carried) -> persist as-is (idempotent).
        if status in ("auto-resolved", "answered"):
            q.setdefault("answer", q.get("proposed_answer"))
            if status == "auto-resolved":
                res.auto_accepted += 1
            else:
                res.answered += 1
            res.persisted.append(str(_persist_question(ledger_dir, q)))
            # auto-resolved value_sets still need applying so assemble picks them up.
            if q.get("kind") == "value_set" and _apply_value_set_answer(mapping, value_sets, q, q["answer"]):
                res.applied_value_sets += 1
            continue

        # Open -> resolve from answers / accept-all.
        chosen: Any
        if accept_all:
            chosen = q.get("proposed_answer")
        elif qid in answers:
            chosen = answers[qid]
        else:
            res.still_open += 1
            continue

        skip_rationale = _skip_rationale(chosen)
        if skip_rationale is not _NOT_A_SKIP:
            # A skip MUST carry an explicit rationale (§9.5 audit): a bare "skip" with
            # no reason is rejected and the question stays OPEN. A skipped BLOCKING
            # question is surfaced so the gate refuses to proceed on a known gap.
            if not skip_rationale:
                res.still_open += 1
                continue
            q["status"] = "skipped"
            q["rationale"] = skip_rationale
            q["answered_by"] = answered_by
            q["answered_at"] = _now()
            res.skipped += 1
            if q.get("kind") in BLOCKING_KINDS:
                res.skipped_blocking += 1
            res.persisted.append(str(_persist_question(ledger_dir, q)))
            continue

        # Accept-all of a proposed_answer that is null/empty cannot resolve -> stays open.
        if chosen is None:
            res.still_open += 1
            continue

        # A value_set answer with ANY unresolved (None) value cannot be settled (§9.2):
        # accepting it would write None tokens into reference_resolution and load null
        # cells. Keep the question OPEN until every source value maps to a real id.
        if q.get("kind") == "value_set" and isinstance(chosen, dict) and any(
            v is None for v in chosen.values()
        ):
            res.still_open += 1
            continue

        q["status"] = "answered"
        q["answer"] = chosen
        q["answered_by"] = (ACCEPT_ALL if accept_all else answered_by)
        q["answered_at"] = _now()
        res.answered += 1
        res.persisted.append(str(_persist_question(ledger_dir, q)))

        kind = q.get("kind")
        if kind == "value_set":
            if _apply_value_set_answer(mapping, value_sets, q, chosen):
                res.applied_value_sets += 1
        elif kind == "source_key":
            if _apply_source_key_answer(project, q, chosen):
                res.applied_source_keys += 1
        else:
            res.recorded_other += 1

    # Write back the mutated ledger artifacts.
    if mapping_path.exists() or mapping.get("tables"):
        mapping_path.write_text(yaml.safe_dump(mapping, sort_keys=False), encoding="utf-8")
    if value_sets_path.exists() or value_sets.get("value_sets"):
        value_sets_path.write_text(yaml.safe_dump(value_sets, sort_keys=False), encoding="utf-8")
    if project_path.exists():
        project_path.write_text(yaml.safe_dump(project, sort_keys=False), encoding="utf-8")

    # Re-write questions.json with updated statuses (so a re-discover carries them).
    questions_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return res
