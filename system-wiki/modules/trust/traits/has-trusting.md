---
trait: HasTrusting
owning_module: Trust
source_paths:
  - modules/Trust/Traits/HasTrusting.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasTrusting

**Source:** `modules/Trust/Traits/HasTrusting.php`
**Registry entry:** [system/traits/index.md#hastrusting](../../../system/traits/index.md#hastrusting)

## Purpose

Attaches a model to the Trust module's arrangement and element system via polymorphic relationships. When the using model is updated, it triggers a cascade update on all associated `TrustArrangement` records (calling `updatedTrustArrangeable($model)` on each) so trust accounting can recalculate in response to source model changes.

Also provides access to a `TrustingScheduleGroup` via a JSON config field (`trusting_config['trusting_schedule_group_id']`).

## Contributed Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `trusting_config` | json | Yes | JSON blob storing trusting configuration, including `trusting_schedule_group_id`. Expected to exist on the using model's table; model docs carry `(via HasTrusting — see trait doc)` if applicable. |

_Note: The presence and exact type of `trusting_config` depend on the specific model's migration. Not all models using `HasTrusting` may include this column if `getTrustingScheduleGroup()` is unused._

## Contributed Casts

None contributed by the trait itself. Models that use `trusting_config` typically cast it to `array` or `object` in their own `$casts`.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `trustArrangements()` | `MorphMany` | `Modules\Trust\Models\TrustArrangement` | All trust arrangements for this model (via `trust_arrangeable` morph). |
| `trustElements()` | `MorphMany` | `Modules\Trust\Models\TrustElement` | All trust elements for this model (via `trust_arrangeable` morph). |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getTrustingScheduleGroup()` | `(): ?TrustingScheduleGroup` | Returns the `TrustingScheduleGroup` identified by `trusting_config['trusting_schedule_group_id']`, or `null`. |

## Boot Behavior

`bootHasTrusting()` registers an `updated` event hook that iterates `$model->trustArrangements` (the loaded collection) and calls `updatedTrustArrangeable($model)` on each arrangement, allowing the Trust module to recalculate trust values in response to source record changes.

## Configuration / Contract

No interface required. The using model's table should have a `trusting_config` JSON column when `getTrustingScheduleGroup()` is needed. The Trust module tables (`trust_arrangements`, `trust_elements`, `trusting_schedule_groups`) must exist.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasTrusting` across model docs, or `use HasTrusting` in Everspot source.
