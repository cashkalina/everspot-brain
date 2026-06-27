"""Stage 6 + THE QUESTION ROUND — the single batched discovery pass (SPEC §9).

ONE pass that collapses the two old gates (mapping, then exceptions). It:

  1. ensures a profile + a (draft) mapping exist (auto-drafting via :mod:`map_draft`
     if the ledger has none);
  2. runs a DRY assemble + validate to surface PROJECTED exceptions (assemble
     needs-attention + blocking validation failures) — offline, no network, no LLM;
  3. aggregates EVERYTHING undecidable into ``runs/<v>/questions.json`` (an array of
     question records conforming to ``schemas/question.schema.json`` + SPEC §9.4) and
     renders ``runs/<v>/questions.md`` FROM that json.

Ask-policy (SPEC §9.1-§9.3, knowledge/core/ask-policy.md) is applied: a question is
emitted ONLY for what is BOTH undecidable AND materially-correctness-affecting (the
§9.2 list). Everything else gets a recorded confident default -> ``auto-resolved``
with the proposed value (LOGGED, never silent), surfaced as a low-friction accept-all
item.

Idempotency (SPEC §9.5, critical): every question ``id`` is a STABLE function of its
SUBJECT (column / value / entity), never run position. A question whose subject already
has a ledger record (an answered ``ledger/questions/<id>.json``, or a settled
mapping/value_set entry) is NEVER re-asked — its prior answer/status is carried and
re-applied. So ``discover`` against a settled ledger yields ZERO ``open`` questions.

This module is GENERAL — no client column names; it reads the project's profile,
draft, and ledger at run time.

Design references: SPEC §8 stage 6, §9 (the question round + ask-policy), §9.5
(idempotency + the orchestrator "any-open" gate).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import contract
import map_draft

VERSION = "1.0.0"

# Question kinds (SPEC §9.4). value_set | unmapped | missing_required | source_key |
# entity_merge | validation.
_KINDS = {"value_set", "unmapped", "missing_required", "source_key", "entity_merge", "validation"}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower()).strip("_") or "x"


def _qid(kind: str, *subject_parts: str) -> str:
    """Stable subject-derived id: ``q_<kind>__<subject-slug>`` (SPEC §9.5)."""
    subject = ".".join(_slug(p) for p in subject_parts if p)
    return f"q_{_slug(kind)}__{subject}"


# --------------------------------------------------------------------------- #
# Question record                                                              #
# --------------------------------------------------------------------------- #
@dataclass
class Question:
    id: str
    gate: str            # mapping | exception
    kind: str            # value_set | unmapped | missing_required | source_key | entity_merge | validation
    question: str
    proposed_answer: Any
    status: str = "open"
    options: list[Any] = field(default_factory=list)
    allow_custom: bool = True
    handoff: str = "internal"
    entity: Optional[str] = None
    field_: Optional[str] = None
    table: Optional[str] = None
    column: Optional[str] = None
    row_refs: list[str] = field(default_factory=list)
    confidence: Optional[float] = None
    answer: Any = None
    rationale: Optional[str] = None
    answered_by: Optional[str] = None
    first_seen_snapshot: Optional[str] = None

    @property
    def subject_key(self) -> tuple:
        """The identity of this question's SUBJECT (independent of which stage emitted
        it or its status). Two questions with the same ``id`` but different
        ``subject_key`` are a slug collision, not a legitimate same-subject dedupe."""
        return (self.kind, self.entity, self.field_, self.table, self.column)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "id": self.id,
            "gate": self.gate,
            "kind": self.kind,
            "question": self.question,
            "proposed_answer": self.proposed_answer,
            "options": self.options,
            "allow_custom": self.allow_custom,
            "handoff": self.handoff,
            "status": self.status,
        }
        for key, val in (
            ("entity", self.entity), ("field", self.field_), ("table", self.table),
            ("column", self.column), ("confidence", self.confidence),
            ("rationale", self.rationale), ("answered_by", self.answered_by),
            ("first_seen_snapshot", self.first_seen_snapshot),
        ):
            if val is not None:
                out[key] = val
        if self.row_refs:
            out["row_refs"] = self.row_refs
        if self.status in ("answered", "auto-resolved"):
            out["answer"] = self.answer
        return out


# --------------------------------------------------------------------------- #
# Ledger idempotency: load already-resolved questions by id                    #
# --------------------------------------------------------------------------- #
def _load_resolved_ledger_questions(ledger_dir: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    qdir = ledger_dir / "questions"
    if not qdir.is_dir():
        return out
    for f in qdir.glob("q_*.json"):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # pragma: no cover
            continue
        if rec.get("id"):
            out[rec["id"]] = rec
    return out


_STATUS_RANK = {"answered": 3, "auto-resolved": 2, "skipped": 1, "open": 0}


def _dedupe_by_id(questions: list[Question]) -> list[Question]:
    """Collapse questions sharing an ``id``, keeping the higher-rank status.

    Legitimate dedupe: the SAME subject is computed by more than one stage (drafts /
    assemble / validation) — identical ``subject_key`` — so collapsing to the
    higher-rank record is correct. A genuine COLLISION (same id, DIFFERENT
    ``subject_key``) would silently drop one subject — and in the worst case mask an
    OPEN gap behind an auto-resolved record. That is a stable-id bug (SPEC §9.5), so
    we raise loudly instead of dropping.
    """
    by_id: dict[str, Question] = {}
    for q in questions:
        existing = by_id.get(q.id)
        if existing is None:
            by_id[q.id] = q
            continue
        if existing.subject_key != q.subject_key:
            raise ValueError(
                f"question id collision: `{q.id}` maps to two distinct subjects "
                f"{existing.subject_key} vs {q.subject_key} "
                f"(statuses {existing.status!r} / {q.status!r}). Stable ids must be "
                f"1:1 with subjects (SPEC §9.5); add a discriminator to disambiguate."
            )
        if _STATUS_RANK[q.status] > _STATUS_RANK[existing.status]:
            by_id[q.id] = q
    return list(by_id.values())


def _carry_prior(q: Question, prior: dict[str, dict[str, Any]]) -> Question:
    """If this subject was already resolved in the ledger, carry its status/answer.

    This is the idempotency core (SPEC §9.5): a settled subject is never re-asked.
    """
    rec = prior.get(q.id)
    if not rec:
        return q
    q.status = rec.get("status", q.status)
    q.answer = rec.get("answer", q.answer)
    q.answered_by = rec.get("answered_by")
    q.rationale = rec.get("rationale")
    if rec.get("first_seen_snapshot"):
        q.first_seen_snapshot = rec["first_seen_snapshot"]
    return q


# --------------------------------------------------------------------------- #
# Build questions from the draft gaps (the mapping-side ambiguities)            #
# --------------------------------------------------------------------------- #
def _questions_from_drafts(drafts: list[map_draft.TableDraft]) -> list[Question]:
    out: list[Question] = []
    for td in drafts:
        # 1) value-set columns: each is EITHER fully auto-resolved or has unresolved codes.
        for vs in td.value_sets:
            qid = _qid("value_set", td.table, vs.column)
            n_total = len(vs.resolved) + len(vs.missing)
            proposed = {**{k: int(v) for k, v in vs.resolved.items()},
                        **{m: None for m in vs.missing}}
            if vs.missing:
                # MUST become a question (§9.2): a value did not resolve to a real id.
                # The proposed_answer surfaces WHICH codes resolved (and which are still
                # None) so the human can fill the gap — but it is NOT accept-all-able:
                # answer.apply_answers refuses to settle a value_set holding any None,
                # so accept-all leaves this question OPEN (those None cells would load
                # as null, violating §9.2).
                out.append(Question(
                    id=qid, gate="mapping", kind="value_set",
                    question=(f"Column `{vs.column}` (→ {vs.target_field}, {vs.list_option_type}): "
                              f"{len(vs.missing)} value(s) did not resolve to a tenant list_option id: "
                              f"{vs.missing}. Map each to a list_option id (or create it in Wave-0b)."),
                    proposed_answer=proposed,
                    options=sorted({*vs.resolved.values()}),
                    entity=td.primary_entity, field_=vs.target_field,
                    table=td.table, column=vs.column,
                    confidence=round(len(vs.resolved) / n_total, 3) if n_total else 0.0,
                    handoff="internal",
                ))
            else:
                # Confident default (§9.3): every value resolved cleanly -> auto-resolved.
                out.append(Question(
                    id=qid, gate="mapping", kind="value_set",
                    question=(f"Column `{vs.column}` (→ {vs.target_field}): all {n_total} value(s) "
                              f"resolved cleanly to {vs.list_option_type} list_options."),
                    proposed_answer={k: int(v) for k, v in vs.resolved.items()},
                    status="auto-resolved",
                    answer={k: int(v) for k, v in vs.resolved.items()},
                    answered_by="auto-resolved",
                    rationale="All codes resolved unambiguously to exactly one tenant list_option.",
                    entity=td.primary_entity, field_=vs.target_field,
                    table=td.table, column=vs.column, confidence=1.0,
                ))

        # 2) low-confidence column mappings flagged as gaps (kind=unmapped).
        for c in td.columns:
            if c.is_gap and c.gap_kind == "unmapped":
                qid = _qid("unmapped", td.table, c.source)
                out.append(Question(
                    id=qid, gate="mapping", kind="unmapped",
                    question=(f"Column `{c.source}`: best guess is `{c.target}` "
                              f"(confidence {c.confidence}). Confirm or correct the target."),
                    proposed_answer=c.target,
                    options=[c.target],
                    table=td.table, column=c.source, confidence=c.confidence,
                    handoff="internal",
                ))

        # 3) structural gaps (missing_required, source_key) computed by the drafter.
        for g in td.gaps:
            if g["kind"] == "missing_required":
                qid = _qid("missing_required", g["entity"], g["field"])
                has_default = "default" in g
                q = Question(
                    id=qid, gate="exception", kind="missing_required",
                    question=(f"Required field `{g['entity']}.{g['field']}` has no mapped source column. "
                              + (f"Use the obvious default `{g['default']}`?" if has_default
                                 else "Which column feeds it (or what default should be used)?")),
                    proposed_answer=(g.get("default")),
                    entity=g["entity"], field_=g["field"], table=td.table,
                    handoff="either",
                )
                if has_default:
                    # §9.3 confident default -> auto-resolved (recorded, never silent).
                    q.status = "auto-resolved"
                    q.answer = g["default"]
                    q.answered_by = "auto-resolved"
                    q.rationale = "Obvious Everspot default for a migrated historical record."
                    q.confidence = 1.0
                out.append(q)
            elif g["kind"] == "source_key":
                qid = _qid("source_key", td.table)
                cks = g.get("candidate_keys") or []
                out.append(Question(
                    id=qid, gate="mapping", kind="source_key",
                    question=(f"Table `{td.table}` has no confirmed stable source_key. "
                              f"Which column(s) uniquely identify a record? "
                              f"(If truly keyless, a deterministic hash is used and the fragility flagged.)"),
                    proposed_answer=(cks[0] if cks else None),
                    options=cks,
                    table=td.table, handoff="internal",
                ))

        # 4) entity routing (a borderline structural merge/split) — DEFERRED by the
        #    drafter, so confirm it. kind=entity_merge (the structural-routing question).
        if td.primary_inferred and td.primary_entity:
            qid = _qid("entity_merge", td.table)
            routing = td.primary_entity + (
                " + " + " + ".join(td.secondary_entities) if td.secondary_entities else ""
            )
            out.append(Question(
                id=qid, gate="mapping", kind="entity_merge",
                question=(f"Table `{td.table}` is inferred to be `{routing}` "
                          f"(one flat row split across these entities). Confirm the entity routing."),
                proposed_answer=routing,
                options=[routing],
                table=td.table, entity=td.primary_entity,
                handoff="internal",
            ))
    return out


# --------------------------------------------------------------------------- #
# Build questions from dry assemble + validate (the exception-side)            #
# --------------------------------------------------------------------------- #
# Assemble needs-attention kinds that are MATERIALLY-CORRECTNESS-AFFECTING and become
# OPEN questions (§9.2): a coded value that did not resolve, or a required FK that
# could not be resolved at all. A needs_attention item where assemble ALREADY APPLIED A
# DEFAULT (its detail says "defaulted to ...") is a recorded default (§9.3) -> surfaced
# as auto-resolved, never an open question. Routine low-confidence data-quality items
# (needs_llm, data_quality) are likewise defaults, not questions.
_NA_OPEN_KINDS = {"unmapped_value", "unresolved_ref"}


def _questions_from_assemble(report: dict[str, Any]) -> list[Question]:
    out: list[Question] = []
    seen: set[str] = set()
    for na in report.get("needs_attention", []):
        kind = na.get("kind")
        detail = na.get("detail", "")
        table = na.get("table", "")
        ctx = na.get("context", {})
        # Subject = (kind, table, the column/field/value the item is about) — stable,
        # so re-runs over the same data dedupe to one question, not one-per-row.
        subject = ctx.get("column") or ctx.get("field") or ctx.get("value") or detail
        defaulted = "default" in detail.lower()

        if kind in _NA_OPEN_KINDS and not defaulted:
            qkind = "value_set" if kind == "unmapped_value" else "validation"
            qid = _qid(qkind, table, str(subject))
            if qid in seen:
                continue
            seen.add(qid)
            out.append(Question(
                id=qid, gate="exception", kind=qkind,
                question=f"Assemble could not settle {kind} in `{table}`: {detail}",
                proposed_answer=None,
                table=table, row_refs=[na.get("source_id")] if na.get("source_id") else [],
                handoff="either",
            ))
        elif defaulted:
            # A recorded default (§9.3): surface once as auto-resolved, never asked.
            qid = _qid("validation", table, str(subject))
            if qid in seen:
                continue
            seen.add(qid)
            out.append(Question(
                id=qid, gate="exception", kind="validation",
                question=f"Data-quality default applied in `{table}`: {detail}",
                proposed_answer="(default applied)",
                status="auto-resolved", answer="(default applied)",
                answered_by="auto-resolved",
                rationale="Assemble applied a deterministic default; recorded for review.",
                table=table, handoff="either",
            ))
    return out


def _questions_from_validation(failures: list[dict[str, Any]]) -> list[Question]:
    out: list[Question] = []
    seen: set[str] = set()
    for f in failures:
        if not f.get("blocking"):
            continue
        entity = f.get("entity", "")
        fld = f.get("field") or ""
        qid = _qid("validation", entity, fld, f.get("kind", ""))
        if qid in seen:
            continue
        seen.add(qid)
        out.append(Question(
            id=qid, gate="exception", kind="validation",
            question=(f"Blocking validation failure on `{entity}`"
                      + (f".{fld}" if fld else "")
                      + f" ({f.get('kind')}): {f.get('detail','')}. How should this be resolved?"),
            proposed_answer=None,
            entity=entity, field_=(fld or None),
            handoff="either",
        ))
    return out


# --------------------------------------------------------------------------- #
# Dry assemble + validate (offline)                                            #
# --------------------------------------------------------------------------- #
def _dry_assemble_and_validate(root: Path, snapshot: str) -> tuple[dict, list[dict]]:
    """Run assemble (no cache, full) + validate offline; return (assemble_report, failures).

    Best-effort: a hard assemble/validate error (e.g. a half-formed draft) is captured
    as a single validation-style failure rather than aborting discovery.
    """
    assemble_report: dict[str, Any] = {}
    failures: list[dict[str, Any]] = []
    try:
        import assemble as assemble_mod
        result = assemble_mod.assemble(root, snapshot, use_cache=False, scoped=False)
        report_path = result.canonical_dir / "assemble_report.json"
        if report_path.exists():
            assemble_report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive: surfaces as a question
        failures.append({
            "entity": "(assemble)", "field": None, "kind": "validation",
            "detail": f"dry assemble failed: {exc}", "blocking": True,
        })
        return assemble_report, failures

    try:
        import validate as validate_mod
        vresult = validate_mod.validate_run(root, snapshot)
        failures = [f.to_dict() for f in vresult.blocking_failures]
    except Exception as exc:  # pragma: no cover
        failures.append({
            "entity": "(validate)", "field": None, "kind": "validation",
            "detail": f"dry validate failed: {exc}", "blocking": True,
        })
    return assemble_report, failures


# --------------------------------------------------------------------------- #
# Settlement: subjects already decided by the ON-DISK settled ledger (§9.5)     #
# --------------------------------------------------------------------------- #
def _settled_resolutions(root: Path, sources: Optional[list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Subjects already settled in the on-disk mapping/value_sets/project (§9.5).

    Returns ``{question_id: {answer, rationale}}`` for subjects a SETTLED ledger has
    already decided — so a re-run downgrades those questions to ``auto-resolved`` with
    the settled value instead of re-asking. This is the core of idempotency against a
    human-settled ledger: running ``discover`` over bells-chapel's settled ledger yields
    ZERO open questions even though it has no ``ledger/questions/`` files.
    """
    import yaml

    out: dict[str, dict[str, Any]] = {}
    ledger_dir = root / "ledger"
    mapping_path = ledger_dir / "mapping.yaml"
    if not mapping_path.exists():
        return out
    mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    if mapping.get("draft"):
        return out  # a draft ledger is not "settled" — its gaps are still live

    value_sets_path = ledger_dir / "value_sets.yaml"
    value_sets = yaml.safe_load(value_sets_path.read_text(encoding="utf-8")) if value_sets_path.exists() else {}
    vs_index = {(vs.get("table"), vs.get("column")): vs for vs in (value_sets.get("value_sets") or [])}

    key_status = {s.get("table"): s for s in (sources or [])}

    for block in mapping.get("tables", []):
        table = block.get("source_table")
        primary = block.get("target_entity", "")
        secondaries = block.get("secondary_entities") or []
        mapped_fields: set[tuple[str, str]] = set()

        # entity routing is settled by the mapping's own declaration.
        if primary:
            routing = primary + (" + " + " + ".join(secondaries) if secondaries else "")
            out[_qid("entity_merge", table)] = {
                "answer": routing,
                "rationale": "Entity routing declared in the settled mapping.",
            }

        # value_set columns: a settled mapping/value_sets fully resolves them.
        rr_by_field = {rr.get("field"): rr for rr in (block.get("reference_resolution") or [])}
        for col in block.get("columns", []):
            if col.get("action") == "value_map":
                target = col.get("target", "")
                fname = target.split(".")[-1] if target else None
                rr = rr_by_field.get(fname, {})
                missing = rr.get("missing") or []
                vs = vs_index.get((table, col.get("source")))
                if not missing and vs is not None:
                    resolved = rr.get("resolved") or {}
                    out[_qid("value_set", table, col.get("source"))] = {
                        "answer": resolved,
                        "rationale": "All values resolved by the settled mapping/value_sets.",
                    }
            # Any column the settled mapping ADDRESSES (mapped, value-mapped, external_id,
            # or explicitly unmapped) is a decided subject — its `unmapped` question is
            # never re-asked (§9.5). This covers settled attribute targets + ignored cols.
            out[_qid("unmapped", table, col.get("source"))] = {
                "answer": col.get("target") if col.get("action") != "unmapped" else "(ignored)",
                "rationale": f"Column disposition settled in the mapping (action={col.get('action')}).",
            }
            tgt = col.get("target")
            if tgt and "." in tgt and col.get("action") in ("map", "value_map", "external_id"):
                ent, fld = tgt.split(".")[0], tgt.split(".")[1]
                mapped_fields.add((ent, fld))

        # required fields: settled if the mapping maps a source column to them.
        for entity in [e for e in (primary, *secondaries) if e]:
            for fname, spec in contract.entity_fields(entity).items():
                if not spec.get("required_on_insert"):
                    continue
                if fname == "external_id" or spec.get("type") in ("ref", "external_id"):
                    continue
                if (entity, fname) in mapped_fields or (entity, fname) in map_draft._DEFAULTABLE_REQUIRED:
                    default = map_draft._DEFAULTABLE_REQUIRED.get((entity, fname), "(mapped from source)")
                    out[_qid("missing_required", entity, fname)] = {
                        "answer": default,
                        "rationale": "Required field satisfied by the settled mapping.",
                    }

        # source_key: settled if the project declares a confirmed key.
        src = key_status.get(table, {})
        if src.get("source_key") and src.get("key_status", "confirmed") != "deferred":
            out[_qid("source_key", table)] = {
                "answer": src["source_key"],
                "rationale": "source_key confirmed in the project source declaration.",
            }
    return out


