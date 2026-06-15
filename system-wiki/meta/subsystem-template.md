---
title: Subsystem Document Template
purpose: Canonical shape for documenting a non-model subsystem (base class + concrete extensions + plumbing)
applies_to: system/<subsystem>.md
reference_example: system/imports.md
---

# Subsystem Document Template

The canonical shape for a **subsystem document** (foundation.md §5.6) — a bounded, cross-model *mechanism* such as the import subsystem, the event/listener graph, or a service family. Copy the structure below for each new subsystem doc; **do not** maintain a second copy of this shape anywhere else.

`system/imports.md` is the live reference example. When in doubt about depth or tone, read it.

## When to use this (vs. a model doc or a per-file stub)

- **Use a subsystem doc** when many classes share one base/contract and the *pattern* is the insight (imports, jobs of a kind, an event family). One doc covers the base + the registry of instances.
- **Don't** create a subsystem doc for a single class with no siblings — that's a one-off, document it where it's referenced or in the relevant module index.
- **Don't** create a per-file doc for each instance by default. Add thin per-instance stubs only when a recurring fallback-log signal (foundation §6.4) shows people need per-instance detail (e.g. exact column mappings).

## Frontmatter schema

```yaml
---
title: <Subsystem Name>
purpose: <one line — what mechanism this documents>
type: subsystem
doc_kind: subsystem-concept
built_at: <Everspot origin/main commit this was derived from>
primary_source: <path to the base class, if there is one>
source_paths:            # the bounded set that defines freshness (§3.4)
  - <base class>
  - <registry / factory that lists the instances>
  - <shared plumbing: job, livewire entry, dispatcher, …>
related_traits:          # traits the subsystem wires into (link by registry slug)
  - <trait-slug>
related_modules:         # modules whose code the subsystem reaches into
  - <Module>
review_after: <date>     # ONLY if the source set is genuinely unbounded; otherwise omit and rely on source_paths
status: pilot | active | deprecated
---
```

Freshness note: a subsystem maps to a **bounded** source set (base + registry + concrete classes), so it uses the `source_paths` range check like a model doc. Reach for `review_after` only when no honest path set exists. Re-derive `source_paths` on every update — a newly added instance must enter the set.

## Section order

1. **Title + one-paragraph intro** — what the mechanism does, in plain terms, and that it's a subsystem doc (note `status: pilot` while the pattern is still being proven).
2. **Architecture at a Glance** — a small ASCII flow (entry point → processor → base → targets) plus a 3–4 row table naming each moving part and its role.
3. **The Base Contract** — the abstract base / interface: what it implements and the shared helpers or hooks every instance reuses. **This is the reuse surface** — flag that changes here ripple to all instances. Link traits via `[[trait-slug]]`.
4. **The Standard Pattern** — the shape the majority of instances follow, as a short skeleton + the conventions that hold across them (upsert keys, idempotency fields, null-coercion, etc.). Keep instance-specific detail in source (DRY); say so explicitly.
5. **Registry of Concrete <Things>** — a table of every instance, re-derived from the canonical registry/factory (not the file listing). Columns typically: key/label, primary model `[[link]]`, module, also-touches. State the source-of-truth registry and the "re-derive on every update" rule.
6. **Variants & Exceptions** — instances that *don't* follow the standard pattern, called out so the mental model isn't over-applied. Hiding these is a trap.
7. **How to Find / Verify (for maintainers)** — the git/grep recipes to enumerate instances and the source set for freshness.
8. **Human block** — `<!-- human:begin --> ## Business Logic Notes … <!-- human:end -->`. Never regenerated.
9. **Future Work** *(optional)* — deferred stubs, cross-links to add, pattern-codification notes.

## Required invariants

- **DRY:** per-instance detail (mappings, rules, signatures) stays in source and is *linked/pointed to*, not duplicated here. Duplicate only what is genuinely cross-cutting.
- **Registry is truth:** the instance table derives from the code registry, never from a hand-kept list. An instance in source but not the registry is itself a finding worth noting.
- **Register the doc:** add a row under "Subsystem Documents" in `system/index.md`. That index — not foundation.md — is the canonical list of subsystem docs.
- **Variants are mandatory:** if any instance breaks the standard pattern, §6 must name it.
- **Human block present:** every subsystem doc carries a Business Logic Notes block, even if empty.
