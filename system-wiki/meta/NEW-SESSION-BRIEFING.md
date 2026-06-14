# Everspot System Wiki — New Session Briefing

**Last Updated:** 2026-06-12
**Status:** FIX-AND-VALIDATE pass complete, ready for bootstrap
**Your Role:** AI maintainer of the Everspot System Wiki

---

## What This Is

You are working in the **Everspot System Wiki** — an AI-maintained, searchable internal documentation repository for Everspot, a Laravel-based cemetery management application. The wiki's primary purpose is to document the data model (every Eloquent model) so that AI agents (like you) can answer questions about the system without constantly reading raw source code.

**Working Directory:** `/Users/cashkalina/code/everspot-brain/system-wiki/`
**Everspot Codebase:** `/Users/cashkalina/code/everspot` (READ-ONLY, separate repo)

---

## What's Been Built

### 1. Foundation & Specifications (Complete)

**meta/foundation.md** — The authoritative design specification (305 lines)
- Principles: AI-first, code is source of truth, self-contained on purpose
- Architecture: Two repos, canonical branch, schema snapshots, frontmatter-grep search
- Documentation standards: What goes in model docs, DRY/MECE, freshness tracking
- **§5.3: STI Convention** — How to document Single Table Inheritance patterns

**meta/conventions.md** — Naming, tags, completeness rules, model enumeration
- 14-tag controlled vocabulary (core, financial, customer, inventory, etc.)
- Completeness levels: complete/partial/stub (rule-based)
- Model enumeration rule: concrete Eloquent in `modules/*/Models/` and `app/Models/`
- **STI detection rules** — How to identify and document STI hierarchies

**meta/model-template.md** — Standard model documentation template
- Frontmatter fields (model, module, table, connection, source_paths, related, built_at, tags, completeness)
- Section structure (Overview, Schema, Properties, Relationships, Methods, Scopes, Events, Usage)
- **STI templates** — Separate patterns for base models vs. subtypes
- Human-content markers (`<!-- human:begin -->...<!-- human:end -->`)

**meta/commands.md** — Full specifications for 7 maintenance commands
- Generate, Sync, Snapshot-schema, Update, Audit, Review-coverage, Bootstrap
- Source_paths derivation, validation gates, human-note reconciliation, resumable sync

**CLAUDE.md** — Standing operating instructions for you (1.5 pages)
- Your role as single-writer maintainer
- Core rules: never overwrite human blocks, always re-derive source_paths, read Everspot via `git show origin/main:<path>`
- Pointer to foundation.md as authoritative spec

### 2. Schema Snapshots (Real Data)

**schema/central.json** — 18 tables from central database
- Users, tenants, domains, plans, features, permissions, roles, processor accounts, integrations
- Snapshot commit: `86b4328c28` (Everspot origin/main)
- Generated from throwaway database via standalone extractor

**schema/tenant.json** — 152 tables from tenant database
- Complete data model: transactions, customers, orders, properties, certificates, memorials, work orders, etc.
- Snapshot commit: `86b4328c28` (Everspot origin/main)
- Generated from throwaway tenant database

**How snapshots work:**
- Each JSON contains full table schema: columns (name, type, nullable, default), indexes, foreign keys
- Extracted from live, migrated databases using `tools/generate-schema-snapshots.php`
- Model docs render schema tables directly from these snapshots (guaranteed accurate)

### 3. Extraction Tooling (Operational)

