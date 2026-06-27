"""`migrate` — the scriptable CLI the `/migrate` orchestrator drives.

This CLI is the scriptable/CI-able layer. The single orchestrator is the
`/migrate` command (`.claude/commands/migrate.md`); it sequences these stages and
performs the only genuinely AI-driven step — the mapping/value-set proposal and the
cleanse LLM judgment (SPEC §8). Every stage that can be deterministic runs here
directly (assemble, validate, profile, reconcile, map-draft, discover, answer,
report). There is ONE question round (SPEC §9, the `discover`/`answer` pair), not
the old two-gate model.

Project layout (SPEC §16)::

    <projects-root>/<client-slug>/
      project.yaml
      ledger/{mapping.yaml, value_sets.yaml, cell_overrides.jsonl, external_ids.json}
      snapshots/<v>/{raw/, tables/, source_index.parquet, manifest.json, delta.json}
      runs/<v>/{clean/, canonical/, validation/, emit/, load/, report/}

Subcommands (SPEC §8 stage order)::

    init  ingest  delta  map-draft  discover  answer  profile  validate
    assemble  cleanse  emit  load  reconcile  report
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

import delta as delta_mod
import run_state
from snapshot import SourceTableConfig, ingest_snapshot

VERSION = "1.0.0"


# --------------------------------------------------------------------------- #
# Run-state checkpointing (SPEC §8/§10/§17)                                    #
# --------------------------------------------------------------------------- #
class _phase_state:
    """Context manager that records a stage's run-state checkpoint, uniformly.

    Entry → ``start_phase``; clean exit → ``finish_phase`` with the metrics/outputs the
    block records via :meth:`record`; an exception → ``fail_phase`` (then re-raises).
    This adds ONLY state writes around a stage — it never changes the stage's logic or
    output, and a stage run standalone updates run_state exactly the same way the
    `/migrate` orchestrator would. A handler that exits before doing real work (a plan-only
    `load`, a print-stub `map`) simply records nothing and the phase stays pending.
    """

    def __init__(self, args: argparse.Namespace, phase: str) -> None:
        self.phase = phase
        self.root = _project_root(args)
        self.snapshot = getattr(args, "snapshot", None) or "v1"
        self.run_dir = self.root / "runs" / self.snapshot
        self.metrics: Optional[dict] = None
        self.outputs: Optional[list] = None
        self._committed = False

    def __enter__(self) -> "_phase_state":
        slug = self.root.name
        run_state.start_phase(self.run_dir, self.phase, project=slug, snapshot=self.snapshot)
        return self

    def record(self, metrics: Optional[dict] = None, outputs: Optional[list] = None) -> None:
        """Capture the real metrics/outputs to write on a clean finish."""
        if metrics is not None:
            self.metrics = metrics
        if outputs is not None:
            self.outputs = outputs

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            run_state.fail_phase(self.run_dir, self.phase, f"{exc_type.__name__}: {exc}")
            return False
        run_state.finish_phase(self.run_dir, self.phase, self.metrics, self.outputs)
        self._committed = True
        return False


# --------------------------------------------------------------------------- #
# project.yaml helpers                                                         #
# --------------------------------------------------------------------------- #
def _project_root(args: argparse.Namespace) -> Path:
    return Path(args.project).resolve()


def _load_project(root: Path) -> dict:
    pf = root / "project.yaml"
    if not pf.exists():
        sys.exit(f"no project.yaml at {pf} — run `migrate init` first.")
    if yaml is None:
        sys.exit("PyYAML required to read project.yaml.")
    return yaml.safe_load(pf.read_text(encoding="utf-8")) or {}


def _source_configs(project: dict) -> list[SourceTableConfig]:
    out: list[SourceTableConfig] = []
    for s in project.get("sources", []):
        out.append(
            SourceTableConfig(
                table=s["table"],
                source_key=s.get("source_key"),
                key_status=s.get("key_status", "confirmed"),
                key_columns=s.get("key_columns"),
                description=s.get("description", ""),
            )
        )
    return out


def _snapshot_dir(root: Path, snapshot: str) -> Path:
    return root / "snapshots" / snapshot


def _prior_snapshot(snapshot: str) -> Optional[str]:
    """v3 → v2, v1 → None. Assumes the ``v<N>`` convention from the schema."""
    if not snapshot.startswith("v"):
        return None
    try:
        n = int(snapshot[1:])
    except ValueError:
        return None
    return f"v{n - 1}" if n > 1 else None


# --------------------------------------------------------------------------- #
# Subcommand handlers                                                          #
# --------------------------------------------------------------------------- #
def cmd_init(args: argparse.Namespace) -> int:
    root = _project_root(args)
    if (root / "project.yaml").exists() and not args.force:
        sys.exit(f"project.yaml already exists at {root}; pass --force to overwrite the scaffold.")
    for sub in ("ledger", "snapshots", "runs", "logs"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    scaffold = {
        "schema_version": 1,
        "client": {"slug": args.slug or root.name, "name": args.slug or root.name},
        "target": {
            "domain": "CHANGE-ME.everspot.test",
            "token_env_var": "MIGRATION_ORION_TOKEN",
            "user_id_header": 1,
            "ip_whitelisted": False,
        },
        "sources": [{"table": "EXAMPLE", "key_status": "deferred"}],
        "snapshots": [],
    }
    if yaml is None:
        sys.exit("PyYAML required to write project.yaml.")
    (root / "project.yaml").write_text(yaml.safe_dump(scaffold, sort_keys=False), encoding="utf-8")
    print(f"Initialized migration project at {root}")
    print("Next: drop client files into snapshots/v1/raw/, set source_key per table in project.yaml,")
    print("      confirm the sandbox target + IP whitelist, then `migrate ingest`.")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    root = _project_root(args)
    project = _load_project(root)
    snap_dir = _snapshot_dir(root, args.snapshot)
    with _phase_state(args, "ingest") as ps:
        result = ingest_snapshot(snap_dir, _source_configs(project))
        ps.record(
            metrics={"total_rows": sum(result.tables.values()),
                     "tables": dict(result.tables)},
            outputs=[result.manifest_path, result.source_index_path],
        )
    print(f"Ingested {args.snapshot}: {sum(result.tables.values())} "
          f"rows across {len(result.tables)} tables.")
    print(f"  manifest:     {result.manifest_path}")
    print(f"  source_index: {result.source_index_path}")
    print("Next: review manifest.json, then `migrate delta` (or `migrate map` for v1).")
    return 0


def cmd_delta(args: argparse.Namespace) -> int:
    root = _project_root(args)
    cur_index = _snapshot_dir(root, args.snapshot) / "source_index.parquet"
    if not cur_index.exists():
        sys.exit(f"no source_index at {cur_index} — run `migrate ingest` first.")
    prior = args.against or _prior_snapshot(args.snapshot)
    prior_index = _snapshot_dir(root, prior) / "source_index.parquet" if prior else None
    if prior_index is not None and not prior_index.exists():
        print(f"  (prior snapshot {prior} index missing — treating {args.snapshot} as all-NEW)")
        prior_index = None

    with _phase_state(args, "delta") as ps:
        report = delta_mod.compute_delta(
            cur_index, prior_index, current_snapshot=args.snapshot,
            prior_snapshot=prior if prior_index else None,
        )
        json_path, md_path = delta_mod.write_delta(report, _snapshot_dir(root, args.snapshot))
        totals = report.to_dict()["totals"]
        ps.record(
            metrics={"against": prior if prior_index else None, **totals},
            outputs=[json_path, md_path],
        )
    print(f"Delta {args.snapshot} vs {prior or '(none)'}: "
          f"{totals['NEW']} new · {totals['CHANGED']} changed · "
          f"{totals['UNCHANGED']} unchanged · {totals['REMOVED']} removed.")
    print(f"  review: {md_path}")
    print(f"  json:   {json_path}")
    new_cols = [t for t, td in report.tables.items() if td.new_columns]
    if new_cols:
        print(f"  ⚠ new columns in {new_cols} → re-run `migrate map` for those tables.")
    return 0


def cmd_map(args: argparse.Namespace) -> int:
    print("Mapping has two layers:")
    print("  - deterministic draft: run `migrate map-draft` (auto-drafts mapping.yaml + value_sets.yaml).")
    print("  - AI refinement: the `/migrate` command proposes/refines the mapping and value-set")
    print("    resolutions against the target contract + pattern library, then surfaces anything")
    print("    undecidable in the single question round (`migrate discover` / `migrate answer`).")
    return 0


def _read_residuals(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str) + "\n")


def cmd_cleanse(args: argparse.Namespace) -> int:
    print("Cleanse runs the deterministic Python tier (parse_name/normalize_date/…),")
    print("each cell → {value, confidence, method, needs_llm}; low-confidence cells route to the LLM tier.")

    if not getattr(args, "llm", False):
        print("LLM fallback (residual cells only): re-run with `migrate cleanse --llm` to run the")
        print("structured-output LLM tier directly on clean/residuals.jsonl. The `/migrate` command")
        print("drives this tier when residuals are authorized for LLM resolution (SPEC §8 stage 8).")
        return 0

    # --llm: run the structured-output LLM tier directly on residuals.jsonl.
    import llm_fallback
    from transform_cache import TransformCache

    root = _project_root(args)
    clean_dir = root / "runs" / args.snapshot / "clean"
    residuals_path = clean_dir / "residuals.jsonl"
    if not residuals_path.exists():
        sys.exit(f"no residuals at {residuals_path} — run the deterministic cleanse first.")

    residuals = _read_residuals(residuals_path)
    print(f"LLM fallback: {len(residuals)} residual cell(s) from {residuals_path}")
    print(f"  model: {llm_fallback.MODEL}  (set MIGRATION_LLM_MODEL to override; "
          "claude-haiku-4-5 for high volume)")
    if os.environ.get("MIGRATION_LLM_DRYRUN") == "1":
        print("  MIGRATION_LLM_DRYRUN=1 → offline path: all residuals become exceptions (no API call).")
        print("  (this is an OPTIONAL cost/determinism switch — not a PII gate; AI may process real client data)")
    elif not os.environ.get("ANTHROPIC_API_KEY"):
        print("  no ANTHROPIC_API_KEY in env → the LLM tier cannot call the model; "
              "residuals become exceptions (deterministic by default).")

    log_path = clean_dir / "llm_log.jsonl"
    with _phase_state(args, "cleanse") as ps:
        with TransformCache(root / "ledger") as cache:
            result = llm_fallback.resolve_residuals(
                residuals,
                cache,
                batch_size=args.batch_size,
                max_batches=args.max_batches,
                log_path=log_path,
            )

        _write_jsonl(clean_dir / "exceptions.jsonl", result["exceptions"])
        _write_jsonl(clean_dir / "resolved.jsonl", result["resolved"])
        stats = result["stats"]
        ps.record(
            metrics={"residuals": len(residuals), "resolved": len(result["resolved"]),
                     "exceptions": len(result["exceptions"]),
                     "calls": stats["calls"], "input_tokens": stats["input_tokens"],
                     "output_tokens": stats["output_tokens"]},
            outputs=[clean_dir / "exceptions.jsonl", clean_dir / "resolved.jsonl"],
        )
    print(f"  resolved:   {len(result['resolved'])}")
    print(f"  exceptions: {len(result['exceptions'])}  → {clean_dir / 'exceptions.jsonl'} (question-round input)")
    print(f"  calls={stats['calls']}  input_tokens={stats['input_tokens']}  "
          f"output_tokens={stats['output_tokens']}  cached_writes={stats['cached_writes']}")
    print(f"  log: {log_path} (append-only; replayed on resume)")
    return 0


def cmd_assemble(args: argparse.Namespace) -> int:
    """Run the DETERMINISTIC canonical-graph builder (the mechanical assemble path).

    The genuinely-ambiguous decisions (column→field, value-set meanings, entity
    merges) are already resolved upstream by the mapping stage + the single question
    round and live in the ledger; assemble only applies those settled decisions
    deterministically. Genuinely unresolved cases (a new value-set code, an
    unresolvable required ref) are NOT papered over — they land in
    ``assemble_report.json`` for the question round (`migrate discover`) to surface.
    """
    import assemble as assemble_mod

    root = _project_root(args)
    mapping_path = root / "ledger" / "mapping.yaml"
    if not mapping_path.exists():
        print("Assemble needs a settled ledger/mapping.yaml.")
        print("Run `migrate map-draft` for the deterministic draft; the `/migrate` command")
        print("refines it. Then settle anything open via `migrate discover` / `migrate answer`.")
        return 0

    with _phase_state(args, "assemble") as ps:
        result = assemble_mod.assemble(
            root,
            args.snapshot,
            use_cache=not getattr(args, "no_cache", False),
            scoped=not getattr(args, "full", False),
        )
        na_summary = (assemble_mod.summarize_needs_attention(result.needs_attention)
                      if result.needs_attention else {"total": 0, "by_kind": {}})
        ps.record(
            metrics={"entity_counts": dict(result.entity_counts),
                     "minted": result.minted, "reused": result.reused,
                     "cache_hits": result.cache_hits, "cache_misses": result.cache_misses,
                     "needs_attention_total": na_summary["total"],
                     "needs_attention_by_kind": dict(na_summary.get("by_kind", {}))},
            outputs=[result.canonical_dir],
        )
    total = sum(result.entity_counts.values())
    print(f"Assembled {total} canonical record(s) across {len(result.entity_counts)} entities:")
    for entity, count in sorted(result.entity_counts.items()):
        print(f"  {entity}.ndjson: {count}")
    print(f"  external_ids: {result.minted} minted · {result.reused} reused")
    print(f"  transform cache: {result.cache_hits} hit · {result.cache_misses} miss")
    if result.needs_attention:
        import assemble as assemble_mod
        summary = assemble_mod.summarize_needs_attention(result.needs_attention)
        print(f"  ⚠ {summary['total']} needs-attention item(s) "
              f"→ {result.canonical_dir / 'assemble_report.json'} (question-round input):")
        for kind, n in summary["by_kind"].items():
            print(f"    - {kind}: {n}")
        for reason, n in list(summary["needs_llm_by_reason"].items())[:8]:
            print(f"        · {reason}: {n}")
    print(f"  canonical: {result.canonical_dir}")
    print("Next: `migrate validate`, then `migrate emit`.")
    return 0


def cmd_profile(args: argparse.Namespace) -> int:
    """Stage 3 — Profile the ingested snapshot tables (deterministic, offline)."""
    import profile as profile_mod

    root = _project_root(args)
    snap_dir = _snapshot_dir(root, args.snapshot)
    out_dir = snap_dir / "profile"
    with _phase_state(args, "profile") as ps:
        summary = profile_mod.profile_snapshot(snap_dir)
        ps.record(
            metrics={"tables": len(summary["tables"]),
                     "table_rows": {t: td["row_count"] for t, td in summary["tables"].items()}},
            outputs=[out_dir / "summary.json"],
        )
    print(f"Profiled snapshot {args.snapshot}: {len(summary['tables'])} table(s) → {out_dir}")
    for table, td in summary["tables"].items():
        print(f"  {table}: {td['row_count']} rows · {td['columns']} columns")
        keys = td["candidate_keys"]
        unique = [k for k in keys if k["unique"]]
        if unique:
            k = unique[0]
            print(f"    candidate key: {k['columns']} (uniqueness {k['uniqueness_ratio']})")
        elif keys:
            k = keys[0]
            print(f"    best key: {k['columns']} (uniqueness {k['uniqueness_ratio']}, not fully unique)")
        if td["value_set_columns"]:
            print(f"    value-set candidates: {td['value_set_columns']}")
        if td["signals"]:
            print(f"    signals: {', '.join(f'{s}={cols}' for s, cols in td['signals'].items())}")
    print(f"  summary: {out_dir / 'summary.json'}")
    print("Next: Wave-0 introspect + auto-draft mapping (AI), then `migrate validate`.")
    return 0


def _project_sources(project: dict) -> list[dict]:
    """The raw source declarations (table + source_key + key_status) from project.yaml."""
    return list(project.get("sources", []))


def cmd_map_draft(args: argparse.Namespace) -> int:
    """Stage 5 — Auto-draft mapping.yaml + value_sets.yaml + mapping_review.md."""
    import map_draft

    root = _project_root(args)
    project = _load_project(root)
    with _phase_state(args, "map-draft") as ps:
        result = map_draft.map_draft(root, args.snapshot, sources=_project_sources(project))
        n_tables = len(result.drafts)
        confident = sum(
            1 for td in result.drafts for c in td.columns
            if c.action in ("map", "value_map", "external_id") and not c.is_gap
        )
        gaps = sum(1 for td in result.drafts for c in td.columns if c.is_gap)
        gaps += sum(len(td.gaps) for td in result.drafts)
        inferred = sum(1 for td in result.drafts if td.primary_inferred and td.primary_entity)
        ps.record(
            metrics={"tables": n_tables, "confident_mappings": confident,
                     "gaps": gaps, "inferred_routings": inferred,
                     "settled_existed": result.settled_existed},
            outputs=[result.mapping_path, result.value_sets_path, result.review_path],
        )
    print(f"Drafted mapping for {n_tables} table(s) of snapshot {args.snapshot}:")
    for td in result.drafts:
        routing = (td.primary_entity or "(undecided)") + (
            " + " + " + ".join(td.secondary_entities) if td.secondary_entities else ""
        )
        flag = " ⚠inferred" if td.primary_inferred else ""
        print(f"  {td.table}: → {routing}{flag}")
    print(f"  confident mappings: {confident} · gaps (→ question round): {gaps} · "
          f"inferred routings: {inferred}")
    if result.settled_existed:
        print("  (a SETTLED ledger exists — draft written to sidecars, not clobbered)")
    print(f"  mapping:    {result.mapping_path}")
    print(f"  value_sets: {result.value_sets_path}")
    print(f"  review:     {result.review_path}")
    print("Next: `migrate discover` (the single question round).")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    """Stage 6 + THE QUESTION ROUND — one batched discovery pass (SPEC §9)."""
    import discover as discover_mod

    root = _project_root(args)
    project = _load_project(root)
    with _phase_state(args, "discover") as ps:
        result = discover_mod.discover(root, args.snapshot, sources=_project_sources(project))
        ps.record(
            metrics={"open": result.open_count, "auto_resolved": result.auto_resolved_count,
                     "answered": result.answered_count, "skipped": result.skipped_count},
            outputs=[result.questions_json_path, result.questions_md_path],
        )
    print(f"Discovery {args.snapshot}: "
          f"{result.open_count} open · {result.auto_resolved_count} auto-resolved · "
          f"{result.answered_count} answered · {result.skipped_count} skipped")
    print(f"  questions: {result.questions_json_path}")
    print(f"  review:    {result.questions_md_path}")
    if result.any_open:
        print(f"  ⚠ {result.open_count} OPEN question(s) — orchestrator MUST NOT proceed (SPEC §9.5).")
        print("  Next: answer them — `migrate answer --accept-all` or edit an answers.json, then `migrate answer`.")
    else:
        print("  ✅ No open questions — safe to proceed (assemble → validate → load).")
    return 1 if result.any_open else 0


def cmd_answer(args: argparse.Namespace) -> int:
    """THE QUESTION ROUND — apply answers, persist to the ledger, write back (SPEC §9.5)."""
    import answer as answer_mod

    root = _project_root(args)
    answers = None
    if not args.accept_all:
        answers_path = Path(args.answers) if args.answers else (root / "runs" / args.snapshot / "answers.json")
        if not answers_path.exists():
            sys.exit(f"no answers file at {answers_path} — pass --accept-all or provide --answers <file>.")
        answers = json.loads(answers_path.read_text(encoding="utf-8"))

    with _phase_state(args, "answer") as ps:
        result = answer_mod.apply_answers(
            root, args.snapshot, answers=answers, accept_all=args.accept_all,
            answered_by=args.by,
        )
        ps.record(
            metrics={"answered": result.answered, "auto_accepted": result.auto_accepted,
                     "skipped": result.skipped, "skipped_blocking": result.skipped_blocking,
                     "still_open": result.still_open, "persisted": len(result.persisted)},
        )
    print(f"Applied answers for {args.snapshot}:")
    print(f"  answered {result.answered} · auto-accepted {result.auto_accepted} · "
          f"skipped {result.skipped} · still open {result.still_open}")
    print(f"  applied: {result.applied_value_sets} value-set(s) · "
          f"{result.applied_source_keys} source-key(s) · {result.recorded_other} other recorded")
    print(f"  persisted {len(result.persisted)} question record(s) to ledger/questions/")
    if not result.gate_clear:
        if result.still_open:
            print(f"  ⚠ {result.still_open} question(s) STILL OPEN — orchestrator MUST NOT proceed (SPEC §9.5).")
        if result.skipped_blocking:
            print(f"  ⚠ {result.skipped_blocking} BLOCKING question(s) SKIPPED — known gap; orchestrator MUST NOT proceed (L3).")
    else:
        print("  ✅ No open or skipped-blocking questions remain — safe to proceed.")
    return 0 if result.gate_clear else 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Stage 10 — Validate canonical NDJSON: schema/contract/refs/conservation (offline)."""
    import validate as validate_mod

    root = _project_root(args)
    out_dir = root / "runs" / args.snapshot / "validation"
    with _phase_state(args, "validate") as ps:
        result = validate_mod.validate_run(root, args.snapshot)
        ps.record(
            metrics={"gate": result.gate, "passed": result.passed,
                     "blocking": len(result.blocking_failures),
                     "warnings": sum(result.warnings.values()) if result.warnings else 0,
                     "entity_counts": dict(result.entity_counts)},
            outputs=[out_dir / "validation_summary.json"],
        )
    print(f"Validated {args.snapshot} → {out_dir}")
    for entity, n in sorted(result.entity_counts.items()):
        print(f"  {entity}: {n} record(s)")
    dangling = sum(1 for f in result.blocking_failures if f.kind == "dangling_ref")
    print(f"  dangling refs: {dangling}")
    if result.warnings:
        print(f"  warnings: {dict(result.warnings)}")
    if result.blocking_failures:
        print(f"  ⚠ {len(result.blocking_failures)} BLOCKING failure(s) → {out_dir / 'failures.jsonl'}:")
        by_kind: dict[str, int] = {}
        for f in result.blocking_failures:
            by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
        for kind, n in by_kind.items():
            print(f"    - {kind}: {n}")
        for f in result.blocking_failures[:5]:
            print(f"      · {f.entity} {f.external_id}: {f.detail}")
    print(f"  summary: {out_dir / 'validation_summary.json'}")
    print(validate_mod.render_gate_line(result))
    return 0 if result.passed else 1


