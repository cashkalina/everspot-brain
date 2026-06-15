---
title: MergeCustomersImport
purpose: Spreadsheet import for Customer — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Customer/Imports/MergeCustomersImport.php
source_paths:
  - modules/Customer/Imports/MergeCustomersImport.php
  - app/Imports/BaseImport.php
primary_model: Customer
target_table: customers
registry_key: merge-customers
implements: OnEachRow
---

# MergeCustomersImport

Merges source customers into a target customer (`customers`). This is a **merge** operation, not an upsert — it creates no new customers and updates no columns directly; each row dissolves one or more source [Customer](../models/customer.md) records into a single target customer, reassigning their related records. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `merge-customers` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `merge_to_id` | Yes | FK → `customers.id` | Target customer (merge destination) |
| `merge_from_id` | No | FK → `customers.id` | Single source customer — alternative syntax to the numbered `merge_from_id_N` columns |
| `merge_from_id_N` | No | FK → `customers.id` | Numbered `merge_from_id_1`..`merge_from_id_10`; source customers merged into `merge_to_id` |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- `merge_to_id` is required.
- At least one source (`merge_from_id` or any numbered `merge_from_id_1`..`merge_from_id_10`) is required.
- Throws an Exception if `merge_to_id` is not found.
- Throws an Exception if any `merge_from_id` is not found.

## Related Records

Beyond the primary model, this import also touches:

- None directly named — the merge reassigns all related records of each source customer onto the target customer via the MergeCustomer action.

## Behavior Notes

- **Upsert key:** N/A — this is a merge, not a create/update. Each row merges its source customers into `merge_to_id`; no customer rows are created.
- **External ID:** Not supported.
- Deferred batch merge: per-row merges run with `skipOwnerFileSync=true`, then `batchSyncOwnerFiles` is called in `__destruct` after all rows are processed.
- Affected customer IDs are tracked across rows for the final batch owner-file sync.

## Source

Derived from `modules/Customer/Imports/MergeCustomersImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
