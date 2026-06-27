# Everspot Data-Migration Pipeline — Operating Instructions

You are operating the **autonomous data-migration pipeline** that ingests messy client
data and lands it in Everspot (a Laravel multi-tenant cemetery-management SaaS) via the
Orion REST API. This directory (`migrations/`, inside the `everspot-brain` repo) is the
**general layer** — the dataset-agnostic engine, knowledge, and tests. It was extracted
out of the Everspot repo so it travels independently.

## Read first
- **`SPEC.md`** — the binding design source of truth. Read the relevant sections before
  any non-trivial change (esp. §5 identity/memoization, §6 contract, §7 canonical artifact,
  §8 stages, §9 ask-policy, §10 incremental, §11 self-improvement, §12 tests, §13 Orion,
  §16 layout, §18 binding rules).
- **`.claude/commands/migrate.md`** — the `/migrate` orchestrator. Run `/migrate` from this
  directory to drive a migration end-to-end.
- Skim `CHANGELOG.md`, `LESSONS.md`, `scripts/LIBRARY.md`, `knowledge/INDEX.md` for current
  state and what exists.

## Three separate repos — don't conflate them
1. **`everspot-brain/`** — the repo you commit to; this pipeline is its `migrations/`
   subdirectory (so git paths look like `migrations/...`). The System Wiki is a sibling
   (`system-wiki/`).
2. **Everspot** — the Laravel codebase you load INTO. A **separate** repo whose path is in
   `pipeline.toml` (machine-local). The pipeline **reads** it (codebase-memory-mcp / grep
   self-introspection) and runs `php artisan migration:generate-contract` there; the Orion
   write controllers, the `HasExternalIds` registration, the nullable `interments.date`
   migration, and the contract-generator command all live in Everspot.
3. **Per-client project data** — lives OUTSIDE the repo (gitignored `projects/` or any
   path you pass with `migrate -p <dir>`). Client data never enters this repo.

## The Everspot codebase path (machine-local)
`scripts/config.py` resolves it: env `EVERSPOT_CODEBASE_PATH` → `pipeline.toml`
(`everspot_codebase_path`) → a default. Copy `pipeline.example.toml` → `pipeline.toml` on a
new machine. It must point at a checkout that HAS the migration PHP (the
`migration:generate-contract` command, atomic Orion register, nullable `interments.date`).

## Environment / setup
Rebuild the venv (not committed):
```bash
cd migrations && python3 -m venv .venv
./.venv/bin/pip install pandas pyarrow pyyaml openpyxl python-dateutil nameparser \
  phonenumbers rapidfuzz requests anthropic jsonschema pytest
./.venv/bin/pytest -q            # the offline safety net must stay green
```
The contract generator is invoked via `config.generate_contract_argv(...)` (it passes
`--pipeline-root` so the Everspot-side command writes the contract back into THIS pipeline).

## Binding rules (SPEC §18 — do not violate)
- **General fixes only** — client-specific decisions live in a project's ledger/mapping,
  never in `scripts/`.
- **Test-first / test-gated** — every behavior change gets a regression test; the offline
  suite must pass before anything ships (it gates self-modification, §11.4).
- **Orion auth is off-limits** — there is no auth-guard bug; never touch
  `AuthenticateTenantApiToken`, token generation, or guards.
- **Never `git checkout`** in the Everspot repo (you only read it); never run
  `vendor/bin/pint` without a path when editing Everspot PHP.
- **LLM tier** — AI may process real client data per the user's standing authorization;
  `MIGRATION_LLM_DRYRUN` is an optional cost/determinism switch. With no `ANTHROPIC_API_KEY`
  the tier stays deterministic (cannot call). Re-validate every LLM output through the library.
- Record self-edits in `CHANGELOG.md`; institutionalize each fixed defect in `LESSONS.md`
  with a `test_regression_<slug>`; add new utilities to `scripts/LIBRARY.md` with a test.
