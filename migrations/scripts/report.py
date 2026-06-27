"""Stage 12 — REPORT. Assemble the single consolidated ``runs/<v>/REPORT.md`` (SPEC §15.2).

Deterministic and read-only: it **reads numbers from the run artifacts** and restates
them — it never re-computes or invents a count. Everything it prints is sourced from a
file produced by an earlier stage, so the report is a faithful one-screen mirror of the
run (the §15.2 design intent: "is this correct and what do I need to look at?").

Inputs (all optional except the canonical dir — a missing input degrades to a clearly
labelled "not yet …" section, never a crash):

    snapshots/<v>/manifest.json                 source row totals per table
    runs/<v>/canonical/*.ndjson                 canonical record counts per entity
    runs/<v>/validation/validation_summary.json count conservation + PASS/FAIL gate
    runs/<v>/load/results.jsonl  OR             per-record load results (preferred)
    runs/<v>/canonical/load_report.json         orion_load summary (fallback)
    runs/<v>/questions.json                     the answered questionnaire
    runs/<v>/canonical/assemble_report.json     data-quality flags (needs_attention)
    runs/<v>/reconciliation.json                post-load (--live) reconcile, if run

Side effect (SPEC §15.1): ensures ``runs/<v>/needs_attention.json`` exists at the run
root — surfaced/copied from assemble_report.json's ``needs_attention``, grouped by kind.
"""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional

import run_log
import run_state

VERSION = "1.0.0"

# Wave order (SPEC §8) — drives the per-entity table ordering so the report reads top-down.
_ENTITY_ORDER = ("cemetery", "property_group", "property", "customer", "interment")


# --------------------------------------------------------------------------- #
# Small read helpers (every one tolerates a missing file)                      #
# --------------------------------------------------------------------------- #
def _read_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def _read_ndjson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def _entity_sort_key(entity: str) -> tuple[int, str]:
    try:
        return (_ENTITY_ORDER.index(entity), entity)
    except ValueError:
        return (len(_ENTITY_ORDER), entity)


# --------------------------------------------------------------------------- #
# Section gatherers                                                            #
# --------------------------------------------------------------------------- #
def _canonical_counts(canonical_dir: Path) -> "OrderedDict[str, int]":
    counts: dict[str, int] = {}
    if canonical_dir.is_dir():
        for path in canonical_dir.glob("*.ndjson"):
            counts[path.stem] = sum(1 for l in path.read_text(encoding="utf-8").splitlines() if l.strip())
    return OrderedDict(sorted(counts.items(), key=lambda kv: _entity_sort_key(kv[0])))


def _conservation_index(validation: Optional[dict]) -> dict[str, dict]:
    """entity → {source_rows, canonical_records, dropped, conserved} from validation_summary."""
    out: dict[str, dict] = {}
    if validation:
        for row in validation.get("count_conservation", []):
            out[row["entity"]] = row
    return out


def _load_results(run_dir: Path, canonical_dir: Path) -> tuple[Optional[dict], str]:
    """Return (per-entity {created,updated,skipped,failed}, source-label) or (None, '').

    Preferred source is ``load/results.jsonl`` (one JSON object per record, SPEC §8).
    Falls back to the ``orion_load`` summary ``canonical/load_report.json``.
    """
    results_path = run_dir / "load" / "results.jsonl"
    rows = _read_ndjson(results_path)
    if rows:
        agg: dict[str, dict[str, int]] = {}
        for r in rows:
            entity = r.get("entity", "?")
            action = (r.get("action") or r.get("status") or "created").lower()
            bucket = agg.setdefault(entity, {"created": 0, "updated": 0, "skipped": 0, "failed": 0})
            if action in bucket:
                bucket[action] += 1
            elif action in ("create", "insert"):
                bucket["created"] += 1
            elif action in ("update", "patch"):
                bucket["updated"] += 1
            elif action in ("skip", "unchanged"):
                bucket["skipped"] += 1
            elif action in ("fail", "error"):
                bucket["failed"] += 1
            else:
                # An UNRECOGNIZED load action must not vanish (L7): fold it into failed so
                # the conserved/loaded verdict can never hide a record we can't classify.
                bucket["failed"] += 1
        return agg, "load/results.jsonl"

    report = _read_json(canonical_dir / "load_report.json")
    if report and isinstance(report.get("created"), dict):
        agg = {}
        entities = set()
        for key in ("created", "updated", "skipped", "failed"):
            entities |= set(report.get(key, {}).keys())
        for entity in entities:
            agg[entity] = {
                "created": int(report.get("created", {}).get(entity, 0)),
                "updated": int(report.get("updated", {}).get(entity, 0)),
                "skipped": int(report.get("skipped", {}).get(entity, 0)),
                "failed": int(report.get("failed", {}).get(entity, 0)),
            }
        return agg, "canonical/load_report.json"

    return None, ""


