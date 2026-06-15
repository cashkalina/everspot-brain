---
title: CustomerImport
purpose: Spreadsheet import for Customer — valid columns, types, and rules
type: import
doc_kind: import-instance
parent_subsystem: system/imports.md
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
primary_source: modules/Customer/Imports/CustomerImport.php
source_paths:
  - modules/Customer/Imports/CustomerImport.php
  - app/Imports/BaseImport.php
primary_model: Customer
target_table: customers
registry_key: customer
implements: OnEachRow
---

# CustomerImport

Imports rows into **[Customer](../models/customer.md)** (`customers`). Creates or updates customers, and conditionally manages an attached Address, a Note, and a VeteranTag (with award/war relationships) based on per-row flags. Part of the [import subsystem](../../../system/imports.md) — see that doc for the upload→job→Excel flow and the `BaseImport` contract.

> **Registry key:** `customer` (select this type in the import UI).

## Columns

Spreadsheet header row uses these column names. **Required** reflects the literal `rules()` validation only — see **Conditional Rules** below for constraints the validator can't express. Blank cells are allowed for any non-required column.

| Column | Required | Type / constraint | Notes |
|---|---|---|---|
| `_delete` | No | boolean | Deletion flag (alternative to `delete`) |
| `delete` | No | boolean | Deletion flag (alternative to `_delete`) |
| `id` | No | FK → `customers.id` | Present = update / absent = create |
| `external_id` | No | string max 255 | Stored on Customer via `saveExternalId()` |
| `parent_id` | No | FK → `customers.id` | Empty string converted to null |
| `model_no` | No | string max 255 | — |
| `status` | No | enum-like string | One of `Customer::STATUSES` keys |
| `type_id` | No | FK → `list_options.id` | Empty string converted to null |
| `title_id` | No | FK → `list_options.id` | Empty string converted to null |
| `first_name` | No | string max 255 | — |
| `middle_name` | No | string max 255 | — |
| `last_name` | No | string max 255 | — |
| `maiden_name` | No | string max 255 | — |
| `suffix_id` | No | FK → `list_options.id` | Empty string converted to null |
| `company_name` | No | string max 255 | — |
| `contact_email` | No | email, max 255 | — |
| `contact_phone` | No | string max 255 | All non-digits stripped via `preg_replace` in `onRow` |
| `has_address` | No | boolean | If true, creates/updates an Address record |
| `address_external_id` | No | string max 255 | Stored on Address via `saveExternalId()` |
| `address_id` | No | FK → `addresses.id` | Used as the `updateOrCreate` key on the address |
| `line_one` | No | string max 255 | Address field; only processed if `has_address=1` |
| `line_two` | No | string max 255 | Address field; only processed if `has_address=1` |
| `line_three` | No | string max 255 | Address field; only processed if `has_address=1` |
| `city` | No | string max 255 | Address field; only processed if `has_address=1` |
| `state` | No | string (state code) | Converted to `state_id` via `State::where('code', ...)` if `has_address=1` |
| `zip_code` | No | string max 255 | Stored as `postcode` on the address; only if `has_address=1` |
| `country` | No | string (country name) | Converted to `country_id` via `Country::where('name', ...)` if `has_address=1` |
| `shipping` | No | boolean | Stored as `shipping_default`; only if `has_address=1` |
| `billing` | No | boolean | Stored as `billing_default`; only if `has_address=1` |
| `notes` | No | string | Creates a Note on the Customer if provided |
| `user_id` | No | FK → `users.id` | Used for note creation; falls back to `auth()->id()` if notes provided |
| `is_veteran` | No | boolean | If true, creates/updates a VeteranTag; if false, deletes it |
| `v_external_id` | No | string max 255 | Stored on VeteranTag via `saveExternalId()` |
| `v_country` | No | string (country name) | Veteran field; converted to `country_id` via `Country::where('name', ...)` |
| `v_branch_id` | No | FK → `list_options.id` | Veteran field; empty string converted to null |
| `v_branch_other` | No | string max 255 | Veteran field |
| `v_service_status_id` | No | FK → `list_options.id` | Veteran field; empty string converted to null |
| `v_service_status_other` | No | string max 255 | Veteran field |
| `v_rank_id` | No | FK → `list_options.id` | Veteran field; empty string converted to null |
| `v_rank_other` | No | string max 255 | Veteran field |
| `v_discharge_status_id` | No | FK → `list_options.id` | Veteran field; empty string converted to null |
| `v_discharge_status_other` | No | string max 255 | Veteran field |
| `v_awards_other` | No | string max 255 | Veteran field |
| `v_wars_other` | No | string max 255 | Veteran field |
| `v_unit` | No | string max 255 | Veteran field |
| `v_mos` | No | string max 255 | Veteran field |
| `v_start_date` | No | date | Veteran field |
| `v_end_date` | No | date | Veteran field |
| `v_additional_notes` | No | string | Veteran field |
| `v_awards` | No | comma-separated integer IDs | Veteran field; parsed and synced to `VeteranTag.awards` |
| `v_wars` | No | comma-separated integer IDs | Veteran field; parsed and synced to `VeteranTag.wars` |
| *(attribute keys)* | No | per attribute | Any [Customer](../models/customer.md) custom attribute may be set by adding a column named after its key. See [Attribute module](../../attribute/index.md). |

## Conditional Rules

Constraints enforced in code beyond `rules()` (these can fail the import even when columns validate):

- `contact_phone`: all non-digits stripped via `preg_replace`.
- Address is created/updated only if `has_address=1`; omitted if `has_address` is absent or 0.
- `state` and `country` lookups are performed only if `has_address=1` and the field has a value.
- `is_veteran` is only processed if the key is present in the row. If true, creates/updates a VeteranTag; if false, deletes it.
- `v_awards` / `v_wars`: comma-separated integers are parsed to an array, cast to integers, filtered for `> 0`, then synced; empty after filtering detaches all.
- Notes are created only if `notes` is provided; `user_id` defaults to `auth()->id()` if not supplied.

## Related Records

Beyond the primary model, this import also touches:

- Address — if `has_address=1`.
- Note — if `notes` provided.
- VeteranTag — if `is_veteran=true`.
- VeteranAward — synced if `v_awards` provided.
- VeteranWar — synced if `v_wars` provided.

## Behavior Notes

- **Upsert key:** `id` present = update / absent = create.
- **External ID:** `external_id` column stored via the HasExternalIds trait ([HasExternalIds](../../../system/traits/index.md#hasexternalids)) for idempotent re-imports (also `address_external_id` on Address and `v_external_id` on VeteranTag).
- Conditional address/veteran handling driven by the `has_address` and `is_veteran` flags.
- Phone numbers are normalized to digits only; `state`/`country` names are resolved to IDs for addresses.
- Comma-separated award/war IDs are synced to their many-to-many relationships; empty `parent_id`/`type_id`/`title_id`/`suffix_id` are converted to null.

## Source

Derived from `modules/Customer/Imports/CustomerImport.php` and `app/Imports/BaseImport.php` @ `origin/main` 86b4328. Re-derive `rules()` and `onRow()` on update — column lists live in source, not here.

<!-- human:begin -->
## Business Logic Notes
<!-- human:end -->
