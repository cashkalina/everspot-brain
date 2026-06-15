# Non-Model Surface Inventory (Map Only — Charter Not Yet Expanded)

> **Generated:** 2026-06-15
> **Everspot source basis:** `origin/main` @ `78b496b`
> **Status:** **MAP ONLY.** This is a reconnaissance artifact, not a commitment to document these files. The wiki's charter (`CLAUDE.md`, `foundation.md`) is still **models + traits only**. Expanding to services/actions/etc. is a *charter change* — see §4 before acting.

---

## 1. The Gap, In One Line

The wiki documents **~152 models + ~30 traits ≈ 182 files**. The non-model PHP surface under `modules/` is **2,536 files across 41 kinds** — roughly **14× larger** than what's documented today. Expanding coverage is a strategic decision deferred to a later session; this file exists so we have the map ready when we make it.

---

## 2. Non-Model Surface by Kind

| Kind | Files | Modules | Doc value² | Priority³ |
|---|---:|---:|---|---|
| Actions | 175 | 27 | ⭐⭐⭐ High | **P1** |
| Services | 78 | 11 | ⭐⭐⭐ High | **P1** |
| Events | 91 | 21 | ⭐⭐⭐ High | **P2** |
| Listeners | 78 | 15 | ⭐⭐⭐ High | **P2** |
| Observers | 69 | 26 | ⭐⭐⭐ High | **P2** |
| Enums | 30 | 13 | ⭐⭐⭐ High | **P3** |
| Exceptions | 51 | 13 | ⭐⭐ Med | **P3** |
| Jobs | 23 | 7 | ⭐⭐ Med | P4 |
| Casts | 6 | 3 | ⭐⭐ Med | P4 |
| Rules | 10 | 4 | ⭐⭐ Med | P4 |
| Builders | 11 | 6 | ⭐⭐ Med | P4 |
| Collections | 12 | 4 | ⭐⭐ Med | P4 |
| Pivots | 4 | 3 | ⭐⭐ Med | P4 (may fold into model docs) |
| Contracts | 6 | 3 | ⭐⭐ Med | P4 |
| Data/DTOs + Data/Objects | 6 | 5 | ⭐⭐ Med | P4 |
| Notifications | 7 | 1 | ⭐⭐ Med | P4 |
| Mail | 3 | 2 | ⭐⭐ Med | P4 |
| Imports | 17 | 10 | ⭐ Low | P5 |
| Exports | 7 | 2 | ⭐ Low | P5 |
| Middleware | 12 | 9 | ⭐ Low | P5 |
| Policies | 50 | 26 | ⭐ Low | P5 |
| Console/Commands | 36 | 17 | ⭐ Low | P5 |
| Helpers | 5 | 5 | ⭐ Low | P5 |
| Http/Controllers | 110 | 31 | ⚪ Mechanical | P6 (skip?) |
| Livewire | 158 | 28 | ⚪ UI | P6 (skip?) |
| Components | 96 | 15 | ⚪ UI | P6 (skip?) |
| Http/Requests | 3 | 1 | ⚪ Mechanical | P6 |
| Http/Resources | 3 | 1 | ⚪ Mechanical | P6 |
| Providers | 99 | 35 | ⚪ Wiring | P6 (skip?) |
| Routes | 44 | 35 | ⚪ Wiring | P6 (skip?) |
| Definitions | 118 | 26 | ❓ Investigate | TBD⁴ |
| Formatters | 60 | 2 | ❓ Investigate | TBD⁴ |
| Support | 126 | 10 | ❓ Investigate | TBD⁴ |
| Implementations | 35 | 2 | ❓ Investigate | TBD⁴ |
| Core | 16 | 2 | ❓ Investigate | TBD⁴ |
| Traits | 98 | 14 | ⚠️ Partly done | see note⁵ |
| Defaults / Configurations / Permission Levels | 32 | — | ⚪ Config | P6 |
| **Other** | **751** | 30 | ❓ Unclassified | TBD⁴ |
| **TOTAL** | **2,536** | 35 | | |

² Rough documentation value — how much a reader learns about *how the system works* per file.
³ Priority reflects the user's stated ordering (see §4). Not yet a committed plan.
⁴ **TBD kinds need a classification pass before planning.** "Other" (751), Definitions (118), Support (126), Formatters (60), Implementations (35), Core (16) total ~1,106 files (44% of the surface) and are too coarsely bucketed to scope. The Definition module alone holds 197 "Other" + 118 Definitions + 59 Formatters — likely a metadata/schema engine that may warrant its own *system-level concept doc* rather than file-by-file coverage.
⁵ Traits: ~30 of 98 are already documented (the model-applied ones). The remaining ~68 are class-level/helper traits not yet in the registry — re-derive which are model traits before counting.

