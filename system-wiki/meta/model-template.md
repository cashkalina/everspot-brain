---
title: Model Document Template
purpose: Standard template for all model documentation
version: 2
last_updated: 2026-06-14
---

# Model Document Template

This is the standard template for all model documentation in the Everspot System Wiki. Copy this structure for every new model document.

The section skeleton is **deterministic**: the mandatory sections below are **always present**, even when empty (rendered as `_None._`), so an AI always knows where to look and can trust that a missing answer means "none" rather than "undocumented." Optional sections appear only when they have content. See "Section Floor vs. Ceiling" below and `meta/conventions.md`.

---

```markdown
---
model: Payment
module: Transaction
table: payments
connection: tenant            # central | tenant (derived from which snapshot holds the table)
primary_source: modules/Transaction/Models/Payment.php   # the single model class file
source_paths:                 # everything ELSE the doc derives from; excludes primary_source; recomputed every regeneration
  - app/Models/BaseModel.php
  - modules/Transaction/Models/Concerns/HasRefunds.php
  - modules/Transaction/Observers/PaymentObserver.php
  - app/Providers/EventServiceProvider.php
traits:                       # mechanical, from the model's `use` statements; links resolve via system/traits/index.md
  - HasRefunds
  - SoftDeletes
related_models: [Transaction, Refund, Customer]   # every distinct model targeted by a relationship method in this doc; powers reverse-relationship lookups
built_at: <main commit this document was generated against>
last_updated: 2026-06-14        # informational only; currency is built_at + sources + snapshot
completeness: complete         # complete | partial | stub (rule-based; see conventions)
deprecated: false              # if true, requires `successor:`
tags: [financial, payment, core]   # controlled vocabulary
---

# Payment

## Overview
What this model represents and why it exists, and its business role. AI-owned prose, 2-4 paragraphs.

## Schema
| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| amount | decimal(10,2) | No | - | Payment amount |
| deleted_at | timestamp | Yes | - | (via SoftDeletes — see [trait doc](../../system/traits/index.md#softdeletes)) |
| ...    | ...  | ...      | ...     | ...         |
<!-- rendered from schema/tenant.json; validated against it before commit -->

## Casts
- `amount` → `decimal:2`
<!-- $casts and Attribute-cast objects. Trait-contributed casts are OMITTED here and deferred to the trait doc. -->

## Attributes
**Fillable:** `[...]` (or `Guarded: []` — all mass-assignable)
**Hidden:** `[...]`
**Visible:** `[...]`
**Appends:** `[...]`
**Defaults (`$attributes`):** `status => pending`
<!-- mass-assignment + serialization visibility + default attribute values -->

## Accessors & Mutators
- `getFullNameAttribute(): string` — computed full name from first/middle/last
<!-- get*Attribute accessors, set*Attribute mutators, and computed/virtual attributes exposed via $appends -->

## Traits
- [HasRefunds](../../system/traits/index.md#hasrefunds) — enables refund tracking for this payment
- [SoftDeletes](../../system/traits/index.md#softdeletes) — payments are archived, never hard-deleted
<!-- one bullet per trait: link to the registry entry + one-line role THIS model gets from it -->

## Relationships
- `transaction()` — belongs to [Transaction](./transaction.md): the parent financial record.
- `customer()` — belongs to [Customer](../customer/models/customer.md): the paying customer.

## Scopes
- `completed(Builder $query)` — filters to `status = 'completed'`
<!-- query scopes AND global scopes; _None._ if there are none -->

## Events
- Dispatches `PaymentProcessed` on successful processing (`$dispatchesEvents`).
<!-- model events ($dispatchesEvents), booted()/creating()/etc. hooks defined ON the model. Observer-handled events are noted under Observers. _None._ if none. -->

## Observers
- `PaymentObserver` registered in `EventServiceProvider` — handles `created`, `updated`.
<!-- observers registered for this model (usually in a service provider). _None registered._ if none. -->

## Key Methods
- `process()` — processes the payment; public business-logic method.
<!-- public business-logic methods only — NOT accessors, scopes, or relationships. Signature + purpose, not bodies. -->

## Common Usage
```php
// representative examples
```

<!-- human:begin -->
## Business Logic Notes
Human-authored insight. Never overwritten by the agent. See §6.3.
<!-- human:end -->
```