def cmd_emit(args: argparse.Namespace) -> int:
    from emit_excel import emit  # local import: openpyxl only needed here

    root = _project_root(args)
    run = root / "runs" / args.snapshot
    canonical = run / "canonical"
    if not canonical.is_dir():
        sys.exit(f"no canonical dir at {canonical} — run assemble first.")
    with _phase_state(args, "emit") as ps:
        written = emit(canonical, run / "emit")
        ps.record(
            metrics={"files": len(written), "names": [p.name for p in written]},
            outputs=[run / "emit"],
        )
    print(f"Emitted {len(written)} wave-ordered Excel file(s) to {run / 'emit'}:")
    for p in written:
        print(f"  {p.name}")
    print(f"  runbook: {run / 'emit' / 'RUNBOOK.md'}")
    return 0


def cmd_load(args: argparse.Namespace) -> int:
    root = _project_root(args)
    project = _load_project(root)
    target = project.get("target", {})

    if not args.live:
        print("Load (PLAN — pass --live to execute via Orion):")
        print("  Wave order: cemetery+property_type (prereq) → property_group → property → customer → interment.")
        print("  Each record is POSTed to its Orion resource; its external_id is registered on the")
        print("  polymorphic `external-ids` resource; FKs resolve via the external_id→internal-id map;")
        print("  re-runs upsert by external_id (PATCH if present, else POST). Excel emit is the alt path.")
        print(f"  Target: https://{target.get('domain','CHANGE-ME')}/api/v1  user-id={target.get('user_id_header')}")
        return 0

    from orion_client import OrionClient
    import orion_load

    base_url = args.base_url or f"https://{target['domain']}/api/v1"
    token_var = target.get("token_env_var", "")
    token = os.environ.get(token_var)
    if not token:
        sys.exit(f"set ${token_var} to the tenant API token (sha256 stored on the tenant).")
    client = OrionClient(base_url, token=token, user_id=target.get("user_id_header", 1))
    if args.insecure:
        import warnings
        import urllib3
        warnings.simplefilter("ignore")
        urllib3.disable_warnings()
        client._session.verify = False

    cemetery = args.cemetery or project.get("client", {}).get("name") or "Migrated Cemetery"
    with _phase_state(args, "load") as ps:
        res = orion_load.load(root, args.snapshot, client, cemetery_name=cemetery, scoped=not args.no_scope)
        ps.record(
            metrics={"created": dict(res.created), "updated": dict(res.updated),
                     "skipped": dict(res.skipped), "failed": dict(res.failed),
                     "cemetery_id": res.cemetery_id, "property_type_id": res.property_type_id,
                     "attribute_values_written": res.attribute_values_written,
                     "reference_gaps": len(res.reference_gaps), "errors": len(res.errors)},
            outputs=[root / "runs" / args.snapshot / "canonical" / "load_report.json"],
        )
    print(f"Loaded {args.snapshot} via Orion (cemetery_id={res.cemetery_id}, property_type_id={res.property_type_id}):")
    for entity in ("property_group", "property", "customer", "interment"):
        c, u, s, f = (res.created.get(entity, 0), res.updated.get(entity, 0),
                      res.skipped.get(entity, 0), res.failed.get(entity, 0))
        print(f"  {entity:16s} created {c} · updated {u} · skipped {s} · failed {f}")
    print(f"  {'location attrs':16s} written {res.attribute_values_written} · failed {res.attribute_values_failed}"
          " (property section/lot/space → Attribute engine)")
    if res.reference_gaps:
        print(f"  ⚠ {len(res.reference_gaps)} attribute reference gap(s) (Wave-0b) "
              f"→ runs/{args.snapshot}/canonical/load_report.json")
    if res.errors:
        print(f"  ⚠ {len(res.errors)} error/warning(s) → runs/{args.snapshot}/canonical/load_report.json")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Stage 12 — Assemble the consolidated runs/<v>/REPORT.md (SPEC §15.2; offline)."""
    import report as report_mod

    root = _project_root(args)
    res = report_mod.build_report(root, args.snapshot)
    bs = res["question_summary"]
    print(f"Report {args.snapshot} → {res['report_path']}")
    print(f"  validation: {res['gate']} · open questions: {res['open_questions']} · "
          f"loaded: {'yes' if res['loaded'] else 'not yet'}")
    print(f"  questions: {bs.get('open', 0)} open · {bs.get('auto-resolved', 0)} auto-resolved · "
          f"{bs.get('answered', 0)} answered · {bs.get('skipped', 0)} skipped")
    print(f"  needs_attention: {res['needs_attention_total']} flag(s) → {res['needs_attention_path']}")
    print(f"  run log:  {res['run_log_path']}")
    print(f"  project status: {res['migration_status_path']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Render runs/<v>/RUN_LOG.md from run_state.json + print a compact summary (SPEC §8)."""
    import run_log

    root = _project_root(args)
    run_dir = root / "runs" / args.snapshot
    if not (run_dir / run_state.STATE_FILENAME).exists():
        sys.exit(f"no run_state.json at {run_dir} — run a stage first (e.g. `migrate ingest`).")

    state = run_state.load(run_dir)
    log_path = run_log.write_run_log(run_dir, state)
    prog = run_state.progress(state)
    print(f"Run status {args.snapshot}: {prog['done']}/{prog['total']} phases done "
          f"(updated {state.get('updated_at')})")
    for phase in prog["phases"]:
        ph = state["phases"].get(phase)
        status = ph.get("status", "pending") if ph else "pending"
        mark = {"done": "✅", "running": "🔄", "failed": "❌"}.get(status, "·")
        line = f"  {mark} {phase:12s} {status}"
        if ph and ph.get("error"):
            line += f"  — {ph['error'][:80]}"
        print(line)
    cp = state.get("load_checkpoint") or {}
    if cp and not cp.get("complete") and cp.get("current_wave"):
        print(f"  ⚠ load incomplete: done {cp.get('waves_done', [])} · "
              f"current `{cp.get('current_wave')}` (a re-run resumes here)")
    print(f"  run log: {log_path}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Stage 10/12 — Reconcile: offline source→canonical conservation, or post-load --live."""
    import reconcile as reconcile_mod

    root = _project_root(args)

    if not args.live:
        results, detail = reconcile_mod.reconcile_offline(root, args.snapshot)
    else:
        project = _load_project(root)
        target = project.get("target", {})
        from orion_client import OrionClient

        base_url = args.base_url or f"https://{target['domain']}/api/v1"
        token_var = target.get("token_env_var", "")
        token = os.environ.get(token_var)
        if not token:
            sys.exit(f"set ${token_var} to the tenant API token for the --live read.")
        client = OrionClient(base_url, token=token, user_id=target.get("user_id_header", 1))
        if args.insecure:
            import warnings
            import urllib3
            warnings.simplefilter("ignore")
            urllib3.disable_warnings()
            client._session.verify = False
        results, detail = reconcile_mod.reconcile_live(root, args.snapshot, client)

        if getattr(args, "correct", False):
            # A2 — self-healing: PATCH already-loaded live records whose field VALUE
            # drifted from the canonical projection (e.g. after a script fix changed
            # canonical output for unchanged-source rows). Idempotent: a second run
            # finds nothing. Then re-read live so the report reflects the corrected state.
            corr = reconcile_mod.apply_corrections(root, args.snapshot, client)
            patched = sum(e.get("records_patched", 0) for e in corr.get("entities", {}).values())
            fields = sum(e.get("fields_patched", 0) for e in corr.get("entities", {}).values())
            print(f"  self-heal: PATCHed {patched} record(s) · {fields} field(s) to match canonical")
            for ent, ed in corr.get("entities", {}).items():
                if ed.get("records_patched"):
                    print(f"    {ent:14s} {ed['records_patched']} record(s) corrected")
            for err in corr.get("errors", []) or []:
                print(f"    ⚠ {err}")
            results, detail = reconcile_mod.reconcile_live(root, args.snapshot, client)

    md_path, json_path = reconcile_mod.write_reconcile_stage(root, args.snapshot, results, detail)
    # Count conservation gates the run; field-level value mismatches are WARN only.
    overall = all(r.passed for r in results)
    fl = detail.get("field_level") or {}
    fl_mismatches = fl.get("mismatches_total", 0)
    run_state.start_phase(root / "runs" / args.snapshot, "reconcile",
                          project=root.name, snapshot=args.snapshot)
    run_state.finish_phase(
        root / "runs" / args.snapshot, "reconcile",
        metrics={"mode": detail["mode"], "passed": overall,
                 "entities": {e: d.get("conserved") for e, d in detail["entities"].items()},
                 "field_mismatches": fl_mismatches},
        outputs=[md_path, json_path],
    )
    print(f"Reconcile {args.snapshot} ({detail['mode']}): {'✅ PASS' if overall else '❌ FAIL'}")
    for entity, d in detail["entities"].items():
        if detail["mode"] == "offline":
            mark = "✅" if d["conserved"] else f"❌ (dropped {d['dropped']})"
            print(f"  {entity:16s} source {d['source_rows']} → canonical {d['canonical_records']}  {mark}")
        else:
            mark = "✅" if d["conserved"] else "❌"
            print(f"  {entity:16s} canonical {d['canonical']} → live {d['live_present']}  {mark}")
    if fl:
        fmark = "✅" if fl_mismatches == 0 else f"⚠ {fl_mismatches} (warn — not blocking)"
        print(f"  field-level values: {fmark}")
        for entity, fd in fl.get("entities", {}).items():
            if fd["mismatches_total"]:
                drift = ", ".join(f"{f}×{n}" for f, n in
                                  sorted(fl.get("per_field", {}).get(entity, {}).items(),
                                         key=lambda kv: -kv[1]))
                print(f"    {entity:14s} {fd['mismatches_total']} mismatch(es): {drift}")
    print(f"  report: {md_path}")
    print(f"  json:   {json_path}")
    return 0 if overall else 1


# --------------------------------------------------------------------------- #
# argparse wiring                                                              #
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="migrate", description=__doc__.split("\n")[0])
    p.add_argument("--version", action="version", version=f"migrate {VERSION}")
    p.add_argument("-p", "--project", default=".", help="Project root dir (holds project.yaml).")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("init", help="Scaffold a new migration project dir.")
    sp.add_argument("slug", nargs="?", help="Client slug (defaults to project dir name).")
    sp.add_argument("--force", action="store_true", help="Overwrite an existing project.yaml scaffold.")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("ingest", help="Normalize raw drop → tables + source_index + manifest.")
    sp.add_argument("-s", "--snapshot", default="v1", help="Snapshot id, e.g. v1.")
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("delta", help="Classify NEW/CHANGED/UNCHANGED/REMOVED vs prior snapshot.")
    sp.add_argument("-s", "--snapshot", required=True, help="Current snapshot id, e.g. v2.")
    sp.add_argument("--against", help="Prior snapshot id (defaults to v<N-1>).")
    sp.set_defaults(func=cmd_delta)

    sp = sub.add_parser("map", help="Pointer to `map-draft` (deterministic) + the `/migrate` AI mapping refinement.")
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_map)

    sp = sub.add_parser(
        "map-draft",
        help="Stage 5: deterministic auto-draft of mapping.yaml + value_sets.yaml (never clobbers a settled ledger).",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_map_draft)

    sp = sub.add_parser(
        "discover",
        help="THE QUESTION ROUND: one batched discovery pass → questions.json/.md (exit 1 if any OPEN).",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_discover)

    sp = sub.add_parser(
        "answer",
        help="Apply answers (accept-all or an answers.json) → persist to ledger + write back into mapping/value_sets.",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.add_argument("--accept-all", action="store_true",
                    help="Take every question's proposed_answer as its answer.")
    sp.add_argument("--answers", default=None,
                    help="Path to answers.json {id: answer} (default runs/<v>/answers.json).")
    sp.add_argument("--by", default="operator", help="Recorded answered_by (default 'operator').")
    sp.set_defaults(func=cmd_answer)

    sp = sub.add_parser(
        "profile",
        help="Per-column stats + candidate keys + value-sets + data-shape signals.",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_profile)

    sp = sub.add_parser(
        "validate",
        help="Schema + contract + referential integrity + count conservation (PASS/FAIL gate).",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser(
        "assemble",
        help="Deterministic canonical-graph builder → NDJSON (mechanical path).",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.add_argument(
        "--full",
        action="store_true",
        help="Build the whole snapshot, ignoring delta scoping (v2+ default is scoped).",
    )
    sp.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the Tier-3 transform cache (forces a re-parse of every cell).",
    )
    sp.set_defaults(func=cmd_assemble)

    sp = sub.add_parser("cleanse", help="Deterministic cleanse + AI/`--llm` LLM-fallback.")
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.add_argument(
        "--llm",
        action="store_true",
        help="Run the structured-output LLM tier on clean/residuals.jsonl directly "
             "(otherwise the `/migrate` command drives it). Set MIGRATION_LLM_DRYRUN=1 "
             "for the offline/no-key path.",
    )
    sp.add_argument("--batch-size", type=int, default=50, help="Residuals per model call (default 50).")
    sp.add_argument("--max-batches", type=int, default=None, help="Cost ceiling: cap on total model calls.")
    sp.set_defaults(func=cmd_cleanse)

    sp = sub.add_parser("emit", help="Canonical NDJSON → wave-ordered Excel + RUNBOOK.")
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_emit)

    sp = sub.add_parser("load", help="Load canonical records into the tenant via the Orion API.")
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.add_argument("--live", action="store_true", help="Execute the load (default prints the plan only).")
    sp.add_argument("--insecure", action="store_true", help="Skip TLS verify (Herd self-signed cert).")
    sp.add_argument("--base-url", default=None, help="Override the Orion base URL (default https://<domain>/api/v1).")
    sp.add_argument("--cemetery", default=None, help="Cemetery name to create/use (default client.name).")
    sp.add_argument("--no-scope", action="store_true", help="Load all records, ignoring delta scope on v2+.")
    sp.set_defaults(func=cmd_load)

    sp = sub.add_parser(
        "report",
        help="Stage 12: assemble the consolidated runs/<v>/REPORT.md + needs_attention.json (offline).",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser(
        "status",
        help="Render runs/<v>/RUN_LOG.md from run_state.json + print a compact per-phase summary.",
    )
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("reconcile", help="Counts + money totals: source↔canonical (offline) or ↔live.")
    sp.add_argument("-s", "--snapshot", default="v1")
    sp.add_argument("--live", action="store_true",
                    help="Post-load: read the live tenant via Orion (offline never hits the network).")
    sp.add_argument("--insecure", action="store_true", help="Skip TLS verify (Herd self-signed cert).")
    sp.add_argument("--base-url", default=None, help="Override the Orion base URL for --live.")
    sp.add_argument("--correct", action="store_true",
                    help="With --live: self-heal — PATCH live records whose field value "
                         "drifted from the canonical projection (idempotent).")
    sp.set_defaults(func=cmd_reconcile)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