**tools/generate-schema-snapshots.php** (396 lines, standalone)
- Boots Everspot Laravel framework in-process (require vendor/autoload + bootstrap/app)
- NO writes to Everspot repo (read-only)
- Extracts central schema from 'mysql' connection
- Extracts tenant schema via stancl/tenancy: `tenancy()->initialize($tenant)`
- Filters by database name (critical: Laravel's Schema::getTables() returns ALL databases)
- Skips framework tables (migrations, jobs, cache, telescope_*, nova_*, etc.)
- Usage: `php tools/generate-schema-snapshots.php --central schema/central.json --tenant schema/tenant.json --tenant-id <tenant-id>`

**tools/extract-model-skeleton.php** (700+ lines)
- Generates mechanical parts of model docs (frontmatter, properties, methods, relationships, scopes)
- Reads model source via `git show origin/main:<path>` from Everspot
- Handles inheritance (recursively parses parent classes, traits)
- Supports STI pattern (separates "Defined in X" vs "Inherited from Y" sections)
- Leaves AI-owned sections marked with `<!-- AI: ... -->` comments
- Usage: `php tools/extract-model-skeleton.php <model-path> > skeleton.md`

**tools/generate-snapshots.sh** (wrapper script)
- Automated extraction using standalone PHP script
- Auto-discovers tenant if not provided

### 4. Validated Model Documentation (4 Examples)

**modules/transaction/models/transaction.md** (STI base, tenant)
- 31-column schema table rendered from tenant.json
- Frontmatter: `sti: base`, `sti_subtypes: [Payment, Refund]`
- Owns full schema for shared `transactions` table
- Documents polymorphic relationships (transactionable, postable)
- Lists STI subtypes with discriminator values

**modules/transaction/models/payment.md** (STI subtype, tenant)
- Frontmatter: `sti: subtype`, `sti_base: Transaction`, `sti_discriminator: type=payment`
- Links to Transaction for schema (no duplicate table)
- Documents ONLY Payment-specific relationships/methods
- "See [Transaction](./transaction.md) for full schema"

**modules/customer/models/customer.md** (plain tenant model)
- 27-column schema table rendered from tenant.json
- Standard model documentation (no STI)
- Complete relationships, methods, scopes

**system/models/user.md** (central model)
- 17-column schema table rendered from central.json
- Central connection confirmed
- Two-factor authentication fields documented

**All 4 models validated:** 100% schema accuracy against real database structure.

---

## How the STI Convention Works

**Single Table Inheritance (STI)** is when multiple models share one database table, discriminated by a `type` column. Example: Transaction (base), Payment/Refund (subtypes) all use `transactions` table.

### Base Model (e.g., Transaction)
- **Frontmatter:** `sti: base`, `sti_subtypes: [Payment, Refund]`
- **Schema:** Renders FULL table schema from snapshot (all 31 columns)
- **STI Subtypes section:** Lists each subtype with its discriminator value
- **Owns:** The complete schema documentation for the shared table

### Subtype Model (e.g., Payment)
- **Frontmatter:** `sti: subtype`, `sti_base: Transaction`, `sti_discriminator: type=payment`
- **Schema:** Links to base model — "See [Transaction](./transaction.md) for full schema"
- **NO duplicate schema table** (would violate DRY)
- **Documents:** Only subtype-specific relationships/methods/scopes
- **STI Details section:** Documents discriminator value and global scope

### Detection Rule
Treat models as STI hierarchy when multiple concrete models resolve to the same table name (typically child's table matches parent's). Both base and subtypes count as separate models for coverage.

---

## The Directory Structure

```
system-wiki/
├── meta/                          # Wiki's own documentation
│   ├── foundation.md              # Authoritative design spec ⭐
│   ├── conventions.md             # Naming, tags, model rules
│   ├── model-template.md          # Standard model template
│   ├── commands.md                # Command specifications
│   ├── wiki-state.json            # Sync baseline (synced_through)
│   ├── migration-path-mapping.json # Central/tenant migration paths
│   ├── build-log.md               # Build history
│   ├── FINAL-BUILD-REPORT.md      # Initial build report
│   └── FIX-AND-VALIDATE-REPORT.md # Latest validation report ⭐
│
├── schema/                        # Real database snapshots
│   ├── central.json               # 18 central tables ⭐
│   └── tenant.json                # 152 tenant tables ⭐
│
├── tools/                         # Automation scripts
│   ├── generate-schema-snapshots.php  # Standalone extractor ⭐
│   ├── extract-model-skeleton.php     # Model skeleton generator
│   └── generate-snapshots.sh          # Wrapper script
│
├── modules/                       # Per-module documentation
│   ├── transaction/
│   │   └── models/
│   │       ├── transaction.md     # STI base example ⭐
│   │       └── payment.md         # STI subtype example ⭐
│   ├── customer/
│   │   └── models/
│   │       └── customer.md        # Plain tenant example ⭐
│   └── core/
│       └── models/
│           └── user.md            # Central example ⭐
│
├── system/                        # Cross-cutting system docs
│   ├── index.md
│   └── models/
│       └── index.md
│
├── index.md                       # Master entry point
├── CLAUDE.md                      # Your standing instructions ⭐
├── wiki.config.json               # Local config (gitignored)
└── wiki.config.example.json       # Config template
```

---

## The Proven End-to-End Pipeline

**snapshot → render → validate** is now PROVEN and operational:

1. **Snapshot Extraction:**
   - Standalone extractor boots Everspot framework without writes
   - Extracts real schema from live databases (central + tenant contexts)
   - Filters by database name (critical fix)
   - Produces accurate JSON snapshots

2. **Schema Rendering:**
   - Model docs render schema tables directly from snapshots
   - STI bases render complete shared table
   - STI subtypes link to base (no duplication)
   - 100% accurate column specs (names, types, nullable, defaults)

3. **Validation:**
   - All 4 validated models: schema matches snapshots exactly
   - Spot-checked against real database: 100% accuracy
   - Connection classification correct (central vs tenant)
   - STI convention properly applied

---

## Key Rules to Remember

### Database Safety (Non-Negotiable)
- **Everspot repo is READ-ONLY** — never write, stage, or commit files there
- Read Everspot files via `git show origin/main:<path>` (not working tree)
- When creating test databases, use obvious throwaway prefix (e.g., `wiki_scratch_*`)
- Never touch production/real databases

### Documentation Rules
- **Never overwrite human-authored content** (`<!-- human:begin -->...<!-- human:end -->` blocks)
- Always re-derive `source_paths` from current code (never trust stored)
- Schema sections render from snapshots (not hand-written)
- Follow model-template.md exactly
- Use controlled tag vocabulary (see conventions.md)

### STI Rules
- Base model owns and renders full schema
- Subtype model links to base, no duplicate schema
- Both count as separate models for coverage
- Detection: multiple models sharing same table name

### Connection Classification
- Determined by which snapshot contains the table
- Central tables → schema/central.json
- Tenant tables → schema/tenant.json

---

## What's NOT Done Yet

**These are intentionally incomplete** (FIX-AND-VALIDATE was targeted validation, not full bootstrap):

- Only 4 models documented (Transaction, Payment, Customer, User)
- 148+ remaining tenant models not documented
- Generate/Sync commands not implemented (specifications exist in commands.md)
- Bootstrap process not run
- System documentation (architecture.md, multi-tenancy.md, etc.) still placeholders

---

## If You Need to...

### Generate Schema Snapshots
```bash
# Ensure MySQL is running and Everspot is migrated
php tools/generate-schema-snapshots.php \
  --central schema/central.json \
  --tenant schema/tenant.json \
  --tenant-id <existing-tenant-id>
```

### Generate a Model Skeleton
```bash
# From Everspot model path, output mechanical sections
php tools/extract-model-skeleton.php modules/Customer/Models/Customer.php > temp.md
```

### Read Everspot Source
```bash
# Always use git show with canonical branch
cd /Users/cashkalina/code/everspot
git show origin/main:modules/Transaction/Models/Payment.php
```

### Check a Model's Table
```bash
# Look up in appropriate snapshot
jq '.tables.transactions' schema/tenant.json
jq '.tables.users' schema/central.json
```

### Find All Tenant Tables
```bash
jq -r '.tables | keys | .[]' schema/tenant.json
```

---

## Common Questions

**Q: Why two repositories?**
A: The wiki (this repo) documents Everspot (separate repo). Everspot is the source of truth; the wiki is its optimized projection for AI consumption. This keeps generated docs separate from application code.

**Q: Why snapshot schema instead of reading migrations?**
A: Migrations can have raw SQL, conditional logic, and cumulative complexity. Snapshots from live introspection are guaranteed accurate and complete.

**Q: Why the STI convention?**
A: Without it, Payment would duplicate Transaction's 31-column schema table (violates DRY). The convention makes Transaction own the schema once, and Payment link to it while documenting subtype-specific behavior.

**Q: What's the 'central' vs 'tenant' distinction?**
A: Everspot uses stancl/tenancy. Central DB has users, tenants, domains, plans (shared across all tenants). Each tenant has its own database with transactions, customers, orders, etc. (isolated per tenant).

**Q: Can I edit Everspot files?**
A: **NO.** Everspot repo is strictly READ-ONLY. Read via `git show origin/main:<path>`, never modify.

**Q: How do I know if a model uses STI?**
A: Look for multiple models with same table name, or child model's `$table` matching parent's. Check for `type` column and global scopes applying `WHERE type = '...'`.

---

## Your Next Likely Tasks

Based on where we are, you'll probably be asked to:

1. **Bootstrap remaining models** — Generate docs for the other 148+ tenant models
2. **Implement Generate command** — Using the proven pipeline (skeleton → AI fill → validate)
3. **Implement Sync command** — Incremental updates when Everspot code changes
4. **Document more STI hierarchies** — There are likely others beyond Transaction
5. **Build validation tools** — Check existing docs against current snapshots
6. **System documentation** — Fill in architecture.md, multi-tenancy.md, database.md placeholders

---

## Quick Reference

**Read this first:** meta/foundation.md (authoritative spec)
**Then read:** CLAUDE.md (your standing instructions)
**Latest status:** meta/FIX-AND-VALIDATE-REPORT.md (what's proven and working)
**Model examples:** modules/transaction/models/transaction.md (STI base), payment.md (STI subtype)
**Real data:** schema/tenant.json (152 tables), schema/central.json (18 tables)

**Key principle:** The code is the source of truth; the wiki is its optimized projection. Never invent, always derive.

---

**Welcome! You're maintaining an AI-first documentation system that's already proven to work. The pipeline is operational, the patterns are validated, and the foundation is solid. Let's build on it.**
