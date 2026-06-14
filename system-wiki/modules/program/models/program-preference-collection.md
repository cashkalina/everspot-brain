---
model: ProgramPreferenceCollection
module: Program
table: program_preference_collections
connection: tenant
primary_source: modules/Program/Models/ProgramPreferenceCollection.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Program/Models/Program.php
  - modules/Program/Models/ProgramPreferenceCollectionOption.php
traits:
  - HasByUserFields
related_models: [Program, ProgramPreferenceCollectionOption]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, program]
---

# ProgramPreferenceCollection

## Overview

The ProgramPreferenceCollection model defines a preference-collection template that belongs to a [Program](./program.md). It specifies when preferences should be collected from customers (via `collection_start_date` and `collection_end_date`), which obligations those preferences apply to (via `obligation_due_start_date` and `obligation_due_end_date`), how many preference selections the customer must make (`min_preferences`, `max_preferences`), and whether automated email and SMS communications should be sent to prompt the customer for their selections.

This is the **template** side of the preference-collection system. When a [ProgramObligation](./program-obligation.md) falls within the collection window, a [ProgramObligationPreferenceCollection](./program-obligation-preference-collection.md) is created as the per-obligation response container, pointing back to this template. The actual options available to the customer are defined as child [ProgramPreferenceCollectionOption](./program-preference-collection-option.md) records.

The model carries audit user stamps via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) but has no observers registered.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| program_id | bigint | No | - | FK → programs: the program this preference collection belongs to |
| collection_start_date | date | No | - | Date on which preference collection begins for eligible obligations |
| collection_end_date | date | No | - | Date on which preference collection ends |
| obligation_due_start_date | date | No | - | Start of the obligation due-date range this collection applies to |
| obligation_due_end_date | date | No | - | End of the obligation due-date range this collection applies to |
| min_preferences | int | No | - | Minimum number of preference selections a customer must make |
| max_preferences | int | No | - | Maximum number of preference selections a customer may make |
| enable_auto_email | tinyint | No | 0 | Whether to automatically send an email prompting customers for their selections |
| enable_auto_sms | tinyint | No | 0 | Whether to automatically send an SMS prompting customers for their selections |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `program_id` → `programs.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `program_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `collection_start_date` → `date`
- `collection_end_date` → `date`
- `obligation_due_start_date` → `date`
- `obligation_due_end_date` → `date`
- `enable_auto_email` → `boolean`
- `enable_auto_sms` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backing the `created_by` / `updated_by` / `deleted_by` columns

## Relationships

- `program()` — belongs to [Program](./program.md) (`program_id`): the program this preference-collection template belongs to
- `programPreferenceCollectionOptions()` — has many [ProgramPreferenceCollectionOption](./program-preference-collection-option.md): the predefined options available for customer selection within this collection

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

_None._

## Common Usage

```php
// Create a preference-collection template for a program
$collection = ProgramPreferenceCollection::create([
    'program_id'                => $program->id,
    'collection_start_date'     => '2026-01-01',
    'collection_end_date'       => '2026-03-31',
    'obligation_due_start_date' => '2026-04-01',
    'obligation_due_end_date'   => '2026-06-30',
    'min_preferences'           => 1,
    'max_preferences'           => 3,
    'enable_auto_email'         => true,
    'enable_auto_sms'           => false,
]);

// Add options to the template
$collection->programPreferenceCollectionOptions()->create([
    'name'                 => 'White Roses',
    'enable_text_response' => false,
    'is_default'           => true,
]);

// Access all preference collections for a program
$collections = $program->programPreferenceCollections;

// Check communication settings
if ($collection->enable_auto_email) {
    // System will send automated emails to customers
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
