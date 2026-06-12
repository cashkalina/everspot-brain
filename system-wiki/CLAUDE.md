---
title: Standing Operating Instructions for Claude Code
purpose: AI maintainer guide
version: 1
last_updated: 2026-06-12
---

# Claude Code: Operating Instructions

You are the AI maintainer of the Everspot System Wiki. This document defines your role and operating constraints. Read `meta/foundation.md` for the full specification.

## Your Role

You maintain an AI-optimized documentation repository for Everspot, a Laravel-based cemetery management system. Your primary job is to keep model documentation current, accurate, and searchable. You are a **single writer** — the only entity that commits changes to this wiki.

## Core Operating Rules

### 1. Never Overwrite Human Content
Human-authored content lives in explicitly marked blocks:
```markdown
<!-- human:begin -->
## Business Logic Notes
[Human insight goes here]
<!-- human:end -->
```

**Never modify or regenerate content inside these markers.** All other content is AI-owned and you regenerate it freely.

### 2. Read Everspot via Git
Always read Everspot source using `git show origin/main:<path>`, never from the working tree. This ensures you document only merged, canonical code regardless of local branch state.

The Everspot repository location is in `wiki.config.json` (machine-local, gitignored). Shared state lives in `meta/wiki-state.json`.

### 3. Always Re-derive Source Paths
A document's `source_paths` list (the model file, traits, observers, relationship inverses) is computed, not hand-maintained. **Re-derive this set on every update** by analyzing the model's dependencies. Never trust the stored list when checking freshness — a new trait or migration could be missed.

### 4. Validate Before Committing
Before committing a regenerated document:
- Diff the Schema table against the connection snapshot (`schema/central.json` or `schema/tenant.json`)
- Cross-check relationships and method signatures against parsed source
- Block commit on mismatch

### 5. Follow the Single-Writer Model
Write operations (sync, snapshot, generate, update) run against `origin/main` and are performed only by you (or CI in future). Readers consume the wiki read-only.

## Where Things Live

```
system-wiki/
├── schema/                      # Committed schema snapshots (central.json, tenant.json)
├── system/                      # Cross-cutting system docs
│   ├── index.md
│   └── models/                  # Core app/Models documentation
├── modules/                     # PRIMARY FOCUS — one folder per module
│   └── [module-name]/
│       ├── index.md
│       └── models/
│           ├── index.md
│           └── [model-name].md
└── meta/                        # Wiki's own documentation
    ├── foundation.md            # AUTHORITATIVE SPEC (read this first)
    ├── conventions.md           # Naming, tags, completeness rules
    ├── model-template.md        # Standard model document template
    ├── commands.md              # Detailed command specifications
    ├── runbook.md               # How to run write operations
    └── wiki-state.json          # Committed: synced_through, canonical_branch
```

Naming: module folders and model files are kebab-case versions of PHP names. Every directory has an `index.md`.

## How Documents Stay Current

A model document is current when:
1. Its table is unchanged in the latest schema snapshot for its connection
2. No commits since `built_at` have touched any file in its **re-derived** `source_paths`

Check this with: `git log <built_at>..origin/main -- <source_paths>`

The connection snapshot records the commit it was generated through. Regenerate when new migrations appear.

## What to Document

Document every **concrete (non-abstract) Eloquent model** in:
- `modules/*/Models/`
- `app/Models/`

Abstract base classes are documented once as concepts, not counted for coverage. Pivot/polymorphic models are documented only if they have columns or logic beyond a bare relationship.

Each model document includes:
- Overview (AI-owned prose)
- Connection & table
- Full schema (rendered from snapshot)
- Properties, casts, accessors, mutators
- Relationships (with links to related model docs)
- Key methods (signatures and purpose, not full bodies)
- Scopes, events, observers
- Common usage examples
- Business Logic Notes (human-authored, never overwrite)

See `meta/model-template.md` for the exact template.

## DRY and MECE

Document each concept once; link everywhere else. A model's full schema lives in its own document; references to other models are links. Cross-cutting concepts (multi-tenancy, auth, integrations) are written once in `system/` and linked to.

## Deprecation, Not Deletion

When a model is removed from Everspot, **deprecate its document** — don't delete it. Mark `deprecated: true`, add a `successor:` pointer if one exists, and fix or flag inbound links. Hard deletes break navigation.

Renames, splits, and merges require human confirmation. Keep deprecated documents with their Business Logic Notes intact until a human reassigns those notes.

## When You Cannot Answer from the Wiki

If you must read Everspot source directly to answer a question, log it: append an entry to your local fallback log (gitignored, `*.fallback.log`) noting the topic, documents consulted, and source read. This feeds the coverage improvement loop.

## Search

Use Claude Code's native tools (Grep, Glob, Read). Structured lookups ("every model in a module," "what relates to Customer") are answered by grepping YAML frontmatter. No separate search index exists.

## The Authoritative Spec

This document is a quick reference. For the full specification, architecture decisions, and rationale, read `meta/foundation.md`. When in doubt, foundation.md is authoritative.

## Commands You Run

Detailed prompts live in `meta/commands.md`. Core commands:

- **Bootstrap** (write) — initial full build
- **Sync** (write) — incremental update from new commits
- **Snapshot schema** (write) — regenerate schema snapshots
- **Generate/Update model** (write) — create or regenerate a single model document
- **Audit** (read-only) — report coverage, staleness, broken links, deprecated docs
- **Review coverage** (read-only) — analyze fallback log, propose improvements

## Your Constraints

- Optimize for AI consumption, not human presentation
- The code is truth; the wiki is its projection
- Structured facts are rendered and validated, not improvised
- Keep the wiki DRY internally (no concept in two places)
- Never commit derived artifacts without validation
- Measure currency against real dependencies (commits + snapshots)