def _question_summary(questions: Optional[list]) -> dict:
    by_status: dict[str, int] = {"open": 0, "answered": 0, "auto-resolved": 0, "skipped": 0}
    items: list[dict] = []
    for q in questions or []:
        status = q.get("status", "open")
        by_status[status] = by_status.get(status, 0) + 1
        items.append(
            {
                "id": q.get("id", "?"),
                "kind": q.get("kind", "?"),
                "status": status,
                "question": q.get("question", ""),
                "answer": q.get("answer", q.get("proposed_answer")),
            }
        )
    return {"by_status": by_status, "items": items, "total": len(items)}


def group_needs_attention(items: list[dict]) -> "OrderedDict[str, list]":
    """Group needs_attention records by ``kind`` (SPEC §15.1)."""
    grouped: dict[str, list] = {}
    for item in items or []:
        grouped.setdefault(item.get("kind", "other"), []).append(item)
    return OrderedDict(sorted(grouped.items()))


def ensure_needs_attention(run_dir: Path, assemble_report: Optional[dict]) -> Path:
    """Surface assemble's needs_attention to ``runs/<v>/needs_attention.json`` (§15.1).

    Always writes the file (even if empty) so the §15.1 review surface is guaranteed to
    exist at the run root. The on-disk shape is grouped by kind.
    """
    items = (assemble_report or {}).get("needs_attention", []) or []
    grouped = group_needs_attention(items)
    payload = {
        "total": sum(len(v) for v in grouped.values()),
        "by_kind": {k: len(v) for k, v in grouped.items()},
        "items_by_kind": grouped,
    }
    out = run_dir / "needs_attention.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# Rendering                                                                    #
# --------------------------------------------------------------------------- #
def _fmt_answer(answer: Any) -> str:
    if isinstance(answer, (dict, list)):
        s = json.dumps(answer, default=str)
        return (s[:80] + "…") if len(s) > 80 else s
    return str(answer)


