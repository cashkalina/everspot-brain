---
title: Model Document Template
purpose: Standard template for all model documentation
version: 1
last_updated: 2026-06-12
---

# Model Document Template

This is the standard template for all model documentation in the Everspot System Wiki. Copy this structure for every new model document.

---

```markdown
---
model: Payment
module: Transaction
table: payments
connection: tenant            # central | tenant (derived from which snapshot holds the table)
source_paths:                 # computed; recomputed on every regeneration
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Models/Concerns/HasRefunds.php
  - app/Providers/EventServiceProvider.php
related: [Transaction, Refund, Customer]   # derived; powers reverse-relationship lookups
built_at: <main commit this document was generated against>
last_updated: 2026-06-12       # informational only; currency is built_at + sources + snapshot
completeness: complete         # complete | partial | stub (rule-based; see conventions)
deprecated: false              # if true, requires `successor:`
tags: [financial, payment, core]   # controlled vocabulary
---

# Payment

**Primary source:** `modules/Transaction/Models/Payment.php`

## Overview
What this model represents and why it exists. AI-owned.

## Connection & Table
Tenant · `payments`

## Schema
| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| ...    | ...  | ...      | ...     | ...         |
<!-- rendered from schema/tenant.json; validated against it before commit -->

## Properties / Casts
...

## Relationships
- `transaction()` — belongs to [Transaction](./transaction.md): the parent financial record.

## Key Methods
- `process()` — ...

## Scopes / Events / Observers
...

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

## Template Notes

### Frontmatter Fields

- **model:** The PHP class name (e.g., `Payment`, `TransactionItem`)
- **module:** The module name if in `modules/`, or `Core` if in `app/Models/`
- **table:** The database table name
- **connection:** `central` or `tenant` — derived from which schema snapshot contains the table
- **source_paths:** List of all files this document derives from (model, traits, observers, relationship inverses). **Recomputed on every regeneration.**
- **related:** List of model names this model has relationships to. Powers reverse-relationship lookups.
- **built_at:** The `main` commit hash this document was generated against
- **last_updated:** Human-readable date (YYYY-MM-DD). Informational only; actual currency is `built_at` + `source_paths` + snapshot
- **completeness:** `complete`, `partial`, or `stub` (see `meta/conventions.md`)
- **deprecated:** `true` if model has been removed from Everspot. If true, must include `successor:` field
- **tags:** 2-4 tags from controlled vocabulary (see `meta/conventions.md`)
- **sti:** (Optional) `base`, `subtype`, or omit for non-STI models
- **sti_subtypes:** (STI base only) Array of subtype model names, e.g., `[Payment, Refund, Credit]`
- **sti_base:** (STI subtype only) The base model name, e.g., `Transaction`
- **sti_discriminator:** (STI subtype only) The discriminator column and value, e.g., `type=payment`

### Section Guidelines

**Overview:** AI-generated prose explaining the business purpose and role of this model. Should be 2-4 paragraphs.

**Connection & Table:** Format as `Connection · table_name` (e.g., `Tenant · payments` or `Central · users`)

**Schema:** Rendered deterministically from the connection snapshot (`schema/central.json` or `schema/tenant.json`). Include markdown comment noting the source snapshot. Validated against snapshot before commit.

**Properties / Casts:** Document `$fillable`, `$guarded`, `$casts`, `$dates`, `$appends`, accessors (`get*Attribute`), and mutators (`set*Attribute`).

**Relationships:** One bullet per relationship. Format:
- `relationshipName()` — relationship type [LinkedModel](./path/to/model.md): description of what it represents

**Key Methods:** Public methods beyond standard Eloquent. Show signature and purpose, not full body.

**Scopes / Events / Observers:** Document query scopes, model events, and observer registrations.

**Common Usage:** Code examples showing typical usage patterns. Use PHP code blocks.

**Business Logic Notes:** Human-authored section. Content between `<!-- human:begin -->` and `<!-- human:end -->` is never overwritten by AI. This is where humans add insights not derivable from code.

### AI Maintenance Rules

1. **Never modify content between `<!-- human:begin -->` and `<!-- human:end -->`**
2. All other sections are AI-owned and regenerated freely
3. Re-derive `source_paths` on every update by analyzing model dependencies
4. Re-derive `related` by extracting all relationship target models
5. Derive `connection` by checking which snapshot (`central.json` or `tenant.json`) contains the table
6. Validate Schema table against snapshot before committing
7. Stamp `built_at` with the current `main` commit hash
8. Update `last_updated` to current date

---

## STI (Single Table Inheritance) Templates

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
source_paths:
  - modules/Transaction/Models/Transaction.php
  - modules/Transaction/Observers/TransactionObserver.php
related: [Customer, Account]
built_at: abc123def456
last_updated: 2026-06-12
completeness: complete
deprecated: false
tags: [financial, transaction, core]
---

# Transaction

**Primary source:** `modules/Transaction/Models/Transaction.php`

## Overview
Base model for all transaction types in the system. Uses Single Table Inheritance with subtypes Payment, Refund, and Credit sharing the `transactions` table, discriminated by the `type` column.

## Connection & Table
Tenant · `transactions`

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

## Properties / Casts
```php
protected $fillable = ['type', 'customer_id', 'amount', 'status'];
protected $casts = ['amount' => 'decimal:2'];
```

## Relationships
- `customer()` — belongs to [Customer](../customer/models/customer.md): the customer who owns this transaction

## Key Methods
- `process()` — abstract method implemented by subtypes to process the transaction

## Scopes / Events / Observers
- Observer: `TransactionObserver` registered in `EventServiceProvider`

## STI Subtypes
This model is the base for an STI hierarchy. See subtype documentation:
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

Use this template for **subtype models** in an STI hierarchy (e.g., Payment):

```markdown
---
model: Payment
module: Transaction
table: transactions  # same table as base
connection: tenant
sti: subtype
sti_base: Transaction
sti_discriminator: type=payment
source_paths:
  - modules/Transaction/Models/Payment.php
  - modules/Transaction/Scopes/PaymentScope.php
