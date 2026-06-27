# LESSONS.md — the §11.2 7c failure → fix → test log

**Purpose.** Every error the pipeline has hit, root-caused and fixed **generally**, then
locked behind a **regression test** so that class of error cannot recur (§11 loop 7c).
This is the institutional record — an **audit log, never loaded in full as context**.
Recurring data-quality issues graduate into validators (7b); recurring questions graduate
into defaults (7a / the ledger).

**Format:** `error → root cause → general fix → regression test (the test that locks it)`.
Regression tests follow the convention `test_regression_<slug>` and live in
`tests/regression/`. (The test-suite workstream implements them; this file is the
institutional record they correspond to.)

---

## Seeded lessons (mined from prior runs — all general, no client data)

1. **Snapshot case-sensitivity dropped the whole source declaration**
   → the table-config map was keyed by the **raw** `project.yaml` table name but looked
   up by the **filename-normalized** name, so the declaration silently dropped → records
   fell back to a hash identity, `identity_fragile=True`, with no warning. A second
   case bug then matched the declared `source_key` against lowercased columns and raised
   "source_key columns not found".
   → **general fix:** `normalize_column_name()` applied at the `snapshot.py` boundary to
   **both** the declared table key **and** the `source_key`/`hash` columns.
   → `test_regression_snapshot_case_normalization`

2. **Unmatched source declaration deferred silently**
   → a declared `sources[].table` that matched no ingested table was silently ignored
   (the defer that masked lesson 1).
   → **general fix:** `snapshot.py` WARNs (stderr) and records `unmatched_source_declarations` in the manifest.
   → `test_regression_unmatched_source_declaration`

3. **`__NULL__` sentinel was raw NUL bytes**
   → the missing-key-component sentinel embedded raw `\x00` into source_ids/external_ids
   → crashed the xlsx emitter and left non-printable bytes in ids (bad for logs/URLs).
   → **general fix:** `identity._NULL_SENTINEL` = printable `"__NULL__"` (xlsx/URL-safe).
   → `test_regression_null_sentinel_printable`

4. **Partial dates violated the server's calendar + contract validity**
   → composed dates like Feb-29 (non-leap) / Apr-31, and orphan days with no month, which
   the server's `PartialDate` rejects.
   → **general fix:** `assemble._compose_partial_date` enforces calendar validity (drop the
   offending day) AND "day requires month" (orphan day → null); genuinely out-of-range
   values → null + a `data_quality` flag.
   → `test_regression_partial_date_calendar_validity`

5. **Non-atomic Orion batch caused duplicate inserts**
   → a batch-create that failed partway left orphan rows (no external_id); the per-record
   fallback then re-inserted them → duplicates (false multi-occupancy observed).
   → **general fix:** `config/orion.php` `transactions.enabled=true` → batches atomic → a
   failed batch rolls back → the per-record fallback is safe; on batch error, retry the
   chunk per-record to isolate the bad row.
   → `test_regression_non_atomic_batch_duplication`

6. **Canonical↔emit FK name mismatch dropped the property→interment link**
   → the emitter wrote the interment FK as `interment_space_ref` while canonical used
   `property_ref` → the link was silently dropped at emit (a latent template bug too).
   → **general fix:** `emit_excel.py` uses `property_ref` for the interment FK; the
   contract is the single name authority.
   → `test_regression_interment_property_ref_name`

7. **Silent joint-name collapse**
   → a cell holding two people (`"Robert & Phyllis"`) was collapsed to one person with no
   flag; `assemble` emitted 0 needs-attention for it, so a large 1→N gap was invisible at
   the question round.
   → **general fix:** a first-class `needs_attention` category — `assemble._apply()` flags
   every `needs_llm` cell (predicate = the explicit `cell.needs_llm` flag) carrying
   column/transform/reason but **no raw value** (PII-safe);
   `summarize_needs_attention()` groups them so structural cases surface.
   → `test_regression_joint_name_needs_attention`