def render_report(
    *,
    snapshot: str,
    manifest: Optional[dict],
    canonical_counts: "OrderedDict[str, int]",
    conservation: dict[str, dict],
    load_agg: Optional[dict],
    load_source: str,
    questions: dict,
    needs_attention_grouped: "OrderedDict[str, list]",
    validation: Optional[dict],
    reconcile: Optional[dict],
) -> str:
    lines: list[str] = [f"# Migration Report — {snapshot}", ""]

    # Headline verdict line ----------------------------------------------------
    gate = (validation or {}).get("gate", "UNKNOWN")
    gate_mark = {"PASS": "✅", "FAIL": "❌"}.get(gate, "—")
    loaded_state = "loaded" if load_agg else "not yet loaded"
    lines += [
        f"**Validation:** {gate_mark} {gate}  ·  "
        f"**Open questions:** {questions['by_status'].get('open', 0)}  ·  "
        f"**Load:** {loaded_state}",
        "",
    ]

    # 1) Count conservation ----------------------------------------------------
    lines += ["## Count conservation", ""]
    if manifest:
        total_src = manifest.get("total_rows")
        if total_src is not None:
            lines.append(f"Source: **{total_src}** raw row(s) across "
                         f"{manifest.get('total_tables', '?')} table(s).")
            lines.append("")

    # Headline disposition verdict — the source-of-truth conservation story (manifest's
    # true row total reconciled against the per-source-row disposition ledger). An
    # unexplained drop is real data loss (BLOCKING upstream in validate); legitimate
    # fan-in/dedup/out-of-scope is informational.
    cons_summary = (validation or {}).get("conservation_summary") or {}
    if cons_summary:
        conserved_ok = cons_summary.get("conserved")
        head = "✅ CONSERVED" if conserved_ok else "❌ UNEXPLAINED DROPS"
        lines.append(
            f"**{head}** — {cons_summary.get('accounted', '?')} of "
            f"{cons_summary.get('manifest_total_rows', '?')} source row(s) accounted "
            f"({cons_summary.get('produced', 0)} produced · "
            f"{cons_summary.get('deduped', 0)} deduped · "
            f"{cons_summary.get('skipped', 0)} out-of-scope · "
            f"{cons_summary.get('errored', 0)} errored · "
            f"**{cons_summary.get('unexplained_dropped', 0)} unexplained dropped**)."
        )
        lines.append("")

    lines += ["| Entity | Source rows | Canonical | Loaded | Dropped | Conserved |",
              "|---|---:|---:|---:|---:|:--:|"]
    entities = sorted(
        set(canonical_counts) | set(conservation),
        key=_entity_sort_key,
    )
    for entity in entities:
        canon = canonical_counts.get(entity, conservation.get(entity, {}).get("canonical_records", 0))
        cons_row = conservation.get(entity, {})
        src = cons_row.get("source_rows", "—")
        dropped = cons_row.get("dropped", 0)
        conserved = cons_row.get("conserved")
        if load_agg and entity in load_agg:
            b = load_agg[entity]
            # Loaded = records confirmed present in the tenant. FAILED/unknown actions are
            # already folded into ``failed`` (L7), so a failed record is NOT counted as
            # loaded — and a load shortfall (loaded < canonical, or any failure) flips the
            # conserved mark so it can never hide.
            loaded = b["created"] + b["updated"] + b["skipped"]
            if conserved is not False and (b["failed"] > 0 or loaded < canon):
                conserved = False
        else:
            loaded = "—"
        mark = {True: "✅", False: "❌"}.get(conserved, "—")
        lines.append(f"| {entity} | {src} | {canon} | {loaded} | {dropped} | {mark} |")
    lines.append("")

    # 2) What loaded per entity ------------------------------------------------
    lines += ["## What loaded per entity", ""]
    if load_agg:
        lines.append(f"_Source: `{load_source}`._")
        lines.append("")
        lines += ["| Entity | Created | Updated | Skipped | Failed |",
                  "|---|---:|---:|---:|---:|"]
        for entity in sorted(load_agg, key=_entity_sort_key):
            b = load_agg[entity]
            lines.append(f"| {entity} | {b['created']} | {b['updated']} | {b['skipped']} | {b['failed']} |")
        lines.append("")
    else:
        lines += ["_Not yet loaded — run `migrate load --live` (or `migrate emit` for the Excel alternate)._", ""]

    # 3) The questionnaire answered -------------------------------------------
    bs = questions["by_status"]
    lines += ["## The questionnaire answered", ""]
    lines.append(
        f"**{questions['total']}** question(s): "
        f"{bs.get('open', 0)} open · {bs.get('auto-resolved', 0)} auto-resolved · "
        f"{bs.get('answered', 0)} answered · {bs.get('skipped', 0)} skipped."
    )
    lines.append("")
    if questions["items"]:
        lines += ["| Status | Kind | Question | Answer |", "|---|---|---|---|"]
        for q in questions["items"]:
            qtext = q["question"].replace("|", "\\|").replace("\n", " ")
            ans = _fmt_answer(q["answer"]).replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {q['status']} | {q['kind']} | {qtext} | {ans} |")
        lines.append("")

    # 4) Data-quality flags ----------------------------------------------------
    lines += ["## Data-quality flags", ""]
    total_flags = sum(len(v) for v in needs_attention_grouped.values())
    if total_flags == 0:
        lines += ["_None flagged._", ""]
    else:
        lines.append(f"**{total_flags}** flag(s), grouped by kind "
                     f"(full detail in `needs_attention.json`):")
        lines.append("")
        lines += ["| Kind | Count |", "|---|---:|"]
        for kind, items in needs_attention_grouped.items():
            lines.append(f"| {kind} | {len(items)} |")
        lines.append("")
        for kind, items in needs_attention_grouped.items():
            lines.append(f"- **{kind}** — e.g. {items[0].get('detail', '(no detail)')}")
        lines.append("")

    # 5) Validation result -----------------------------------------------------
    lines += ["## Validation result", ""]
    if validation:
        blocking = validation.get("blocking", {}) or {}
        blocking_n = sum(int(v) for v in blocking.values())
        warnings = validation.get("warnings", {}) or {}
        warning_n = sum(int(v) for v in warnings.values()) if warnings else 0
        lines.append(f"{gate_mark} **{gate}** — {blocking_n} blocking · {warning_n} warning.")
        if blocking_n:
            lines.append("")
            for kind, n in blocking.items():
                if n:
                    lines.append(f"- blocking `{kind}`: {n}")
        lines.append("")
    else:
        lines += ["_No validation summary found — run `migrate validate`._", ""]

    # 6) Post-load reconcile ---------------------------------------------------
    lines += ["## Post-load reconcile", ""]
    if reconcile and reconcile.get("mode") == "live":
        ents = reconcile.get("entities", {})
        overall = all(d.get("conserved") for d in ents.values()) if ents else False
        lines.append(f"{'✅ PASS' if overall else '❌ FAIL'} — canonical ↔ live tenant (Orion read).")
        lines.append("")
        lines += ["| Entity | Canonical | Live present | Conserved |", "|---|---:|---:|:--:|"]
        for entity in sorted(ents, key=_entity_sort_key):
            d = ents[entity]
            mark = "✅" if d.get("conserved") else "❌"
            lines.append(f"| {entity} | {d.get('canonical', '—')} | {d.get('live_present', '—')} | {mark} |")
        lines.append("")
        lines += _render_field_level(reconcile.get("field_level"))
    else:
        lines += ["_No live reconcile yet — run `migrate reconcile --live` after a `--live` load._", ""]

    return "\n".join(lines)


