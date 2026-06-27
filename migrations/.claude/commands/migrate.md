---
description: Drive a client data-migration end-to-end into an Everspot sandbox — autonomous through every runnable stage, pausing exactly once for the question round.
---

# /migrate — the data-migration orchestrator

You are the **conductor** of Everspot's autonomous data-migration pipeline (SPEC:
`docs/migration-pipeline/SPEC.md`). Drive one client migration from raw files to a
loaded, reconciled, reported sandbox tenant. Run **unattended** through every runnable
stage; **pause exactly once** — the single question round (§9). After answers, run to
completion and hand back one `REPORT.md`.

This command is itself a **maintained, versioned artifact** (§11.1). Obey the
self-improvement loop at the end of every run — running `/migrate` should leave the
general layer a little better than it found it.

`$ARGUMENTS` = a **project slug** (or path) + a **sentence of context** + optional flags:
- `--live` — actually load into the sandbox via Orion (default: **dry-plan only** — print
  the load plan, do not write to the tenant). `migrate emit` (Excel) is always available
  as the alternate output.
- `--snapshot vN` — operate on a specific drop (default `v1`; v2+ is the incremental path).
- The LLM cleanse tier may process **real client data** per the user's standing
  authorization — there is **no `--authorize-llm` gate**. It goes live only when
  `ANTHROPIC_API_KEY` is set; absent a key it stays deterministic (residuals →
  exceptions, no call). `MIGRATION_LLM_DRYRUN=1` is an **optional** cost/determinism
  switch (forces the offline path even with a key), not a PII gate.

## The CLI you drive

Every stage is a subcommand of the pipeline CLI. **Always** invoke it with the venv
python and `-p <project-dir>`:

```bash
PIPE=docs/migration-pipeline
PY=$PIPE/.venv/bin/python
PROJ=.context/migration-projects/<slug>          # or the path given in $ARGUMENTS
$PY $PIPE/scripts/migrate.py -p $PROJ <subcommand> [-s vN] [flags]
```

Runnable subcommands: `init · ingest · delta · profile · map-draft · discover · answer ·
assemble · cleanse · validate · reconcile · emit · load · report · status`. If the venv is
missing, rebuild it per SPEC §18 (it is not committed).

**Run-state checkpointing (SPEC §8/§10/§17).** Every runnable stage records a structured
checkpoint into `runs/<v>/run_state.json` (per-phase status/metrics/outputs + a
`load_checkpoint`) on entry/exit — automatically, whether a stage is driven by this command
or run standalone. `migrate status -s <v>` renders `runs/<v>/RUN_LOG.md` (the constant,
human-readable per-phase progress record) and prints a compact summary; the `report` stage
refreshes `RUN_LOG.md` + the project-level `MIGRATION_STATUS.md` entry automatically.

---

## START-OF-RUN: load only what this run needs (§11.3 tiered loading)

1. Read `docs/migration-pipeline/knowledge/INDEX.md` (cheap) **and** all of
   `knowledge/core/*` (always loaded: `ask-policy.md`, `everspot-cheatsheet.md`,
   `contract-summary.md`).
2. After `profile` (stage 3) you will know the run's data-shape **signals**. Load **only**
   the `knowledge/topics/*.md` whose `triggers` match those signals + the current stage —
   never load all topics "just in case".
