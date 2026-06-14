---
title: Generate-trait-doc Command
purpose: Create or regenerate the deep documentation for a single trait
last_updated: 2026-06-14
---

# Generate-trait-doc

**Purpose:** Create or regenerate the **deep documentation** for a single trait — the canonical, write-once explanation that the registry and every model's `## Traits` section link to. This is the unit of trait documentation; models never re-explain trait behavior.

**Operation type:** Write

**Invoked by:** [Generate › Ensure trait registry coverage](./generate.md#ensure-trait-registry-coverage-lazy-trait-doc-build) (lazily, per trait a model uses), [Sync › Map changes to affected documents](./sync.md#map-changes-to-affected-documents) (when a trait file changes), and directly/on demand. Bootstrap inherits it transitively through Generate.

**Inputs:**
- A trait, by short name or source path (e.g. `HasFiles` / `modules/Common/Traits/HasFiles.php`)
- `wiki.config.json` for the Everspot repository location

**Idempotency contract (critical for lazy build):**

This command is **existence-based and a no-op when the deep doc is already current**:

1. Resolve the trait's deep-doc path (see [Determine the deep-doc path](#determine-the-deep-doc-path)).
2. If the deep doc exists AND is current — its `built_at` has no intervening commits touching the trait's own `source_paths` (the trait file plus any traits/classes it depends on), re-derived from current `origin/main` — **return without writing.**
3. Otherwise, build/regenerate it.

Because callers only ever ask "ensure this trait's doc exists and is current," the order in which models are generated does not matter, and concurrent or resumed runs cannot double-build a stale doc into divergent states.

**Process:**

### Resolve and classify the trait

1. Resolve the short name to a source path via PSR-4 (Everspot `composer.json`), or take the given path.
2. Classify:
   - **Module-owned** — path under `modules/<Module>/Traits/` (or another module trait location). Owning module = `<Module>`.
   - **Framework/vendor** — e.g. `Illuminate\...\SoftDeletes`, `HasFactory`. No owning module.

### Determine the deep-doc path

- Module-owned → `modules/<module-kebab>/traits/<trait-kebab>.md` (e.g. `modules/common/traits/has-files.md`).
- Framework/vendor → `system/traits/<trait-kebab>.md` (no module owns it).

### Extract trait content from source

Via `git show origin/main:<trait-path>` (and recursively for traits/classes the trait itself uses):

1. **Purpose** — what capability the trait adds (AI prose).
2. **Contributed columns** — columns the trait expects/implies on a using model's table (e.g. `deleted_at`, `created_by`/`updated_by`/`deleted_by`, `model_no`). These are what model docs mark with `(via <Trait> — see trait doc)` provenance.
3. **Contributed casts** — casts the trait adds (deferred out of model docs into here).
4. **Contributed relationships** — relationship methods the trait defines (e.g. `createdBy()`), with links to target models where documented.
5. **Contributed scopes / global scopes** — query scopes the trait defines.
6. **Contributed methods** — public helper methods (signature + purpose).
7. **Configuration / contract** — interfaces the trait requires (e.g. `HasMedia`), properties a using model must define, boot behavior.
8. **Used by** — optional: note that the list of using models is discoverable by grepping `traits:` frontmatter (do not hand-maintain an exhaustive list).

### Write the deep doc and update the registry

1. Write the deep doc with frontmatter recording at minimum: `trait`, `owning_module` (or `framework`), `source_paths` (the trait file + dependencies), `built_at` (current `origin/main` hash), `last_updated`.
2. Update the trait's row in `system/traits/index.md`: ensure description, owning module, source path are accurate and the **Deep doc** column links to the written file (replace any `_pending_`).

### Validation gate

- Contributed columns named in the deep doc that claim to exist on tables are sanity-checked against the snapshots where applicable.
- Method/relationship/scope names are cross-checked against parsed trait source.

**Outputs:**
- Deep-doc `.md` at the resolved path, stamped with `built_at`
- Updated registry row in `system/traits/index.md`

**Error handling:**
- Trait not resolvable via PSR-4 — fail, report the unresolved name
- Trait source not found in `origin/main` — fail
- Validation failure — fail, report mismatches, do not write
