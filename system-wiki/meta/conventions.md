---
title: Wiki Conventions
purpose: Naming, tags, completeness rules, model enumeration, section structure, traits
version: 2
last_updated: 2026-06-14
---

# Wiki Conventions

This document defines the naming conventions, controlled tag vocabulary, section structure, trait-documentation rules, completeness definitions, and model-enumeration rules for the Everspot System Wiki.

## Naming Conventions

### File and Directory Names
- Use **kebab-case** for all file and directory names
- Convert PHP class names to kebab-case for file names
  - `Payment.php` → `payment.md`
  - `TransactionItem.php` → `transaction-item.md`
  - `HasRefunds.php` (trait) → documented in the model that uses it, not as a separate file

### Directory Structure
- Every directory must have an `index.md` file
- Module directory names match their Everspot module names in kebab-case
  - `Transaction` module → `modules/transaction/`
  - `CustomerManagement` module → `modules/customer-management/`

### Model Documentation Placement (Routing Rule)

Model documentation location depends on the model's source location in Everspot:

**app/Models/ → system/models/**
- Models in Everspot's `app/Models/` directory are documented under `system/models/<model-name>.md`
- Examples: `app/Models/User.php` → `system/models/user.md`
- Frontmatter: `module: System`
- These are core Laravel models used across the entire application (User, Tenant, Plan, Feature, etc.)
- Connection typically: `central` (but verify against schema snapshots)

**modules/*/Models/ → modules/*/models/**
- Models in Everspot's module directories are documented under their respective module directory
- Examples: `modules/Transaction/Models/Payment.php` → `modules/transaction/models/payment.md`
- Frontmatter: `module: Transaction` (matches the module name)
- These are module-specific domain models
- Connection typically: `tenant` (but verify against schema snapshots)

### Connection Determination Algorithm

When documenting a model, determine its database connection using this algorithm:

1. **Check explicit `$connection` property** in the model class
   - If present, use that value (e.g., `protected $connection = 'central';`)

2. **Check parent class** if model extends another model
   - Inherited `$connection` applies to child unless overridden

3. **Verify against schema snapshots** (authoritative)
   - Table must exist in exactly one snapshot (schema/central.json or schema/tenant.json)
   - If found in central.json → `connection: central`
   - If found in tenant.json → `connection: tenant`
   - If found in both: ERROR (table duplication issue in Everspot)
   - If found in neither: snapshot may be stale, regenerate

4. **Module context heuristic** (fallback if snapshots unavailable)
   - app/Models/* → typically `central`
   - modules/*/** → typically `tenant`
   - Mark `completeness: partial` until verified against snapshot

**BaseModel (abstract)**
- Abstract base classes are documented as concepts in `system/models/` but not counted for coverage

### Link Conventions
- Use relative links within the wiki: `[Payment](./payment.md)`, `[Customer](../customer/models/customer.md)`
- Links to Everspot source are written as paths relative to Everspot repo root: `modules/Transaction/Models/Payment.php`
- **Link every relationship target that is a documented model.** Forward links to not-yet-written docs are allowed and expected during bootstrap (the path is correct even if the file is pending). A bare model name where a link belongs is a defect.

## Model Document Section Structure

Model docs use a **deterministic section skeleton**: a fixed mandatory floor that is always present, plus an extensible optional ceiling. The canonical template and per-section guidance live in `meta/model-template.md`; this section states the *rules* the template embodies.

### The Mandatory Floor (always present)

These sections appear in **every** model doc, in this order, even when empty:

1. Overview
2. Schema
3. Casts
4. Attributes
5. Accessors & Mutators
6. Traits
7. Relationships
8. Scopes
9. Events
10. Observers
11. Key Methods
12. Common Usage
13. Business Logic Notes (human block)

**Rule:** A missing mandatory section is a documentation defect. An empty mandatory section is rendered with an explicit placeholder — `_None._`, or a section-appropriate variant such as `_None registered._` for Observers — because the empty state is itself a valid, trusted answer. This is what lets an AI conclude "this model has no observers" from `## Observers → _None registered._` instead of going to hunt service providers.

**Why these are split out.** Scopes, Events, and Observers each answer a distinct question and (especially Observers) are often registered *outside* the model file, so they get dedicated anchors rather than being lumped together. Casts, Attributes, and Accessors & Mutators are likewise split so mass-assignment/visibility, type-casting, and computed attributes are each locatable without scanning a combined block.

### The Optional Ceiling (present only when they have content)

These appear only when relevant. **Absence is unambiguous: no section means the feature is absent.** When in doubt about one of these for a given model, consult the relevant `system/` doc, not the model doc.

