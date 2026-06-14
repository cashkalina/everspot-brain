---
model: ProgramPreferenceCollectionOption
module: Program
table: program_preference_collection_options
connection: tenant
primary_source: modules/Program/Models/ProgramPreferenceCollectionOption.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Program/Models/ProgramPreferenceCollection.php
traits:
  - HasByUserFields
  - LogsActivity
  - HasExternalIds
  - HasIcon
  - HasModelDefinition
  - HasModificationRules
related_models: [ProgramPreferenceCollection]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, program]
---

# ProgramPreferenceCollectionOption

## Overview

The ProgramPreferenceCollectionOption model defines a single selectable option within a [ProgramPreferenceCollection](./program-preference-collection.md) template. When a cemetery sets up a preference-collection workflow for a program (e.g., "choose your flower arrangement"), each available choice — such as "White Roses," "Mixed Seasonal," or "No Flowers" — is stored as a `ProgramPreferenceCollectionOption` record.

Options carry a `name` and optional `description`. The `enable_text_response` flag indicates whether the customer is allowed or required to provide a free-text response when selecting this option (used when a choice needs elaboration, e.g., "Other — please specify"). The `is_default` flag marks which option is pre-selected when the preference collection is auto-defaulted by the system. A `default_text_response` stores the text that is auto-filled when this option is defaulted.

When a customer makes a selection, the chosen option is referenced by a [ProgramObligationPreference](./program-obligation-preference.md) record via the `ppco_id` foreign key. The model carries audit user stamps via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) and has no observers registered.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| ppc_id | bigint | No | - | FK → program_preference_collections: the collection template this option belongs to |
| name | varchar | No | - | Display name of this option (e.g., "White Roses") |
| description | text | Yes | - | Long-form description of the option |
| enable_text_response | tinyint | No | 0 | Whether a free-text response is enabled when this option is selected |
| is_default | tinyint | No | 0 | Whether this option is pre-selected when a collection is auto-defaulted |
| default_text_response | text | Yes | - | The text auto-filled in the text response field when this option is defaulted |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `ppc_id` → `program_preference_collections.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `ppc_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `enable_text_response` → `boolean`
- `is_default` → `boolean`

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

- `programPreferenceCollection()` — belongs to [ProgramPreferenceCollection](./program-preference-collection.md) (`ppc_id`): the collection template this option belongs to

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
// Create options for a preference collection template
$defaultOption = ProgramPreferenceCollectionOption::create([
    'ppc_id'               => $collection->id,
    'name'                 => 'White Roses',
    'description'          => 'Standard white rose arrangement',
    'enable_text_response' => false,
    'is_default'           => true,
    'default_text_response'=> null,
]);

$customOption = ProgramPreferenceCollectionOption::create([
    'ppc_id'               => $collection->id,
    'name'                 => 'Other',
    'description'          => 'Specify a custom arrangement',
    'enable_text_response' => true,
    'is_default'           => false,
    'default_text_response'=> null,
]);

// Access all options for a preference collection
$options = $collection->programPreferenceCollectionOptions;

// Find the default option
$default = $collection->programPreferenceCollectionOptions
    ->firstWhere('is_default', true);

// Check if an option accepts free-text input
if ($option->enable_text_response) {
    // Show a text field alongside the option
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