---

## Section Floor vs. Ceiling

**Mandatory floor — always present, even when empty (`_None._`).** Their absence is a documentation defect, and an empty section is itself a valid answer (e.g. `## Observers` → `_None registered._` means the AI does not need to hunt service providers).

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
13. Business Logic Notes (human block — always present by rule)

**Optional ceiling — appear only when they have content.** Absence is unambiguous: no section means the feature is absent. When in doubt about one of these, consult the relevant `system/` doc rather than the model doc.

- **STI Details** — STI base/subtype models only (see below)
- **Routing** — only if `getRouteKeyName()` or custom route-model binding exists
- **Factory & Seeders** — pointer to factory/seeder paths, only if one exists
- **Multi-Tenancy Notes** — only when the model *deviates* from the default tenant pattern. The default tenant/central behavior is carried by the `connection:` frontmatter and documented once in `system/multi-tenancy.md`; per-model body notes are for exceptions only.

New model-specific sections may be added beyond this list when content demands. The floor guarantees determinism; the ceiling allows the doc to match reality.

---

## Template Notes

### Frontmatter Fields

- **model:** The PHP class name (e.g., `Payment`, `TransactionItem`)
- **module:** The module name if in `modules/`, or `System` if in `app/Models/`
- **table:** The database table name
- **connection:** `central` or `tenant` — **Determination algorithm:** (1) Check model's `$connection` property if explicit, (2) Check parent class if inherited, (3) Verify against snapshots (table must exist in exactly one snapshot), (4) If ambiguous, check module context (app/Models typically central, modules/* typically tenant)
- **primary_source:** The **single** model class file this document is about. Exactly one path. Body no longer repeats it as a `**Primary source:**` line.
- **source_paths:** All **other** files this document derives from — parent class, observers, event providers, relationship inverses, and any non-trait source. **Excludes** `primary_source` and **excludes** trait files (traits are tracked via the `traits:` field, and freshness unions all three). **Recomputed on every regeneration.**
- **traits:** The traits the model `use`s, by short name. Mechanical, from the model's `use` statements. Each resolves to a registry entry in `system/traits/index.md`, which links to the trait's deep doc in its owning module. Trait source files contribute to freshness via the registry's recorded paths.
- **related_models:** Every distinct concrete model targeted by a relationship method in this doc's Relationships section. **Derivation:** mechanical — collect the target model of every `hasMany`/`belongsTo`/`belongsToMany`/`morphMany`/etc. method. Exclude polymorphic abstract targets (e.g. "Notable") and external-package models not documented here. Powers reverse-relationship lookups, so it must stay in sync with the body.
- **built_at:** The `main` commit hash this document was generated against
- **last_updated:** Human-readable date (YYYY-MM-DD). Informational only; actual currency is `built_at` + `source_paths` + `traits` + snapshot
- **completeness:** `complete`, `partial`, or `stub` (see `meta/conventions.md`)
- **deprecated:** `true` if model has been removed from Everspot. If true, must include `successor:` field
- **tags:** 2-4 tags from controlled vocabulary (see `meta/conventions.md`)
- **sti:** (Optional) `base`, `subtype`, or omit for non-STI models
- **sti_subtypes:** (STI base only) Array of subtype model names, e.g., `[Payment, Refund, Credit]`
- **sti_base:** (STI subtype only) The base model name, e.g., `Transaction`
- **sti_discriminator:** (STI subtype only) The discriminator column and value, e.g., `type=payment`
- **successor:** (Required when `deprecated: true`) The model that replaces this one, if any

### Section Guidelines

**Overview:** AI-generated prose explaining the business purpose and role of this model. 2-4 paragraphs. (Connection and table are in frontmatter and no longer restated in the body.)

