---
trait: HasRecognition
owning_module: Recognition
source_paths:
  - modules/Recognition/Traits/HasRecognition.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasRecognition

**Source:** `modules/Recognition/Traits/HasRecognition.php`
**Registry entry:** [system/traits/index.md#hasrecognition](../../../system/traits/index.md#hasrecognition)

## Purpose

Attaches a model to the Recognition module's arrangement and rule system via polymorphic relationships. When the using model is updated, it triggers a cascade update on all associated `RecognitionArrangement` records (calling `updatedRecognizable($model)` on each) so recognition rules can be re-evaluated in response to source model changes.

Also provides a helper to look up a specific `RecognitionRule` by type from a JSON config field (`recognition_config`).

## Contributed Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `recognition_config` | json | Yes | JSON blob storing recognition configuration keyed by rule type (e.g. `['some_rule_type' => <recognition_rule_id>]`). Expected to exist on the using model's table. |

_Note: The presence and exact type of `recognition_config` depend on the specific model's migration._

## Contributed Casts

None contributed by the trait itself. Models that use `recognition_config` typically cast it to `array` in their own `$casts`.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `recognitionArrangements()` | `MorphMany` | `Modules\Recognition\Models\RecognitionArrangement` | All recognition arrangements for this model (via `recognizable` morph). |
| `recognitionElements()` | `MorphMany` | `Modules\Recognition\Models\RecognitionElement` | All recognition elements for this model (via `recognizable` morph). |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getRecognitionRule()` | `(string $type): ?RecognitionRule` | Looks up `recognition_config[$type]` and returns the corresponding `RecognitionRule`, or `null`. |

## Boot Behavior

`bootHasRecognition()` registers an `updated` event hook that iterates `$model->recognitionArrangements` (the loaded collection) and calls `updatedRecognizable($model)` on each arrangement.

## Configuration / Contract

No interface required. The using model's table should have a `recognition_config` JSON column. The Recognition module tables (`recognition_arrangements`, `recognition_elements`, `recognition_rules`) must exist.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasRecognition` across model docs, or `use HasRecognition` in Everspot source.
