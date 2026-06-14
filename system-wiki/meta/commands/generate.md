---
title: Generate Command
purpose: Create a single new model document from scratch
last_updated: 2026-06-14
---

# Generate

**Purpose:** Create a single new model document from scratch.

**Operation type:** Write

**Inputs:**
- Model class path relative to Everspot repository root (e.g., `modules/Transaction/Models/Payment.php`)
- Implicit: `wiki.config.json` for Everspot repository location
- Implicit: Current `schema/central.json` and `schema/tenant.json`

**Preconditions:**
- Schema snapshots exist and are current
- Model class exists at the specified path in `origin/main`

**Process:**

### Derive primary_source, source_paths, and traits

The source set is computed, never hand-maintained, and is split across three frontmatter fields:

- **`primary_source`** — the single model class file (the input path). Exactly one path. Not repeated in `source_paths`.
- **`traits`** — the model's traits by short name (see step 2). Tracked separately so trait freshness resolves through the registry; **not** listed in `source_paths`.
- **`source_paths`** — every *other* file the document derives from (steps 3–5 below), excluding `primary_source` and excluding trait files.

1. **The model class itself** → `primary_source`.
2. **Traits used by the model** — parse the class via `git show origin/main:<model-path>`, extract `use TraitName` declarations in the class body, resolve each to its file path (follow PSR-4 namespace mapping from Everspot's `composer.json`), recursively including traits those traits use. Record the **short names** in the `traits:` frontmatter array, and ensure each has an entry in `system/traits/index.md` (creating registry entries + module-owned deep docs as needed — see [Ensure trait registry coverage](#ensure-trait-registry-coverage-lazy-trait-doc-build)). The resolved trait file paths feed freshness via the registry, not `source_paths`.
3. **Parent classes** — if the model extends a non-framework class (e.g., a custom base model in `app/Models/`), include that class file in `source_paths` and recursively include its parent. (A parent's *traits* are handled via the parent's own doc/registry entries, not duplicated here.)
4. **Observer registrations** — grep `app/Providers/EventServiceProvider.php` (and any other configured observer registration locations per `meta/conventions.md`) for this model's fully qualified class name. If registered, include the provider and the observer class file in `source_paths`.
5. **Inverse relationship sides** — for each relationship defined in this model that points to another model, include that related model's file in `source_paths`, because the inverse relationship's existence and name affect this model's documentation.

Store `source_paths` relative to Everspot repository root. Freshness checks union `primary_source` + `source_paths` + the trait paths resolved from `traits:`.

### Determine connection

The model's database connection (central or tenant) is derived, not specified manually:

1. Parse the model class. If it has an explicit `$connection` property, use that value.
2. If no explicit connection, use Everspot's default connection for the model's location (modules use tenant by default per Everspot conventions; `app/Models/User` and core auth models use central).
3. Cross-check: the model's `$table` property (or conventionally derived table name) must exist in exactly one schema snapshot. If the derived connection conflicts with snapshot membership, fail with an error requiring investigation.

Store the connection as `connection: central` or `connection: tenant` in frontmatter.

### Render schema

From the appropriate schema snapshot (`schema/central.json` or `schema/tenant.json`):

1. Locate the table entry matching the model's `$table` (or conventional table name derived from the model class name).
2. Render the Schema section as a markdown table with columns: Column, Type, Nullable, Default, Description.
3. For each column in the snapshot: extract name, type, nullable, default. Leave Description empty (to be filled by AI prose or left blank).
4. Include index information below the table (primary key, unique indexes, regular indexes).
5. Include foreign key constraints if present in the snapshot.

The rendered schema is deterministic — given the same snapshot, the output is identical. This section is validated before commit (see [Validation gate](#validation-gate)).

### Parse relationships, methods, attributes, scopes, events, observers

Via `git show origin/main:<model-path>` (and the observer provider from step 4 of [Derive primary_source, source_paths, and traits](#derive-primary_source-source_paths-and-traits)):

1. **Relationships** — parse method signatures returning relationship instances (`hasMany`, `belongsTo`, `belongsToMany`, `morphTo`, etc.). Extract the method name, relationship type, related model class, and any non-default foreign key or pivot table arguments.
2. **Key methods** — public business-logic methods only: **exclude** relationships, scopes, accessors/mutators (they have their own sections) and framework boilerplate. Include signature (name, parameters, return type if declared), exclude body.
3. **Scopes** — methods matching `scope*` pattern and `#[Scope]`-attributed methods, plus any global scopes (`addGlobalScope` / `ScopedBy`). Extract name and signature.
4. **Casts** — `$casts` and `Attribute`/cast-object definitions **declared on the model**. Exclude trait-contributed casts (deferred to the trait doc).
5. **Attributes** — `$fillable` / `$guarded`, `$hidden`, `$visible`, `$appends`, and default attribute values (`$attributes`).
6. **Accessors & mutators** — `get*Attribute` / `set*Attribute` methods and modern `Attribute`-return accessor/mutator methods; note the virtual attributes exposed via `$appends`.
7. **Events** — `$dispatchesEvents` map and model lifecycle hooks defined on the class (`booted()`, `creating()`, `saving()`, etc.).
8. **Observers** — from step 4 above: which observer class is registered for this model, where, and which lifecycle methods it implements.

### Denormalize related_models frontmatter

For reverse-relationship lookups via frontmatter grep:

1. From the parsed relationships, extract every distinct related model class name (short name, not fully qualified). Exclude polymorphic abstract targets and external-package models not documented here.
2. Store in frontmatter as `related_models: [ModelA, ModelB, ModelC]` in alphabetical order.

This allows an agent to find all models that relate to a given model by grepping `related_models:` in frontmatter, without parsing every model document's relationship prose. It must stay in sync with the body Relationships section.

### Ensure trait registry coverage (lazy trait-doc build)

For each trait in the `traits:` field:

1. Ensure an entry exists in `system/traits/index.md` (name anchor, one-line description, owning module, source path, link to deep doc). Add it if missing.
2. **Call [Generate-trait-doc](./generate-trait-doc.md) for the trait.** That command is **idempotent and existence-based**: it is a no-op when the trait's deep doc already exists and is current, and builds the deep doc from source otherwise. This is what makes trait docs build **lazily on first use** — the first model whose generation finds the deep doc missing triggers the build; later models that use the same trait just link to it. No model needs to know whether it is "first," so this is safe under resumable/batched Bootstrap and re-runs.
3. The model's `## Traits` section links each trait to its registry anchor with a one-line per-model role. Do not re-explain trait behavior in the model doc.

### Apply model-template.md

Using the structure defined in `../model-template.md` (foundation §5.2–5.3):

1. Populate frontmatter: model, module, table, connection, **primary_source, source_paths, traits, related_models**, built_at (current `origin/main` commit hash), last_updated (current date), completeness (determined by rule in `../conventions.md`), deprecated (false for new docs), tags (inferred or left for manual refinement), plus `sti*` fields if applicable.
2. Generate Overview section — AI-written prose. (Connection/table are frontmatter-only; no body Connection & Table section.)
3. Insert rendered Schema section from [Render schema](#render-schema), including provenance markers on trait-contributed columns.
4. Render the **mandatory floor** sections in order, emitting `_None._` (or `_None registered._` for Observers) where empty: Overview, Schema, Casts, Attributes, Accessors & Mutators, Traits, Relationships, Scopes, Events, Observers, Key Methods, Common Usage.
5. Add optional ceiling sections only when they have content: STI Details, Routing, Factory & Seeders, Multi-Tenancy Notes.
6. Insert human-content marker block:
   ```markdown
   <!-- human:begin -->
   ## Business Logic Notes
   <!-- human:end -->
   ```

### Validation gate

Before writing the file:

1. **Schema validation** — diff the rendered Schema section against the source snapshot table. Any mismatch (column missing, type wrong, nullability wrong) blocks the commit with a detailed error.
2. **Relationship validation** — for each documented relationship, verify the related model class exists in Everspot source and the inverse relationship is plausible (not necessarily named, but the relationship type is consistent — a `belongsTo` should have a `hasMany`/`hasOne` inverse).
3. **Method signature validation** — cross-check documented method names and signatures against parsed source.

Validation failures produce a detailed report. The command does not commit the document until all validations pass.

### Write and stamp

1. Write the document to the appropriate path: `modules/<module-kebab>/models/<model-kebab>.md` or `system/models/<model-kebab>.md`.
2. Stamp `built_at` with the current `origin/main` commit hash of the Everspot repository.
3. Report completion: document path, validation status, derived connection, number of source_paths.

**Outputs:**
- New `.md` file at the derived path
- Stamped with `built_at` commit and complete metadata

**Error handling:**
- Model class not found in `origin/main` — fail with clear error
- Table not found in either snapshot — fail, report which snapshots were checked
- Connection conflict (derived vs. snapshot membership) — fail, require investigation
- Validation failure — fail, report specific mismatches, do not write file
- Trait or parent class resolution failure — fail, report unresolved class
