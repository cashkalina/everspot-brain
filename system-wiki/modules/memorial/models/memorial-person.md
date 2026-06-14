---
model: MemorialPerson
module: Memorial
table: memorial_people
connection: tenant
primary_source: modules/Memorial/Models/MemorialPerson.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Common/Casts/PartialDateCast.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Traits/HasByUserFields.php
  - modules/Customer/Models/Customer.php
  - modules/Interment/Models/Interment.php
  - modules/Memorial/Models/Memorial.php
  - app/Providers/EventServiceProvider.php
  - modules/Memorial/Providers/MemorialServiceProvider.php
traits:
  - HasByUserFields
  - HasPartialDateScopes
  - SoftDeletes
related_models: [Customer, Interment, ListOption, Memorial]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, customer]
---

# MemorialPerson

## Overview

The MemorialPerson model represents an individual person commemorated on a [Memorial](./memorial.md). Each record links a memorial to a specific person, capturing their name, birth and death partial dates, inscription text, and display order. The person may optionally be linked to an existing [Customer](../../customer/models/customer.md) record and to an [Interment](../../interment/models/interment.md) record.

When a memorial has multiple people, the `order` column controls the display sequence. The `full_name` accessor composes the name from `first_name`, `middle_name`, `last_name`, and `suffix` for display in the memorial's derived `display_name` (see `Memorial::generateDisplayName()`).

Birth and death dates are stored as separate year/month/day component columns (partial dates), following the same pattern used elsewhere in Everspot (e.g. customer DOB). The `PartialDateCast` handles composing these columns into a single value for `birth_date` and `death_date` casts.

The model carries soft deletes and audit user stamps via traits.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| memorial_id | bigint | No | - | FK → memorials: the parent memorial |
| customer_id | bigint | Yes | - | FK → customers: optional link to a customer record |
| interment_id | bigint | Yes | - | FK → interments: optional link to an interment record |
| first_name | varchar | Yes | - | Person's first name |
| middle_name | varchar | Yes | - | Person's middle name |
| last_name | varchar | Yes | - | Person's last name |
| suffix_id | bigint | Yes | - | FK → list_options: name suffix (Jr., Sr., etc.) |
| birth_date_year | smallint | Yes | - | Birth date year component (partial date via [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes)) |
| birth_date_month | tinyint | Yes | - | Birth date month component (partial date) |
| birth_date_day | tinyint | Yes | - | Birth date day component (partial date) |
| birth_date_estimated | tinyint | No | 0 | Whether the birth date is estimated |
| death_date_year | smallint | Yes | - | Death date year component (partial date) |
| death_date_month | tinyint | Yes | - | Death date month component (partial date) |
| death_date_day | tinyint | Yes | - | Death date day component (partial date) |
| death_date_estimated | tinyint | No | 0 | Whether the death date is estimated |
| inscription | text | Yes | - | Inscription text to be engraved on the memorial |
| order | int | No | 0 | Display order among this memorial's people |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `memorial_id` → `memorials.id`; `customer_id` → `customers.id`; `interment_id` → `interments.id`; `suffix_id` → `list_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** `memorial_id`, `customer_id`, `interment_id`, `suffix_id`, `order`; single-column and composite year/month indexes on `birth_date_year` and `death_date_year`; FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

## Casts

- `birth_date` → `PartialDateCast::class.':birth_date'` — composes `birth_date_year` / `birth_date_month` / `birth_date_day` into a partial-date value (see `modules/Common/Casts/PartialDateCast.php`)
- `death_date` → `PartialDateCast::class.':death_date'` — composes `death_date_year` / `death_date_month` / `death_date_day` into a partial-date value

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `getSuffixAttribute(): ?string` — name of the related suffix [ListOption](../../common/models/list-option.md) (via `suffixOption?->name`); null if no suffix
- `getFullNameAttribute(): string` — composed name from `first_name`, `middle_name`, `last_name`, and `suffix`, joined with spaces and trimmed; filters out nulls/empty values

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) — query scopes over the `birth_date_*` and `death_date_*` partial-date component columns
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — memorial people are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `memorial()` — belongs to [Memorial](./memorial.md): the parent memorial this person appears on
- `customer()` — belongs to [Customer](../../customer/models/customer.md) (`customer_id`): the linked customer record (optional; standalone people may not have a customer)
- `interment()` — belongs to [Interment](../../interment/models/interment.md) (`interment_id`): the linked interment record (optional)
- `suffixOption()` — belongs to [ListOption](../../common/models/list-option.md) (`suffix_id`): the name suffix option

## Scopes

_None._

Partial-date query scopes over the birth and death date component columns are contributed by [HasPartialDateScopes](../../../system/traits/index.md#haspartialdatescopes) (see trait doc).

## Events

_None._

## Observers

_None registered._ (The parent `MemorialServiceProvider` registers an observer on `Memorial` only; `MemorialPerson` has no observer.)

## Key Methods

_None beyond standard Eloquent._ (The `getSuffixAttribute()` and `getFullNameAttribute()` accessors are listed in [Accessors & Mutators](#accessors--mutators).)

## Common Usage

```php
// Add a person to a memorial
$person = $memorial->people()->create([
    'first_name'       => 'Jane',
    'middle_name'      => 'Marie',
    'last_name'        => 'Smith',
    'suffix_id'        => $suffixOption->id,
    'customer_id'      => $customer->id,
    'interment_id'     => $interment->id,
    'inscription'      => 'Beloved mother and grandmother',
    'order'            => 1,
    'birth_date_year'  => 1940,
    'birth_date_month' => 4,
    'birth_date_day'   => 10,
    'death_date_year'  => 2020,
    'death_date_month' => 11,
    'death_date_day'   => 3,
]);

// Display name
echo $person->full_name;  // "Jane Marie Smith Jr."

// Update memorial display name from people
if (! $memorial->manual_name) {
    $memorial->display_name = Memorial::generateDisplayName($memorial->people);
    $memorial->save();
}

// Soft delete
$person->delete();
$person->restore();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
