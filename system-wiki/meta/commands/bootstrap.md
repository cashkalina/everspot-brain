---
title: Bootstrap Command
purpose: Perform the initial full build of the wiki
last_updated: 2026-06-14
---

# Bootstrap

**Purpose:** Perform the initial full build of the wiki.

**Operation type:** Write

**Scope note:** This command is mentioned in foundation §8 but its full specification is deferred to implementation, as it is a combination of existing commands. The outline below establishes intent and structure.

**Inputs:**
- Runnable Everspot instance (for schema snapshots)
- `wiki.config.json` for Everspot repository location
- Empty or partially populated wiki repository

**Process (conceptual):**

1. **Generate schema snapshots** — run [Snapshot-schema](./snapshot-schema.md) for both connections.
2. **Enumerate all models** — use the coverage rule from [Audit › Coverage check](./audit.md#coverage-check) to list every in-scope model in `origin/main`.
3. **Generate documents for all models** — for each model, run [Generate](./generate.md). Process in batches if necessary for resumability. **Trait deep docs are built lazily here:** [Generate › Ensure trait registry coverage](./generate.md#ensure-trait-registry-coverage-lazy-trait-doc-build) calls [Generate-trait-doc](./generate-trait-doc.md) for each trait a model uses, which builds the deep doc the first time it is found missing and is a no-op thereafter. No separate trait-building phase is required — by the time every model is generated, every trait used by any model has a built-out deep doc and a registry row.
4. **Set initial synced_through** — record the current `origin/main` commit hash as the first baseline in `meta/wiki-state.json`.
5. **Validate the full set** — run [Audit](./audit.md) to check for any generation failures, broken links, or coverage gaps. Include trait-doc coverage: no registry row should still link to a `_pending_`/missing deep doc for a trait that is actually used.
6. **Commit the initial wiki** — commit all generated documents, snapshots, trait docs, and state.

**Resumability:**

Because generating hundreds of models may take significant time and is interruption-prone:

1. Track which models have been generated in a temporary state file (gitignored).
2. On resume, skip already-generated models.
3. Once all models are generated, remove the temporary state and commit the final result.
4. Trait docs need no separate resume tracking: [Generate-trait-doc](./generate-trait-doc.md) is existence/currency-based, so a resumed run that re-encounters an already-built trait is a safe no-op, and any trait whose build was interrupted mid-write is rebuilt on the next model that uses it.

**Outputs:**
- Full set of model documents
- Built-out trait deep docs (module-owned + framework) and a complete trait registry
- Schema snapshots for both connections
- `meta/wiki-state.json` with first `synced_through`
- Initial commit establishing the wiki baseline

**Error handling:**
- Same per-model error handling as [Generate](./generate.md)
- On failure, report failed models and allow resume
- Do not set `synced_through` until all models are successfully generated

**Deferred:** Exact command interface, progress reporting, and batch size tuning to be determined during implementation.