related: [Transaction, Customer, PaymentMethod]
built_at: abc123def456
last_updated: 2026-06-12
completeness: complete
deprecated: false
tags: [financial, payment, transaction]
---

# Payment

**Primary source:** `modules/Transaction/Models/Payment.php`

## Overview
Represents a payment transaction. Part of the Transaction STI hierarchy, sharing the `transactions` table with other transaction types and automatically scoped to `type=payment`.

## Connection & Table
Tenant · `transactions` (shared via STI)

**See [Transaction](./transaction.md) for full schema.**

## STI Details
- **Base model:** [Transaction](./transaction.md)
- **Discriminator:** `type=payment`
- **Global scope:** Automatically filters to `WHERE type = 'payment'`

## Properties / Casts
Inherits casts from Transaction base model.

Additional subtype-specific casts:
```php
protected $casts = [
    'processed_at' => 'datetime',
];
```

## Relationships
**Inherited from Transaction:**
- `customer()` — belongs to [Customer](../customer/models/customer.md)

**Payment-specific:**
- `paymentMethod()` — belongs to [PaymentMethod](./payment-method.md): the payment method used

## Key Methods
- `process()` — processes the payment transaction (implements abstract method from Transaction)
- `refund()` — creates a Refund transaction for this payment

## Scopes / Events / Observers
- **Global scope:** `PaymentScope` automatically applies `WHERE type = 'payment'`
- Boot method sets `type` attribute to `'payment'` on new instances

## Common Usage
```php
// Create a payment
$payment = Payment::create([
    'customer_id' => $customer->id,
    'amount' => 100.00,
    'status' => 'pending'
]);

// Process payment
$payment->process();

// Issue refund
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