---

## 3. Per-Module Non-Model Footprint

Sorted by size. The top 3 (Common, Definition, Report) are **45% of the entire non-model surface** — they're infrastructure modules and should likely get *architecture/concept docs* rather than exhaustive file coverage.

| Module | Non-model files | Notable concentrations |
|---|---:|---|
| **Common** | 533 | Other 163, Components 58, Support 59, Livewire 33, Traits 28, Actions 22, Http 23, Services 16, Listeners 16 |
| **Definition** | 367 | Other 197, Formatters 59, Traits 30, Exceptions 15, Livewire 15 — *metadata engine* |
| **Report** | 246 | Other 82, Definitions 44, Services 31, Traits 16, Core 12, Livewire 12 — *reporting engine* |
| Trust | 103 | Services 11, Actions 11, Listeners 9, Definitions 8, Events 8 |
| Property | 97 | Other 30, Livewire 12, Actions 12, Http 9 |
| Transaction | 89 | Events 11, Other 28, Listeners 6, Livewire 6, Observers 5, Services 4 |
| Approval | 82 | Actions 13, Events 12, Components 8, Support 8 |
| Attribute | 81 | Other 20, Support 20, Actions 12, Http 8 |
| Interment | 60 | Listeners 15, Other 13, Support 7, Events 5 |
| Customer | 58 | Other 14, Livewire 9, Actions 7 |
| Mapping | 58 | Other 17, Livewire 9, Traits 8 |
| PaymentPlan | 52 | **Actions 26**, Other 10 |
| Order | 50 | Actions 10, Events 6, Livewire 5, Listeners 4 |
| Liability | 49 | Other 15, Actions 11, Listeners 5 |
| Recognition | 45 | Listeners 5, Actions 4, Services 3, Events 6 |
| ExternalSite | 45 | Other 17, Support 8, Livewire 5 |
| Program | 40 | Http 7, Livewire 4, Actions 4 |
| Event | 39 | Livewire 7, Other 11 |
| Accounting | 38 | Actions 5, Other 6, Exceptions 4 |
| Certificate | 38 | Other 7, Actions 5, Http 4 |
| AccountingSystem | 36 | **Implementations 19**, Jobs 4 |
| Product | 36 | Other 12, Http 4 |
| Memorial | 34 | Other 10, Http 4, Livewire 4 |
| Repetition | 32 | Support 11, Other 9 |
| WorkOrder | 32 | Other 11, Events 4, Livewire 4 |
| PaymentProcessor | 25 | **Implementations 16** |
| Cancellation | 24 | Events 4, Other 5 |
| Delivery | 19 | Other 5 |
| Autopay | 17 | Other 3 |
| Opportunity | 15 | Other 5 |
| Task | 15 | Other 2 |
| Signature | 8 | Http 5 |
| Subscription | 4 | — |
| Documentation | 3 | — |

---

## 4. When We Expand — Stated Priority Order

The user's direction (2026-06-15): **map now, scope the actual work later.** When we do expand, document in this order:

1. **P1 — Services & Actions** (253 files) — the core business-logic layer. "How the system actually works."
2. **P2 — Events / Listeners / Observers** (238 files) — the event graph: what fires when, side effects, cross-module reactions.
3. **P3 — Enums & Exceptions** (81 files) — domain states/types and failure modes. Small, high-clarity, cheap.
4. **Explicitly deprioritized:** Http/Controllers, Livewire, Components, Providers, Routes — the UI/wiring surface (~560 files). Largest, most mechanical, lowest semantic density. May be permanently out of scope.

**Before P1 can start, two prerequisites:**
- **(a) Classify the TBD buckets** (§2, note 4) — ~1,106 files in Other/Definitions/Support/Formatters/Implementations/Core are too coarsely labeled to plan against. A focused classification pass is the real next step.
- **(b) Decide the *unit* of documentation.** File-by-file (2,500 docs, huge sync burden) vs. one architecture/concept doc per module (~35 docs, narrative). The infrastructure modules (Common/Definition/Report) almost certainly want the latter. This is a charter design question for `foundation.md`, not just a volume question.

**Charter impact:** expanding beyond models requires new templates (`meta/` — e.g. `service-template.md`, `action-template.md` or `module-architecture-template.md`), new freshness rules (these files have different source sets than models), and a much larger Sync surface. None of that exists yet. Treat the expansion as a `foundation.md` revision, not just more generation work.

---

## 5. Relationship to the Model Roadmap

This file is the *breadth* question (what else exists). `meta/coverage-roadmap.md` is the *depth* question (are the models done — yes, 152/152). The two together: **models are complete; the non-model surface is mapped but uncommitted.** No action is taken on this file's contents until the charter is explicitly expanded in a future session.
