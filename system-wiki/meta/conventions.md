---
title: Wiki Conventions
purpose: Naming, tags, completeness rules, model enumeration
version: 1
last_updated: 2026-06-12
---

# Wiki Conventions

This document defines the naming conventions, controlled tag vocabulary, completeness definitions, and model-enumeration rules for the Everspot System Wiki.

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

### Link Conventions
- Use relative links within the wiki: `[Payment](./payment.md)`, `[Customer](../customer/models/customer.md)`
- Links to Everspot source are written as paths relative to Everspot repo root: `modules/Transaction/Models/Payment.php`

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
All required sections are filled with meaningful content:
- Overview (non-trivial, explains business purpose)
- Connection & Table
- Schema (rendered from snapshot)
- Properties / Casts (if any exist in model)
- Relationships (all relationships documented with links)
- Key Methods (all public methods beyond standard Eloquent)
- Scopes / Events / Observers (if any exist)
- Common Usage (at least one example)

Business Logic Notes may be empty if no human insight has been added yet.

### partial
Document exists with basic structure, but one or more derived sections are missing or incomplete:
- Schema is rendered but relationships are not fully documented
- Some methods are documented but others are missing
- No usage examples provided
- Related models are listed but links are broken

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
   - Document trait behavior within the models that use them
   - Add traits to the model's `source_paths` for currency tracking

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
5. The resulting set is the coverage baseline

## Freshness and Currency

Completeness is about content depth. Freshness is about whether that content matches current code.

A document can be `complete` but stale (all sections filled, but built against old code). A document can be `partial` but current (incomplete coverage, but what's there is up to date).

The audit checks both dimensions independently.

## Evolution

This vocabulary and these rules will evolve as the wiki grows. When adding tags or refining rules:
- Update this document
- Regenerate affected documents to apply new tags
- Run audit to verify consistency