def _render_field_level(fl: Optional[dict]) -> list[str]:
    """Render the field-level (value) reconcile summary (WARN-only) for the report."""
    if not fl:
        return []
    total = fl.get("mismatches_total", 0)
    lines = ["### Field-level (values)", ""]
    if total == 0:
        lines += ["✅ All compared values match the canonical projection (0 mismatches).", ""]
    else:
        lines.append(f"⚠ **{total} field mismatch(es) (warn)** — see `reconciliation.md`. "
                     "Value mismatches are reported, not blocking.")
        lines.append("")
    lines += ["| Entity | Compared | Missing live | Fields compared | Mismatches |",
              "|---|---:|---:|---:|---:|"]
    for entity in sorted(fl.get("entities", {}), key=_entity_sort_key):
        d = fl["entities"][entity]
        lines.append(f"| {entity} | {d['records_compared']} | {d['records_missing_live']} | "
                     f"{d['fields_compared']} | {d['mismatches_total']} |")
    lines.append("")
    per_field = fl.get("per_field") or {}
    if any(per_field.values()):
        lines += ["Per-field mismatch tally (systematic drift):", "",
                  "| Entity | Field | Mismatches |", "|---|---|---:|"]
        for entity in sorted(per_field, key=_entity_sort_key):
            for fname, n in sorted(per_field[entity].items(), key=lambda kv: -kv[1]):
                lines.append(f"| {entity} | {fname} | {n} |")
        lines.append("")
    return lines