- **STI Details** — STI base/subtype models only (see STI rules below)
- **Routing** — only if `getRouteKeyName()` or custom route-model binding exists
- **Factory & Seeders** — pointer to factory/seeder paths, only if one exists
- **Multi-Tenancy Notes** — only when the model *deviates* from the default tenant pattern. Default tenant/central behavior is carried by the `connection:` frontmatter and documented once in `system/multi-tenancy.md`; per-model notes are for exceptions.

New model-specific sections may be added beyond this list when content genuinely demands. The floor guarantees determinism; the ceiling lets the doc match reality.

**Validation** is intentionally **not** in the skeleton for now (validation lives in FormRequests/rule classes outside the model). Revisit after bootstrap if it proves needed.

## Traits Documentation

Trait behavior is documented **once** and linked everywhere it is used, per the DRY rule (foundation §5.1). It is never re-explained inside each model doc.

### Three pieces

1. **Global registry — `system/traits/index.md`.** One entry per trait used in the codebase: the trait's short name (as a heading anchor), a one-line description, the owning module, and a link to the trait's deep doc. This is the single lookup table: model doc → registry → deep doc.

2. **Deep trait doc — in the owning module.** The full explanation of a trait lives with the module that owns it, e.g. `modules/common/traits/has-files.md` for `modules/Common/Traits/HasFiles.php`. It documents what the trait does, the columns/casts/scopes/relationships it contributes, and any required configuration. The registry links to it.

3. **Per-model `## Traits` section + `traits:` frontmatter.** Each model lists its traits (mechanically, from `use` statements) in the `traits:` frontmatter, and the body `## Traits` section gives one bullet per trait: a link to the registry entry plus a **one-line role specific to that model** (e.g. "HasFiles — stores deed scans"). No capability re-explanation.

### How trait effects surface in the model doc

- **Columns** a trait contributes (e.g. `deleted_at` from `SoftDeletes`, audit columns) **stay in the Schema table** — they physically exist in the snapshot, so the table remains complete and validatable — but carry a **provenance marker** in the Description column, e.g. `(via SoftDeletes — see trait doc)` linking to the registry.
- **Casts** a trait contributes are **omitted** from the model's Casts section and deferred to the trait doc.
- Behavior (scopes, events, methods, relationships) a trait contributes is documented in the trait doc, not duplicated per model; the model's `## Traits` link is the pointer.

### Freshness and source tracking

Trait files are tracked for currency via the `traits:` field (resolved to source paths through the registry), **not** by listing them in `source_paths`. Freshness checks union `primary_source` + `source_paths` + the trait source paths. Re-derive the trait list from the model's `use` statements on every regeneration.

## Controlled Tag Vocabulary

Tags are used in model document frontmatter to enable semantic grouping and search. Use tags from this controlled vocabulary:

### Core Tags
- `core` — foundational models used across the system (User, Tenant, Customer)
- `financial` — payment, billing, invoicing, accounting
- `customer` — customer data, relationships, demographics
- `inventory` — product catalog, stock, cemetery plots
- `reporting` — models primarily for reporting/analytics
- `integration` — models related to external integrations (QuickBooks, payment gateways)
- `admin` — administrative, configuration, or system management models
- `deprecated` — models marked for removal or already removed

### Domain-Specific Tags (Add as needed)
- `transaction` — transaction records and related models
- `location` — cemetery sections, plots, locations
- `service` — funeral services, ceremonies
- `contract` — contracts, agreements
- `document` — document management, file attachments

### Tag Usage Rules
- Every model should have 2-4 tags
- Use the most specific tag available
- Combine a domain tag with a functional tag when appropriate
  - Example: `tags: [financial, transaction, core]`
- Propose new tags if existing vocabulary is insufficient; update this document

## Completeness Definitions

Model documents are marked with one of three completeness levels in frontmatter:

### complete
All mandatory-floor sections are present and filled with meaningful content (empty ones explicitly rendered `_None._`), and:
- Overview (non-trivial, explains business purpose)
- Schema (rendered from snapshot; trait columns carry provenance markers)
- Casts / Attributes / Accessors & Mutators (each present; `_None._` where the model has none)
- Traits (each trait linked to the registry with a per-model role)
- Relationships (**every** relationship to a documented model is linked; `related_models:` frontmatter is in sync with the body)
- Scopes / Events / Observers (each present; `_None._` / `_None registered._` where applicable)
- Key Methods (all public business-logic methods beyond standard Eloquent)
- Common Usage (at least one example)

Business Logic Notes may be empty if no human insight has been added yet.