3. **Delegate context-heavy reads to sub-agents** that return *conclusions, not file
   dumps* (§11.3 #4): codebase introspection (via codebase-memory-mcp), profiling of huge
   tables, reading old-run artifacts. The bytes must not enter your context.
   - **Where the Everspot codebase lives:** resolve it from `scripts/config.py`
     (`everspot_codebase_path()` — precedence env `EVERSPOT_CODEBASE_PATH` → `pipeline.toml`
     → default repo root). Use that path for **both** codebase-memory-mcp / grep
     self-introspection **and** for `php artisan migration:generate-contract` (run it with
     `cwd` set to that path: `config.artisan_command("migration:generate-contract")`).
     Never hard-code the path — this is what lets the pipeline keep working once it is
     extracted into its own repo (SPEC §16/§18); just set the env/config there.
4. **Resume check (orchestrator-driven):** if the project exists, this is a RESUME / v2 —
   reuse the ledger, never re-mint external_ids, never re-ask a settled question. **Read
   `runs/<v>/run_state.json`** (or run `migrate status -s <v>`): **YOU (the orchestrator)
   SKIP any phase whose `status` is already `done`** (its output artifact is current) —
   the deterministic `migrate <phase>` CLI commands do NOT auto-skip a done phase, so the
   skip is your call from `run_state` (use `run_state.is_done`). The LOAD stage is the one
   exception that self-resumes: a fresh `migrate load` resumes an incomplete load from its
   `load_checkpoint` at wave granularity (see stage 11). A `failed` or `pending` phase is
   (re)run. This is the structured, machine-readable resume gate — use it instead of only
   eyeballing artifacts.

---

## The phase flow (SPEC §8, stages 0–13)

Before each stage: **idempotency gate (orchestrator-applied)** — is the phase already
`status:done` in `run_state.json` (and its output artifact current vs its inputs and the
ledger)? If yes, YOU reuse and move on (§10, §9.5). Each stage records its own checkpoint
(start → metrics on success → error on failure), so this gate reads from one structured
place — but it is the orchestrator that honors it; invoking `migrate <phase>` directly
always re-runs that phase.

### 0 · Acquire sandbox  `[auto]`
Load into a **dev sandbox pulled from production — never the live client tenant**
(topic: `sandbox-acquisition`).
- **Acceptance default:** the sandbox `bellschapel-sb.manama-v1.test` already exists —
  just confirm it serves (a 200). Only pull/refresh if it is missing or stale.
- Otherwise: `pullFromProduction()` → deterministic `<prefix>-sb.<root>` domain;
  `refreshFromProduction()` is cache-first (offline rebuild). Target by **domain**, never
  repoint. Provision/refresh the tenant API token if expired.
- Record the target domain + `user_id` header + token env var in `project.yaml`.

### 1 · Intake  `[AI]`
Read the dropped files in `snapshots/<v>/raw/` + the context sentence. For each sheet,
infer **"what a row is"** (e.g. a flat burial register = one row → property + customer +
interment) and the **`source_key`** (the column(s) that stably identify a record).
- Confirm the key against `migrate profile`'s candidate keys. **Ask ONLY if undecidable**
  (no stable key, or genuinely ambiguous) → that becomes a `source_key` question (§9.2).
  If truly keyless, fall back to a deterministic hash of the identifying columns and
  **flag the fragility**.
- Write `project.yaml` (sources, source_key/key_status per table, target).

### 2 · Ingest  `[auto]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ ingest -s $SNAP
```
raw → normalized tables; computes `source_id` + `row_hash`; writes the immutable snapshot
+ `manifest.json` (counts). Review the counts.

### 3 · Profile  `[auto]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ profile -s $SNAP
```
per-column stats, candidate keys, value-set candidates, data-shape **signals** →
`snapshots/<v>/profile/*.json`. **Now load the matching topic files** (step 2 above).

### 4 · Wave-0 introspect  `[auto/AI]`
Read tenant reference data via Orion (`orion_client`) → `ledger/reference_data.json` +
a gap report (which list_options / cemeteries already exist vs. what the data needs).
Topics: `orion-load-gotchas` (`/api/v1`, `verify=False`, `paginate()` not `search()`),
`value-set-resolution`. A freshly-pulled tenant may be a near-empty shell — that is
normal; Wave-0b (stage 7) fills gaps.

### 5 · Auto-draft mapping  `[AI]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ map-draft -s $SNAP
```
then **REFINE** the draft:
- against the **target contract** (`contract/target_schema.json` + `overlay.yaml`) — every
  field must be a real contract field;
- using **codebase-memory-mcp** for structural questions about target entities (delegate
  to a sub-agent; get the conclusion back);
- using the loaded knowledge topics whose triggers match the profile;
- **resolve value-sets to real tenant `list_option` ids** — never invent an id; an
  unresolved value becomes a question (§9.2);
- **decide the multi-entity routing** of a flat register (`secondary_entities`) — the
  drafter defers this `[AI]` judgment to you. Decide it from the contract +
  `everspot-cheatsheet` (burial split: each row → Customer + Interment; grave = Property;
  multi-occupancy = 1 Property + N Interments). Topic:
  `single-flat-table-multi-entity`.
- Never clobber a settled ledger — the drafter writes to `.draft` sidecars when one exists.

### 6 · Discovery + THE QUESTION ROUND  `[user — the ONE pause]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ discover -s $SNAP   # exit 1 if any OPEN
```
one batched pass (profile + draft + DRY assemble + validate) → `runs/<v>/questions.json` +
`questions.md`. Each question carries a mandatory `proposed_answer`.
- **Present `questions.md` to the user.** They can **accept-all** or override specific items.
- Apply:
  ```bash
  $PY $PIPE/scripts/migrate.py -p $PROJ answer -s $SNAP --accept-all
  # or, with overrides:  ... answer -s $SNAP --answers runs/$SNAP/answers.json
  ```
- **HARD RULE (§9.5):** never proceed while any question is `open`. Gate strictly on the
  `discover`/`answer` exit code (`any_open`). Re-run `discover` after `answer` to confirm
  0 open.
- On a **settled ledger** (resume / v2) this round yields **0 open and does not pause** —
  auto-resolved questions are logged, not asked.

### 7 · Reference reconcile (Wave-0b)  `[auto]`
Create the **missing** list_options / cemetery via Orion
(`orion_client.create("list-options", …)`), **write the new ids back to the ledger**, and
re-resolve. Topic: `orion-load-gotchas` (Wave-0b writes), `value-set-resolution`. Closes:
read → find-missing → create → re-resolve → assemble clean.

### 8 · Cleanse  `[auto (+ held LLM tier)]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ cleanse -s $SNAP
```
deterministic primitives per cell → `{value, confidence, method, needs_llm}`. The **LLM
tier may run live on real client data** (per the user's standing authorization) — it
fires only when `ANTHROPIC_API_KEY` is present; with no key (or `MIGRATION_LLM_DRYRUN=1`)
residuals become exceptions and no call is made. Re-validate every LLM output through the
same Python library (the library, not the model, is truth).

### 9 · Assemble  `[auto]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ assemble -s $SNAP --full   # v1; v2+ defaults to delta-scoped
```
build the canonical graph (burial split, dedup parent property by external_id-action key,
partial dates calendar-validated, value-sets → resolved ids) → `runs/<v>/canonical/*.ndjson`,
validated against the contract inline. Unresolved cases land in `assemble_report.json`
(needs_attention) — never papered over.

### 10 · Validate + reconcile  `[auto]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ validate -s $SNAP    # exit 1 on BLOCKING failures
$PY $PIPE/scripts/migrate.py -p $PROJ reconcile -s $SNAP   # offline source→canonical conservation
```
schema + referential integrity + count conservation. **Gate: BLOCKING failures stop the
run** — a blocking failure that data cannot fill is itself a question (§9.2), so loop back
to the question round if one appears.

### 11 · Load  `[auto]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ load -s $SNAP            # default: print the PLAN only
$PY $PIPE/scripts/migrate.py -p $PROJ load -s $SNAP --live --insecure   # with --live: Orion load
```
wave-ordered, idempotent **upsert-by-external_id** (skip unchanged, PATCH CHANGED,
batch-create NEW + batch-register external_ids). The load is **checkpointed + resumable at
WAVE granularity** (SPEC §17): it records `waves_done` / `current_wave` into
`run_state.load_checkpoint` as it goes (resume is wave-level, NOT mid-wave; there is no
mid-wave chunk resume). **If a prior load crashed mid-way**, a fresh `migrate load`
RESUMES — it skips already-completed waves and re-runs the interrupted wave in full (safe
because the upsert + prefetched existing-external-ids map + the orphan-repair pass make a
re-POST idempotent: a model created-but-not-registered by the crashed run is detected and
registered, never duplicated), then finalizes the checkpoint on clean completion. A create
whose external-id register fails is reported as `failed` (for-retry), never counted as
created. `--live` only if the user passed it; otherwise print the plan. Topic:
`orion-load-gotchas` (atomic batches via `transactions.enabled`; cemetery JSON-string
fields; external-id `model_type`=FQCN). The Excel alternate:
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ emit -s $SNAP
```

### 12 · Post-load reconcile + report  `[auto]`
```bash
# only after a --live load:
$PY $PIPE/scripts/migrate.py -p $PROJ reconcile -s $SNAP --live --insecure   # canonical ↔ live tenant
$PY $PIPE/scripts/migrate.py -p $PROJ report -s $SNAP
```
`report` assembles the single consolidated `runs/<v>/REPORT.md` **from the artifacts**
(count conservation source→canonical→loaded, what loaded per entity, the questionnaire
answered, data-quality flags by kind, validation PASS/FAIL, post-load reconcile) and
guarantees `runs/<v>/needs_attention.json` at the run root (§15.1). It **also refreshes the
run-state surfaces**: `runs/<v>/RUN_LOG.md` (constant per-phase progress record) and the
project-level `MIGRATION_STATUS.md` (one upserted entry per snapshot — phases completed,
final entity counts, load status, open questions, validation PASS/FAIL). Run
`migrate status -s <v>` any time to (re)render `RUN_LOG.md` standalone. The user reviews:
`REPORT.md` (one screen) + `RUN_LOG.md` + `MIGRATION_STATUS.md` + the canonical NDJSON +
the emitted Excel.

### 13 · Next drop (v2+)  `[auto]`
```bash
$PY $PIPE/scripts/migrate.py -p $PROJ ingest -s v2
$PY $PIPE/scripts/migrate.py -p $PROJ delta  -s v2      # NEW/CHANGED/UNCHANGED/REMOVED on source_id
$PY $PIPE/scripts/migrate.py -p $PROJ assemble -s v2    # delta-scoped by default
$PY $PIPE/scripts/migrate.py -p $PROJ validate -s v2
$PY $PIPE/scripts/migrate.py -p $PROJ load    -s v2 [--live]
$PY $PIPE/scripts/migrate.py -p $PROJ report  -s v2
```
Only NEW/CHANGED reprocess; UNCHANGED reuse cached canonical + existing external_ids;
REMOVED are **never auto-deleted** (listed for user judgment). A clean v2 with no new
value-sets/columns is nearly a **one-command refresh**. Topic: `incremental-delta`.

---

## END-OF-RUN: reflect and self-improve (§11.2, §11.3 — THE POINT)

After a successful run, reflect on the **three §11.2 questions** and **append ONLY IF the
answer is GENERAL** (never client-specific — client facts live in that client's ledger
only):

1. **A reusable heuristic / Everspot gotcha?** → a `knowledge/topics/*.md` entry (+ an
   `INDEX.md` line with `triggers`). **Prefer to GRADUATE it** (the primary anti-bloat
   mechanism, §11.3):
   - a recurring **data-quality lesson** → a **validator** in the script library + a test,
     and **delete the prose**;
   - a recurring **question** → a **default in `core/ask-policy.md`** (no longer asked);
   - a recurring **transform** → a **library function + golden test**, referenced by name.
2. **A transform/validator worth keeping?** → `scripts/` + a **golden test** + a
   `scripts/LIBRARY.md` row (version-stamped — it feeds the transform cache).
3. **An error you hit?** → root-cause, fix it **generally**, add a
   `test_regression_<slug>` regression test, and a `LESSONS.md` entry.

Every self-edit = a **tracked diff** + a **one-line `CHANGELOG.md` rationale**. **NOTHING
ships to the general layer until the test suite passes:**
```bash
cd docs/migration-pipeline && ./.venv/bin/pytest -q
```
(§11.4 — the suite gates self-modification.) Strict separation: general learnings → the
shared layer; client facts → that client's ledger only — never crossed.

Finally, update the `data-migration-pipeline` file-memory entry with what landed.

---

## Binding rules (restated so every run obeys them — SPEC §18)

- **CLAUDE.md governs.** Use **codebase-memory-mcp** for structural code questions; use
  `tenancy()->initialize()/->end()` for tenant DB access.
- **Never `git checkout`** (ask the user). **Never `./vendor/bin/pint` without a path.**
- **The LLM tier may process real client data** (user's standing authorization) — **no
  PII prohibition, no `--authorize-llm` gate.** It runs live only when `ANTHROPIC_API_KEY`
  is set; otherwise it stays deterministic (no call). `MIGRATION_LLM_DRYRUN=1` is an
  optional cost/determinism switch, not a safety gate. Always re-validate LLM output
  through the Python library.
- **General fixes only** — client-specific decisions live in a project's ledger/mapping,
  never in `scripts/`.
- **NO Orion auth-guard bug exists** — never "fix" one; **never touch
  `AuthenticateTenantApiToken` / token generation / the Orion controllers without explicit
  approval.** The §13.3 Orion write-ergonomics items are **spec-and-approve, never silently
  built**.
- **Loads go into the sandbox, never the live client tenant.**
- **Changes stay uncommitted on the working branch unless the user asks for a PR** (base
  `dev`, never `main`).
- **Use sub-agents for context-heavy work**; return conclusions, not file dumps.
