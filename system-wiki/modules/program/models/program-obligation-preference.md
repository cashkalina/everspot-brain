---
model: ProgramObligationPreference
module: Program
table: program_obligation_preferences
connection: tenant
primary_source: modules/Program/Models/ProgramObligationPreference.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Program/Models/ProgramObligationPreferenceCollection.php
  - modules/Program/Models/ProgramPreferenceCollectionOption.php
traits:
  - HasByUserFields
  - LogsActivity
  - HasExternalIds
  - HasIcon
  - HasModelDefinition
  - HasModificationRules
related_models: [ProgramObligationPreferenceCollection, ProgramPreferenceCollectionOption]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, program]
---

# ProgramObligationPreference

## Overview

The ProgramObligationPreference model records a single customer preference selection within a preference-collection response for a program obligation. When a customer is asked to choose how a specific obligation will be fulfilled (e.g., selecting a flower arrangement style or service option), each choice made by the customer is stored as a `ProgramObligationPreference` record.

Each preference belongs to a [ProgramObligationPreferenceCollection](./program-obligation-preference-collection.md) (the obligation-specific response container, identified by its foreign key `popc_id`) and optionally references a specific [ProgramPreferenceCollectionOption](./program-preference-collection-option.md) (a predefined option from the program template, referenced by `ppco_id`). If the option selected includes a free-text response (e.g., a custom choice), it is stored in `text_response`. General notes about the preference selection are stored in `notes`.

The model carries audit user stamps via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields). It has no observers registered.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| popc_id | bigint | No | - | FK → program_obligation_preference_collections: the response container this preference belongs to |
| ppco_id | bigint | Yes | - | FK → program_preference_collection_options: the predefined option selected (null for free-text only) |
| text_response | text | Yes | - | Free-text response from the customer for this preference |
| notes | text | Yes | - | Additional notes about this preference selection |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `popc_id` → `program_obligation_preference_collections.id`; `ppco_id` → `program_preference_collection_options.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `popc_id`, `ppco_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

_None._

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
- [HasExternalIds](../../../system/traits/index.md#hasexternalids) — polymorphic external identifier storage (inherited via BaseModel)
- [HasIcon](../../../system/traits/index.md#hasicon) — Bootstrap Icon class lookup for this model type (inherited via BaseModel)
- [HasModelDefinition](../../../system/traits/index.md#hasmodeldefinition) — resolves the `ModelDefinition` instance for this model (inherited via BaseModel)
- [HasModificationRules](../../../system/traits/index.md#hasmodificationrules) — lifecycle gate: `canBeEdited()`, `canBeDeleted()`, etc. (inherited via BaseModel)
- [LogsActivity](../../../system/traits/index.md#logsactivity) — auto-logs create/update/delete events via Spatie Activitylog (inherited via BaseModel)

## Relationships

- `programObligationPreferenceCollection()` — belongs to [ProgramObligationPreferenceCollection](./program-obligation-preference-collection.md) (`popc_id`): the response container that holds this preference
- `programPreferenceCollectionOption()` — belongs to [ProgramPreferenceCollectionOption](./program-preference-collection-option.md) (`ppco_id`): the predefined option that was selected (nullable)

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
// Access preferences for a given preference collection response
$preferences = $obligationPreferenceCollection->programObligationPreferences;

// Record a customer's choice of a predefined option
$preference = ProgramObligationPreference::create([
    'popc_id' => $obligationPreferenceCollection->id,
    'ppco_id' => $selectedOption->id,
    'notes'   => 'Customer confirmed by phone',
]);

// Record a free-text preference (no predefined option)
$preference = ProgramObligationPreference::create([
    'popc_id'       => $obligationPreferenceCollection->id,
    'ppco_id'       => null,
    'text_response' => 'White roses, please',
]);

// Inspect the selected option
$optionName = $preference->programPreferenceCollectionOption?->name;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
