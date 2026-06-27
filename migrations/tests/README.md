# tests/ — the §12 safety net

The test suite that gates every self-modification (SPEC §11.4) and every
schema/contract change. Pure-Python (pytest). **General/synthetic data only** — no
client data ever enters this tracked layer.

## Running

```bash
cd docs/migration-pipeline
./.venv/bin/pytest            # default: fully OFFLINE, green (live tests auto-skipped)
./.venv/bin/pytest -m live    # the live contract-conformance test (needs app + sandbox)
```

`conftest.py` puts `scripts/` on `sys.path` (the spine modules import each other by
bare name) and auto-skips `@pytest.mark.live` tests unless `-m live` is requested.

## Layout

| Dir | What it locks |
|---|---|
| `unit/` | Golden input→output for every cleansing primitive (`parse_name`, `normalize_date`, `normalize_phone`, `standardize_address`, `to_cents`, `digits_only`, `resolve_list_option`) + the contract validator — happy / edge / `needs_llm`-routing paths. |
| `regression/` | One `test_regression_<slug>` per fixed bug in `LESSONS.md` (7c). Each describes the bug and asserts the FIXED behavior so a reversion fails loudly. |
| `golden/` | End-to-end golden-file run of the SYNTHETIC `acme_synth` flat-register fixture: ingest → assemble → emit → dry-load, diffed against `golden/expected/`. |
| `conformance/` | Schema-conformance (canonical records vs `canonical-record.schema.json` + the target contract) and the **live** contract-conformance test (§6.5). |

## The golden fixture (`golden/fixtures/acme_synth/`)

A small synthetic flat register exercising: burial split (row → Property + Customer +
Interment), multi-occupancy parent dedup (rows sharing `PLOT_NO` → 1 property / N
interments), partial dates (0-placeholders → benign null; Feb-29-1990 non-leap → day
dropped + flagged), a value-set resolution (`ITYPE` BUR/CRE → `interment_type_id`
11/12), and an empty grave (property-only, no phantom children).

To re-freeze the golden after an INTENTIONAL output change, regenerate
`golden/expected/acme_synth/` from a spine run, **manually verify** the diff is
correct, and commit it.
