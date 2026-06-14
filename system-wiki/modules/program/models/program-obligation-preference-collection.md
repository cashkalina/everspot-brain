---
model: ProgramObligationPreferenceCollection
module: Program
table: program_obligation_preference_collections
connection: tenant
primary_source: modules/Program/Models/ProgramObligationPreferenceCollection.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Program/Models/ProgramObligation.php
  - modules/Program/Models/ProgramPreferenceCollection.php
traits:
  - HasByUserFields
related_models: [ProgramObligation, ProgramPreferenceCollection]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [service, program]
---

# ProgramObligationPreferenceCollection

## Overview

The ProgramObligationPreferenceCollection model is the per-obligation response container for a customer preference workflow. When a program obligation requires the customer to select service preferences (e.g., choosing flower types or casket options), this record captures the response session — linking the specific [ProgramObligation](./program-obligation.md) to the [ProgramPreferenceCollection](./program-preference-collection.md) template that defines the available choices.

The model tracks the lifecycle of the preference-collection process: when the collection was defaulted (auto-filled by the system, `defaulted_at`), when the customer actually responded (`responded_at`), whether the response was entered by a staff member on behalf of the customer (`is_staff_response`, `staff_id`), and when automated communications were sent (`email_sent_at`, `sms_sent_at`). These datetime columns are cast via `TimezonedDateTime` for timezone-aware handling.

Individual preference selections within this response container are stored as [ProgramObligationPreference](./program-obligation-preference.md) records (one per selected option), linked back to this record via the `popc_id` foreign key. The model carries audit user stamps via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) but has no observers registered.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| obligation_id | bigint | No | - | FK → program_obligations: the obligation whose preferences are being collected |
| ppc_id | bigint | No | - | FK → program_preference_collections: the preference-collection template defining available options |
| notes | text | Yes | - | Notes about this preference-collection response |
| is_staff_response | tinyint | No | 0 | Whether this response was entered by staff on behalf of the customer |
| staff_id | bigint | Yes | - | FK → users: the staff member who entered the response (when `is_staff_response = 1`) |
| defaulted_at | datetime | Yes | - | Timestamp when the response was auto-defaulted by the system (cast to TimezonedDateTime) |
| responded_at | datetime | Yes | - | Timestamp when the customer (or staff) completed the response (cast to TimezonedDateTime) |
| email_sent_at | datetime | Yes | - | Timestamp when the preference-collection email was sent (cast to TimezonedDateTime) |
| sms_sent_at | datetime | Yes | - | Timestamp when the preference-collection SMS was sent (cast to TimezonedDateTime) |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** `obligation_id` → `program_obligations.id`; `ppc_id` → `program_preference_collections.id`; `staff_id` → `users.id`; `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** FK-backing indexes on `obligation_id`, `ppc_id`, `staff_id`, `created_by`, `updated_by`, `deleted_by`.

## Casts

- `defaulted_at` → `TimezonedDateTime::class` — timezone-aware datetime handling (see `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)
- `responded_at` → `TimezonedDateTime::class` — timezone-aware datetime handling
- `is_staff_response` → `boolean`
- `email_sent_at` → `TimezonedDateTime::class` — timezone-aware datetime handling
- `sms_sent_at` → `TimezonedDateTime::class` — timezone-aware datetime handling

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

- `programObligation()` — belongs to [ProgramObligation](./program-obligation.md) (`obligation_id`): the obligation whose preferences are being collected
- `programPreferenceCollection()` — belongs to [ProgramPreferenceCollection](./program-preference-collection.md) (`ppc_id`): the preference-collection template defining available options

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
// Access the preference-collection response for an obligation
$response = $obligation->programObligationPreferenceCollection;

// Check if the response was submitted by staff
if ($response->is_staff_response) {
    echo "Entered by staff: " . $response->staff_id;
}

// Check communication history
if ($response->email_sent_at) {
    echo "Email sent at: {$response->email_sent_at}";
}

// Check if the customer has responded
if ($response->responded_at) {
    echo "Customer responded at: {$response->responded_at}";
} else {
    echo "Awaiting customer response";
}

// Access the template that defines available options
$template = $response->programPreferenceCollection;
$availableOptions = $template->programPreferenceCollectionOptions;
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