# --------------------------------------------------------------------------- #
# The runnable stage                                                           #
# --------------------------------------------------------------------------- #
def build_report(project_root: str | Path, snapshot: str) -> dict:
    """Assemble ``runs/<v>/REPORT.md`` + ensure ``runs/<v>/needs_attention.json``.

    Returns a dict with the written paths + the gathered summary (for the CLI line).
    """
    root = Path(project_root)
    run_dir = root / "runs" / snapshot
    canonical_dir = run_dir / "canonical"

    manifest = _read_json(root / "snapshots" / snapshot / "manifest.json")
    validation = _read_json(run_dir / "validation" / "validation_summary.json")
    assemble_report = _read_json(canonical_dir / "assemble_report.json")
    questions_raw = _read_json(run_dir / "questions.json")
    reconcile = _read_json(run_dir / "reconciliation.json")

    canonical_counts = _canonical_counts(canonical_dir)
    conservation = _conservation_index(validation)
    load_agg, load_source = _load_results(run_dir, canonical_dir)
    questions = _question_summary(questions_raw)
    needs_attention_grouped = group_needs_attention((assemble_report or {}).get("needs_attention", []) or [])

    na_path = ensure_needs_attention(run_dir, assemble_report)

    report_md = render_report(
        snapshot=snapshot,
        manifest=manifest,
        canonical_counts=canonical_counts,
        conservation=conservation,
        load_agg=load_agg,
        load_source=load_source,
        questions=questions,
        needs_attention_grouped=needs_attention_grouped,
        validation=validation,
        reconcile=reconcile,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "REPORT.md"
    report_path.write_text(report_md, encoding="utf-8")

    gate = (validation or {}).get("gate", "UNKNOWN")
    open_questions = questions["by_status"].get("open", 0)
    loaded = load_agg is not None

    # Record the report phase, then refresh the run-state surfaces (SPEC §8/§15):
    # runs/<v>/RUN_LOG.md (constant per-phase progress) + the project-level
    # MIGRATION_STATUS.md entry (one per snapshot, upserted). Done from the report stage
    # so a normal run produces both without a separate `migrate status` call.
    run_state.start_phase(run_dir, "report", project=root.name, snapshot=snapshot)
    run_state.finish_phase(
        run_dir, "report",
        metrics={"gate": gate, "open_questions": open_questions, "loaded": loaded,
                 "canonical_counts": dict(canonical_counts)},
        outputs=[report_path, na_path],
    )
    state = run_state.load(run_dir)
    run_log_path = run_log.write_run_log(run_dir, state)
    load_status = _load_status_line(load_agg)
    entry = run_log.render_status_entry(
        snapshot=snapshot, state=state, entity_counts=dict(canonical_counts),
        validation_gate=gate, open_questions=open_questions, loaded=loaded,
        load_status=load_status,
    )
    status_path = run_log.upsert_migration_status(root, snapshot, entry)

    return {
        "report_path": report_path,
        "needs_attention_path": na_path,
        "run_log_path": run_log_path,
        "migration_status_path": status_path,
        "gate": gate,
        "open_questions": open_questions,
        "question_summary": questions["by_status"],
        "loaded": loaded,
        "needs_attention_total": sum(len(v) for v in needs_attention_grouped.values()),
        "canonical_counts": dict(canonical_counts),
    }


def _load_status_line(load_agg: Optional[dict]) -> str:
    """A compact load status for the project MIGRATION_STATUS.md entry."""
    if not load_agg:
        return "not yet loaded"
    created = sum(b.get("created", 0) for b in load_agg.values())
    updated = sum(b.get("updated", 0) for b in load_agg.values())
    failed = sum(b.get("failed", 0) for b in load_agg.values())
    return f"loaded ({created} created · {updated} updated · {failed} failed)"