**Schema:** Rendered deterministically from the connection snapshot (`schema/central.json` or `schema/tenant.json`). Every column the snapshot reports appears here — including columns contributed by traits (e.g. `deleted_at` from `SoftDeletes`, audit columns), because they physically exist in the DB. Trait-owned columns keep a **provenance marker** in the Description column, e.g. `(via SoftDeletes — see trait doc)`, with a link to the registry. The behavior of the trait is documented in the trait doc, not here. Include a comment noting the source snapshot. Validated against snapshot before commit.

**If snapshot unavailable or model generation precedes schema extraction:** Use descriptive placeholder listing expected columns derived from code analysis (migrations, model casts, fillable array). Mark with comment `<!-- Schema pending real snapshot extraction -->` and set `completeness: partial`.

**Casts:** `$casts` and Attribute-cast objects defined on the model. **Trait-contributed casts are omitted** and deferred to the trait doc.

**Attributes:** Mass-assignment and serialization configuration: `$fillable` / `$guarded`, `$hidden`, `$visible`, `$appends`, and default attribute values (`$attributes`).

**Accessors & Mutators:** `get*Attribute` accessors, `set*Attribute` mutators, modern `Attribute` accessor/mutator methods, and the computed/virtual attributes exposed via `$appends`.

**Traits:** One bullet per trait. Format: `- [TraitName](../../system/traits/index.md#traitname) — what THIS model gets from it`. The capability itself is explained once in the trait's deep doc (linked from the registry), not re-explained per model. `_None._` if the model uses no documented traits.

**Relationships:** One bullet per relationship. Format:
`- relationshipName() — relationship type [LinkedModel](./path/to/model.md): description of what it represents`

For polymorphic relationships, document the abstract type and list known concrete types in prose:
`- commentable() — morphTo: The parent entity (may be Post, Product, or Customer)`

Every relationship whose target is a documented model **must** be linked. Forward links to not-yet-written docs are allowed (the path is correct even if the file is pending).

**Scopes:** Query scopes (`scope*` methods / `#[Scope]`) and global scopes. `_None._` if none.

**Events:** Model events defined *on the model* — `$dispatchesEvents`, and `booted()`/`creating()`/`saving()`/etc. hooks defined in the model class. Event handling that lives in an observer is noted under **Observers** with a cross-reference. `_None._` if none.

**Observers:** Observers registered for this model and where they are registered (usually a service provider, hence in `source_paths`), plus which lifecycle events they handle. `_None registered._` if none.

**Key Methods:** Public business-logic methods beyond standard Eloquent — **not** accessors, scopes, or relationships (those have their own sections). Show signature and purpose, not full body.

**Common Usage:** Representative code examples. Use PHP code blocks.

**Business Logic Notes:** Human-authored section. Content between `<!-- human:begin -->` and `<!-- human:end -->` is never overwritten by AI. This is where humans add insights not derivable from code.

### AI Maintenance Rules

1. **Never modify content between `<!-- human:begin -->` and `<!-- human:end -->`**
2. All other sections are AI-owned and regenerated freely
3. Render all mandatory sections every time; emit `_None._` (or section-appropriate equivalent like `_None registered._`) for empty ones — never silently drop a mandatory section
4. Re-derive `primary_source`, `source_paths`, `traits`, and `related_models` on every update by analyzing the model
5. Derive `connection` by checking which snapshot (`central.json` or `tenant.json`) contains the table
6. Validate Schema table against snapshot before committing; keep trait-column provenance markers
7. Stamp `built_at` with the current `main` commit hash
8. Update `last_updated` to current date

---

## STI (Single Table Inheritance) Templates

STI models add the optional `## STI Details` section and use the `sti*` frontmatter. The mandatory section floor still applies.

### STI Base Model Template

Use this template for the **base model** in an STI hierarchy (e.g., Transaction):