8. **Standalone interment builder emitted a non-contract field (`interment_date`)**
   → `assemble._build_interment_table` (the BURIALS-only path used when an interment
   table declares **no** `secondary_entities`) wrote the interment date into a scalar
   `interment_date` that does **not** exist in the Target Contract. The §6.4 contract
   gate in `_emit` therefore raised `ContractViolation` ("unknown_field
   interment.interment_date") on **every** such row → the whole standalone-interment
   path was dead. (Found while building the §12 suite; the combined flat-register path
   was unaffected, which is why it stayed hidden.)
   → **general fix:** emit the date as the canonical partial-date field `doi` (date of
   interment); `normalize_date` already returns a `{year,month,day,estimated}` object,
   so it drops straight in and validates against the contract.
   → `test_regression_interment_doi_contract_field`

9. **Target model state machine silently overrode a POSTed status**
   → the loader POSTed `interment.status = completed` (correct: a historical burial IS
   completed) and Orion saved it, but every loaded interment went live as
   `awaiting-scheduling`. Root cause was on the **Everspot** side, not the payload:
   Interment status is a state machine — the `ManageIntermentStages` listener on
   `IntermentSaved` runs auto stage-progression on every save, and because a migrated
   historical record has no scheduled event the `completed` validation fails, so it walks
   the status **backward** step-by-step down to `awaiting-scheduling`. The field-level
   reconcile is what surfaced it (910 interment `status` mismatches with clean count
   conservation — present but wrong). **Lesson:** a target model can impose
   default/state-machine/observer behavior that overrides an explicitly-provided value;
   reconcile VALUES, not just presence, and when a value won't stick suspect server-side
   lifecycle hooks rather than the payload.
   → **general fix (corrected — use the platform field, not an invented one).** The first
   fix invented a virtual `migration_mode` flag; review caught that this **reinvented an
   existing platform field**: `is_manual` ("Manual / Enable to enter historical
   interment"), which every `StatusConfig` already honors — for a manual interment
   `CompletedConfig` uses relaxed manual validation (no scheduled event/space required),
   so `completed` is a valid terminal state and auto stage-progression never demotes it.
   **Everspot:** mark migrated interments `is_manual=true`; removed the invented
   `$isMigrating`/`markAsMigrating()`/`migration_mode` machinery (kept only
   `handleDefaultStatus()`'s invalid-status fallback as a general guard). Of the four
   operational `IntermentSaved` listeners, three are harmless once `is_manual` lands
   (fully reverted); the one that creates spurious records for a bulk historical import,
   `CreateIntermentEventFromDoiToi` (auto-creates a calendar event — the seeded tenant has
   `interment_sync_doi_with_event` ON), is gated on the **existing `is_manual` semantic**,
   not a bespoke flag. **Pipeline:** `project_payload` sets `is_manual=True` (a REAL
   column → part of the projection AND reconciled); `_correct_interment_status` re-applies
   `status`+`is_manual` to already-loaded rows that differ.
   **Meta-lesson:** before inventing a flag/field to bend target behavior, search the
   target model for an existing field with that exact semantic — the platform usually
   already models "this is a historical/manual record."
   → `test_orion_load_interment_status` (pipeline) + `IntermentStatusTest` (Everspot).

## Trust-layer hardening pass (2026-06-27 — adversarial five-axis review remediation)

10. **Count conservation printed "✅ Conserved" after real data loss (H1)**
    → root cause: validate/reconcile/report derived the "source" count from
    `_provenance.source_id` on the canonical records themselves, so a dropped source row
    left no record → no provenance → no count (`dropped` pinned at 0); the ingest
    manifest's true row totals were never read. The reconcile money row had the identical
    self-vs-self defect (left==right==total, a guaranteed pass).
    → **general fix:** `assemble.py` emits a per-source-row **disposition ledger**
    (produced / deduped_into / skipped_out_of_scope / errored); validate/reconcile/report
    compute conservation as `accounted == manifest.total_rows` with `unexplained_dropped`
    BLOCKING and legitimate fan-in/dedup informational; dropped the tautological offline
    money row. L7: fold `failed`/unknown load actions into the conserved verdict.
    → `test_regression_count_conservation_detects_drop`

11. **Duplicate inserts after an external-id register failure (H2)**
    → root cause: `_register` swallowed a failed `external-ids` batch yet still counted the
    records `created`, leaving orphan models with no external_id — invisible to the next
    run's prefetch → re-create → duplicates.
    → **general fix:** register-gated counting (an unregistered create is `failed`/for-retry,
    not created) + a pre-create **repair pass** that adopts orphan rows by the loader's own
    projected-payload signature and registers them in place. The real close (Everspot side):
    create/`batchStore` accept `external_id` and register it atomically via `HasExternalIds`
    in the same transaction (`RegistersExternalIdOnWrite` `performStore` override — the one
    seam shared by single + batch; pop non-column fields before fill; idempotency free from
    `addExternalId`'s `updateOrCreate`).
    → `test_regression_orion_register_failure_no_duplicate` (+ Pest `AtomicExternalIdRegistrationTest`)

12. **"Resumable load" overclaimed mid-wave resume it never did (H3)**
    → root cause: `chunks_done`/`chunk_cb` were written only in the batch-failure branch
    and never consulted; `load()` resume keyed only off `waves_done`.
    → **general fix:** removed the chunk machinery; the honest contract is wave-level resume
    + idempotent upsert (safe once H2 makes a wave re-POST non-duplicating). Make the claim
    match the code. `chunks_done` kept as a deprecated informational no-op.
    → `test_regression_orion_resume_contract_honest`

13. **accept-all settled an unresolved value-set past the one human gate (M1)**
    → root cause: a `value_set` `proposed_answer` dict carrying `None` tokens was taken as
    answered on accept-all → None written to `reference_resolution.missing` → null cells
    (violates §9.2 "never invent/null a list_option"). **Meta:** defend the human gate at
    the CONSUME boundary even when the producer's surface shape is constrained by other tests.
    → **general fix:** `answer.apply_answers` keeps any value_set answer containing a `None`
    OPEN; never accept-all's it.
    → `test_regression_acceptall_keeps_unresolved_valueset_open`

14. **A clean v2 scoped delta FAILED validation on a dangling ref to an unchanged parent (M2)**
    → root cause: validate resolved `*_ref` only within the current canonical set, but a
    scoped run emits only CHANGED+NEW — an in-scope child linking to an unchanged parent
    references a record that lives only in `ledger/external_ids.json`.
    → **general fix:** scoped validation (detected via `snapshots/<v>/delta.json`) seeds the
    ext→entity index from the external_id ledger in addition to the in-run canonical; a ref
    to an already-minted external_id of the right entity is satisfied. Full runs still flag
    a genuinely-missing parent; a wrong-entity ledger hit still dangles.
    → `test_regression_scoped_validate_ledger_ref_satisfied`

15. **interment.date silently set to the decedent's birthday (M3)**
    → root cause: `dob` was in the required-date chain with `is_fallback=False`.
    → **general fix:** use doi/dod only, else the flagged `1900-01-01` sentinel.
    → `test_regression_interment_date_no_dob_fallback`

16. **Records loaded under the wrong cemetery (M4)**
    → root cause: a silent `cems[0]` fallback on a cemetery-name miss.
    → **general fix:** create the named cemetery (logging a `reference_gap` when others
    exist), never silently mis-assign.
    → `test_regression_cemetery_no_silent_misassign`

17. **A generator's `--check` gated only one of its two committed artifacts (M5)**
    → root cause: the contract generator writes `target_schema.json` AND the DERIVED
    `canonical-record.schema.json`, but `--check` diffed only the first, so a stale derived
    schema passed CI. **Meta:** when a generator emits N committed files, `--check` must
    diff ALL N and fail-closed naming each drift; keep write and `--check` sharing one
    derivation function so they can't disagree.
    → `GenerateMigrationContractCheckTest` (offline) + the live conformance pytest

18. **Combinatorial candidate-key search was a latent DoS (M6)**
    → root cause: `combinations(all_cols, 2..5)` × full-table groupby on a wide no-early-key
    table; it "worked" only because real inputs found a key fast. **Meta:** a budget set
    ABOVE the worst-case enumeration is dead code — size it below.
    → **general fix:** top-K(15) by cardinality, distinct-product short-circuit, a hard combo
    budget shared with business-key completion, and a `candidate_keys_truncated` flag.
    → `test_regression_profile_keysearch_budget`

19. **"PII-aware" profiling merely volume-capped real PII (L1)**
    → root cause: capping to 10 samples still wrote 10 real names/phones/addresses into
    committed artifacts.
    → **general fix:** redact PII-signalled columns' samples + value-set keys with a stable
    short sha256 (cardinality structure survives, values don't); keep non-PII samples.
    → `test_regression_profile_pii_samples_redacted`

20. **"skipped" was treated as "resolved" at the gate (L3)**
    → root cause: `any_open` counted only `still_open`, so a skipped BLOCKING question slipped
    the gate.
    → **general fix:** skipping requires a rationale; `answer` exposes `skipped_blocking` +
    `gate_clear`, and `migrate answer`'s exit code gates on `gate_clear`.
    → `test_regression_skipped_blocking_question_surfaced`

21. **Schema validation built on the deprecated `jsonschema.RefResolver` (L4)**
    → root cause: both stages built validators with `RefResolver.from_schema` (removed in a
    future jsonschema → `AttributeError` AFTER canonical is written); the guard caught only
    `ImportError`.
    → **general fix:** migrate to the `referencing` library (shared `_make_ref_validator`);
    `RefResolver` is a fallback only; broaden guards to catch `AttributeError`. No version
    pin needed.
    → `test_regression_jsonschema_ref_without_refresolver`

22. **Question-id dedupe could drop a same-id OPEN question behind an auto-resolved one (L5)**
    → root cause: status-rank dedupe kept the higher-rank record; two distinct subjects
    sluggable to one id meant the OPEN one vanished.
    → **general fix:** `Question.subject_key` + `_dedupe_by_id` raise a loud collision rather
    than silently dropping.
    → `test_regression_discover_qid_collision_keeps_open`

23. **map_draft over-settled fuzzy matches and ignored truncated value sets (L6)**
    → root cause: a ≥90 fuzzy resolution settled at confidence 1.0 with no gap; a
    profiler-truncated value set was neither resolved nor gapped (unseen codes claimed
    complete). **Meta:** a successful list-option resolution is not automatically a certainty
    — read the confidence tier, not just `value is not None`; completeness ≠ "all SEEN codes
    resolved."
    → **general fix:** a fuzzy-only resolution keeps `is_gap=True` at confidence <1.0; a
    truncated value set emits a gap; only exact + complete sets settle at 1.0.
    → `test_regression_map_draft_fuzzy_and_truncated_gap`

## Generalization + honesty pass (2026-06-27 — items A1/A2/C1/C2/C3/B4a)

24. **A nullable DB column is not enough — a status state machine can still demote the record (C3)**
    → root cause: making `interments.date` nullable at the DB level didn't help, because a
    `StatusConfig` validation rule still marked `date` `required`; on save the interment
    failed its current-stage validation and `manageAutoProgression → moveToPreviousStage`
    walked it back down to `awaiting-scheduling`.
    → **general fix:** relax the shared `getManualValidationRules()` (`date` → `nullable`),
    not the per-stage non-manual rules, so a manual+completed undated interment stays put;
    normal app flow still requires a date.
    → `IntermentStatusTest` (null-date manual interment stays completed)

25. **A string-built external_id leaks whatever the source key contains (C2)**
    → root cause: `external_id` was `src:<entity>:<raw source key>`; when the client's key
    is a composite that includes names, the PII rode into every downstream surface
    (logs/URLs/external-ids table/load-report). **Meta:** don't parse source info back out
    of an external_id either — the only legitimate parse is the `src:<entity>:` segment.
    → **general fix:** token = `sha256(source_id)[:20]` (opaque, deterministic, stable);
    keep the readable `source_id` internal in the ledger; key any test/code off
    `_provenance.source_id`, never off the id string.
    → `test_regression_external_id_opaque`

26. **Atomic create+register still needs the orphan-repair pass (A1)**
    → root cause/insight: collapsing create+register into one transaction closes the
    common orphan window, but a crash *between* the row insert and the same-transaction
    external_id commit (or a pre-existing legacy unlinked row) can still leave an
    unlinked model; re-run safety depends on ADOPTING it, not duplicating.
    → **general fix:** send `external_id` inline on create, build id_map from the response,
    but KEEP `_repair_orphans`/`_register_orphans` as belt-and-suspenders.
    → `test_regression_orion_atomic_create_register`

27. **A self-healer and the reconcile that detects drift must share one oracle (A2)**
    → root cause/insight: if "what reconcile flags as drift" and "what corrections fix"
    use different projections/comparators, a fix may not clear the warning. **Meta:**
    removing a fabricated sentinel requires fixing the oracle in lockstep — `project_payload`
    IS the reconcile oracle, so a sentinel→null change there keeps post-load value-reconcile
    consistent (live null ≡ projected null). Idempotency falls out for free: a corrected
    field matches under `_norm`, so the next pass is a no-op.
    → `test_reconcile_apply_corrections`

28. **anthropic.Anthropic() constructs without a key and only fails on request (C1)**
    → root cause: a key-presence check *at client construction* is insufficient to prevent
    an accidental live call — the constructor succeeds; the network hit happens on
    `messages.create`.
    → **general fix:** short-circuit to the deterministic offline path BEFORE building any
    client when there's no `ANTHROPIC_API_KEY` and no explicit client passed — so default/CI
    runs physically cannot fire a call even after the PII prohibition was lifted.
    → `test_llm_policy_gate` (no-key stays deterministic, no call)

29. **The codebase path must not be hard-coded / relative-only (B4a)**
    → root cause: the pipeline is slated to move to its own repo, so an in-Everspot relative
    default would break once extracted.
    → **general fix:** a resolver with precedence env `EVERSPOT_CODEBASE_PATH` → `pipeline.toml`
    → default repo root; everything (codebase-memory-mcp/grep introspection + the artisan
    contract generator) reads `config.everspot_codebase_path()`.
    → `test_config_resolver`

> When a data-quality lesson here proves recurring and general, it **graduates** into a
> validator in the script library (and the corresponding prose topic shrinks to a
> pointer) — recorded in `CHANGELOG.md`. This log itself stays append-only.