# --------------------------------------------------------------------------- #
# Rendering questions.md FROM questions.json (JSON-first, SPEC §9.4)            #
# --------------------------------------------------------------------------- #
def render_questions_md(questions: list[dict[str, Any]], snapshot: str) -> str:
    open_q = [q for q in questions if q["status"] == "open"]
    auto = [q for q in questions if q["status"] == "auto-resolved"]
    answered = [q for q in questions if q["status"] == "answered"]
    skipped = [q for q in questions if q["status"] == "skipped"]

    lines = [f"# Discovery — the single question round ({snapshot})", ""]
    lines.append(f"- **Open (must answer):** {len(open_q)}")
    lines.append(f"- **Auto-resolved (accept-all candidates):** {len(auto)}")
    lines.append(f"- **Answered (carried from ledger):** {len(answered)}")
    lines.append(f"- **Skipped:** {len(skipped)}")
    lines.append("")
    if open_q:
        lines.append("> The orchestrator MUST NOT proceed while any question is `open` (SPEC §9.5).")
    else:
        lines.append("> ✅ No open questions — safe to proceed.")
    lines.append("")

    if open_q:
        lines.append("## Open questions")
        lines.append("")
        for q in open_q:
            lines.append(f"### `{q['id']}` — {q['kind']}")
            lines.append(f"- **Q:** {q['question']}")
            lines.append(f"- **Proposed:** `{json.dumps(q['proposed_answer'])}`")
            if q.get("options"):
                lines.append(f"- **Options:** {q['options']}")
            lines.append(f"- **Handoff:** {q.get('handoff','internal')}  ·  allow_custom: {q.get('allow_custom', True)}")
            lines.append("")

    if auto:
        lines.append("## Auto-resolved (recorded defaults — review or accept-all)")
        lines.append("")
        for q in auto:
            lines.append(f"- `{q['id']}` ({q['kind']}): {q['question']} → `{json.dumps(q.get('answer'))}`")
        lines.append("")

    if answered:
        lines.append("## Answered (carried from prior ledger — not re-asked)")
        lines.append("")
        for q in answered:
            lines.append(f"- `{q['id']}` ({q['kind']}): → `{json.dumps(q.get('answer'))}`")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class DiscoverResult:
    questions: list[dict[str, Any]]
    questions_json_path: Path
    questions_md_path: Path
    open_count: int
    auto_resolved_count: int
    answered_count: int
    skipped_count: int

    @property
    def any_open(self) -> bool:
        return self.open_count > 0