```markdown
---
model: Transaction
module: Transaction
table: transactions
connection: tenant
sti: base
sti_subtypes: [Payment, Refund, Credit]  # derived from code analysis
primary_source: modules/Transaction/Models/Transaction.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Transaction/Observers/TransactionObserver.php
  - app/Providers/EventServiceProvider.php
traits:
  - SoftDeletes
related_models: [Customer, Account]
built_at: abc123def456
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, transaction, core]
---

# Transaction

## Overview
Base model for all transaction types in the system. Uses Single Table Inheritance with subtypes Payment, Refund, and Credit sharing the `transactions` table, discriminated by the `type` column.

## Schema
| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint unsigned | No | - | Primary key |
| type | varchar(50) | No | - | STI discriminator (payment, refund, credit) |
| customer_id | bigint unsigned | No | - | Foreign key to customers |
| amount | decimal(10,2) | No | - | Transaction amount |
| status | varchar(20) | No | pending | Transaction status |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
<!-- rendered from schema/tenant.json -->

## Casts
- `amount` → `decimal:2`

## Attributes
**Fillable:** `['type', 'customer_id', 'amount', 'status']`

## Accessors & Mutators
_None._

## Traits
- [SoftDeletes](../../system/traits/index.md#softdeletes) — transactions are archived, never hard-deleted

## Relationships
- `customer()` — belongs to [Customer](../customer/models/customer.md): the customer who owns this transaction

## Scopes
_None._

## Events
_None._

## Observers
- `TransactionObserver` registered in `EventServiceProvider`

## Key Methods
- `process()` — abstract method implemented by subtypes to process the transaction

## STI Details
This model is the **base** of an STI hierarchy. It owns and renders the full shared-table schema above. Subtypes:
- [Payment](./payment.md) — `type=payment`
- [Refund](./refund.md) — `type=refund`
- [Credit](./credit.md) — `type=credit`

## Common Usage
```php
// Access all transactions
$transactions = Transaction::all();

// Access specific subtype
$payments = Payment::all(); // automatically scoped to type=payment
```

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
```

### STI Subtype Model Template

Use this template for **subtype models** in an STI hierarchy (e.g., Payment). Subtypes do NOT render the schema and document only subtype-specific content.

```markdown
---
model: Payment
module: Transaction
table: transactions  # same table as base
connection: tenant
sti: subtype
sti_base: Transaction
sti_discriminator: type=payment
primary_source: modules/Transaction/Models/Payment.php
source_paths:
  - modules/Transaction/Models/Transaction.php
  - modules/Transaction/Scopes/PaymentScope.php
traits: []
related_models: [Transaction, Customer, PaymentMethod]
built_at: abc123def456
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [financial, payment, transaction]
---

# Payment

## Overview
Represents a payment transaction. Part of the Transaction STI hierarchy, sharing the `transactions` table with other transaction types and automatically scoped to `type=payment`.

## Schema
**See [Transaction](./transaction.md) for the full shared-table schema.** (Subtypes do not render the schema table.)

## STI Details
- **Base model:** [Transaction](./transaction.md)
- **Discriminator:** `type=payment`
- **Global scope:** automatically filters to `WHERE type = 'payment'`

## Casts
Inherits casts from Transaction. Subtype-specific:
- `processed_at` → `datetime`

## Attributes
_None beyond base._

## Accessors & Mutators
_None._

## Traits
_None._

## Relationships
**Inherited from Transaction:**
- `customer()` — belongs to [Customer](../customer/models/customer.md)

**Payment-specific:**
- `paymentMethod()` — belongs to [PaymentMethod](./payment-method.md): the payment method used

## Scopes
- **Global scope:** `PaymentScope` automatically applies `WHERE type = 'payment'`

## Events
- Boot method sets `type = 'payment'` on new instances

## Observers
_None registered._

## Key Methods
- `process()` — processes the payment (implements the abstract method from Transaction)
- `refund()` — creates a Refund transaction for this payment

## Common Usage
```php
$payment = Payment::create([
    'customer_id' => $customer->id,
    'amount' => 100.00,
    'status' => 'pending'
]);
$payment->process();
$refund = $payment->refund();
```

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
```

### STI Template Selection Rules

**Use the base template when:**
- The model is the parent class in an STI hierarchy
- Multiple concrete models extend this model and share its table
- The model owns the shared table schema

**Use the subtype template when:**
- The model extends another model (STI base)
- The model shares a table with its parent
- The model has a discriminator value (typically in a `type` column)
- The model applies a global scope to filter to its discriminator value

**Use the standard template when:**
- The model does not participate in STI
- The model has its own unique table