### partial
Document exists with the section skeleton, but one or more derived sections are missing or incomplete:
- Schema is rendered but relationships are not fully documented or not linked
- Some methods are documented but others are missing
- No usage examples provided
- Relationship targets are named but not linked, or `related_models:` is out of sync with the body
- A mandatory section is absent (rather than present-but-`_None._`)

### stub
Only frontmatter and minimal structure exist:
- Overview is generic or missing
- Schema may be rendered but no other sections have content
- Typically newly generated documents awaiting full sync

**Rule:** A model document should be marked `complete` only when a human or the sync process has verified all sections are filled. Default new documents to `stub` or `partial`.

## Model Enumeration Rules

These rules define what counts as a model for coverage purposes, per foundation.md §5.2.

### What Counts as a Model

Document every **concrete (non-abstract) Eloquent class** found in:
- `modules/*/Models/` (all module Models directories)
- `app/Models/` (core Laravel models)

### What Does NOT Count as a Model

Do not document (or count as coverage gaps):

1. **Abstract base classes**
   - Example: `abstract class BaseModel extends Model`
   - Document these once as concepts in `system/` if they define shared behavior, but do not count them as models requiring individual documentation

2. **Traits**
   - Example: `HasRefunds.php`, `Auditable.php`
   - Trait behavior is documented **once** in the global registry (`system/traits/index.md`) plus a deep doc in the trait's owning module — not re-explained inside each model that uses it (see "Traits Documentation" above)
   - List traits in the model's `traits:` frontmatter (not `source_paths`); they are tracked for currency via the registry

3. **Pivot models without columns or logic**
   - Bare pivot tables that only hold foreign keys (e.g., `customer_service` with only `customer_id` and `service_id`)
   - Do not document these unless they have:
     - Additional columns beyond the relationship keys
     - Casts, accessors, mutators, or scopes
     - Business logic methods
     - Timestamps or soft deletes

4. **Polymorphic intermediary models without logic**
   - Similar rule to pivots: document only if they carry columns or behavior beyond the polymorphic relationship

5. **Migration files, seeders, factories**
   - These are source inputs for schema and usage examples, not documentable models

### Special Cases

- **Soft-deleted models:** Document normally; add `deprecated: true` if they are no longer used in current code
- **Models in `database/` directory:** Do not document (these are typically migration-support classes)
- **Third-party package models:** Do not document unless they are extended or customized in Everspot

### Discovery Process

To find all models for coverage:
1. Glob `modules/*/Models/*.php`
2. Glob `app/Models/*.php`
3. Parse each file to check:
   - Extends `Model` or `Eloquent`
   - Not marked `abstract`
   - Not a trait (`trait` keyword)
4. Apply the pivot/polymorphic column check
5. Detect STI hierarchies (see STI Detection below)
6. The resulting set is the coverage baseline

### STI Detection and Documentation Rules

**Single Table Inheritance (STI)** occurs when multiple concrete models share the same database table, typically discriminated by a `type` column. Detect and document STI hierarchies as follows:

**Detection:**
- Treat models as an STI hierarchy when multiple concrete models resolve to the same table name
- Typically: child model's `$table` property matches its parent's table
- Or: child model has no explicit `$table` and inherits parent's table, but parent and child both share the same physical table

**Table ownership:**
- The **base model** (parent in the inheritance chain) owns the table
- The base model's document renders the full schema from the connection snapshot
- Subtype models reference the same table name in frontmatter but do NOT render the schema

**Model enumeration:**
- Both base and subtypes count as models for coverage purposes
- Each subtype is documented as a separate model file
- Example: Transaction (base) + Payment + Refund = 3 models documented, 3 coverage items

**Naming and discriminator:**
- Subtypes must clearly document their discriminator value (e.g., `type=payment`)
- The discriminator column and value are typically found in:
  - Global scopes applied in the subtype model
  - Boot method setting default attribute values
  - Explicit `$attributes` array in the model

**Frontmatter requirements:**
- Base model: `sti: base`, `sti_subtypes: [Payment, Refund, ...]` (derived from code)
- Subtype model: `sti: subtype`, `sti_base: Transaction`, `sti_discriminator: type=payment`
- Non-STI model: omit `sti` field (or `sti: none`)

## Freshness and Currency

Completeness is about content depth. Freshness is about whether that content matches current code.

A document can be `complete` but stale (all sections filled, but built against old code). A document can be `partial` but current (incomplete coverage, but what's there is up to date).

The audit checks both dimensions independently.

## Evolution

This vocabulary and these rules will evolve as the wiki grows. When adding tags or refining rules:
- Update this document
- Regenerate affected documents to apply new tags
- Run audit to verify consistency