def discover(
    project_root: str | Path,
    snapshot: str,
    *,
    sources: Optional[list[dict[str, Any]]] = None,
    draft_if_missing: bool = True,
) -> DiscoverResult:
    """Run the single batched discovery round for a snapshot.

    Ensures a (draft) mapping exists, runs a dry assemble + validate, aggregates all
    undecidable subjects into question records (idempotent vs the ledger), and writes
    ``runs/<v>/questions.json`` + ``questions.md``.
    """
    import yaml

    root = Path(project_root)
    ledger_dir = root / "ledger"
    mapping_path = ledger_dir / "mapping.yaml"

    # 1) ensure a profile exists (auto-profile if absent).
    profile_summary = root / "snapshots" / snapshot / "profile" / "summary.json"
    if not profile_summary.exists():
        import profile as profile_mod
        profile_mod.profile_snapshot(root / "snapshots" / snapshot)

    # 2) ensure a mapping exists. When the ledger is SETTLED we never write to it (not
    #    even a sidecar) — we compute the drafts in-memory purely to derive the gap set,
    #    and the settlement resolver (step 5) closes any subject the settled ledger
    #    already decided. When there is no usable mapping, auto-draft one to disk so the
    #    dry assemble has something to run against.
    if mapping_path.exists():
        existing = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
        settled = not existing.get("draft")
    else:
        settled = False

    if settled or (mapping_path.exists() and not draft_if_missing):
        drafts = map_draft.compute_drafts(root, snapshot, sources=sources)
    elif draft_if_missing:
        result = map_draft.map_draft(root, snapshot, sources=sources)
        drafts = result.drafts
    elif mapping_path.exists():
        drafts = map_draft.compute_drafts(root, snapshot, sources=sources)
    else:
        raise FileNotFoundError(
            f"no mapping at {mapping_path} and draft_if_missing=False."
        )

    # 3) dry assemble + validate (offline) — only if a usable on-disk mapping exists.
    assemble_report: dict[str, Any] = {}
    failures: list[dict[str, Any]] = []
    if mapping_path.exists():
        assemble_report, failures = _dry_assemble_and_validate(root, snapshot)

    # 4) aggregate every undecidable subject into question records.
    questions: list[Question] = []
    questions.extend(_questions_from_drafts(drafts))
    questions.extend(_questions_from_assemble(assemble_report))
    questions.extend(_questions_from_validation(failures))

    # 5) idempotency (SPEC §9.5): a subject already decided by the SETTLED on-disk
    #    ledger is never re-asked — downgrade it to auto-resolved with the settled value.
    settled_res = _settled_resolutions(root, sources)
    for q in questions:
        if q.status == "open" and q.id in settled_res:
            r = settled_res[q.id]
            q.status = "auto-resolved"
            q.answer = r["answer"]
            q.answered_by = "auto-resolved"
            q.rationale = r["rationale"]

    # Then carry any explicitly-recorded prior ledger answers; dedupe by id (a genuine
    # id collision between two distinct subjects raises rather than dropping the OPEN
    # one — see _dedupe_by_id).
    prior = _load_resolved_ledger_questions(ledger_dir)
    for q in questions:
        _carry_prior(q, prior)
        if q.first_seen_snapshot is None:
            q.first_seen_snapshot = snapshot
    ordered = sorted(
        _dedupe_by_id(questions),
        key=lambda q: (_STATUS_RANK[q.status], q.kind, q.id),
    )

    records = [q.to_dict() for q in ordered]

    run_dir = root / "runs" / snapshot
    run_dir.mkdir(parents=True, exist_ok=True)
    qjson = run_dir / "questions.json"
    qmd = run_dir / "questions.md"
    qjson.write_text(json.dumps(records, indent=2), encoding="utf-8")
    qmd.write_text(render_questions_md(records, snapshot), encoding="utf-8")

    counts = {"open": 0, "auto-resolved": 0, "answered": 0, "skipped": 0}
    for r in records:
        counts[r["status"]] += 1

    return DiscoverResult(
        questions=records,
        questions_json_path=qjson,
        questions_md_path=qmd,
        open_count=counts["open"],
        auto_resolved_count=counts["auto-resolved"],
        answered_count=counts["answered"],
        skipped_count=counts["skipped"],
    )
