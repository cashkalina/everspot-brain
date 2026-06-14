---
trait: Repeatable
owning_module: Repetition
source_paths:
  - modules/Repetition/Traits/Repeatable.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# Repeatable

**Source:** `modules/Repetition/Traits/Repeatable.php`
**Registry entry:** [system/traits/index.md#repeatable](../../../system/traits/index.md#repeatable)

## Purpose

Adds recurring-schedule support to a model via the `Repetition` polymorphic model. Using models can define named repetition groups (e.g. `'default'`), each with its own recurrence configuration (daily, weekly, monthly, etc.), and query for records occurring on specific dates or within date ranges.

The `repeat()` fluent builder returns a `Repeat` instance that is the primary API for setting up and querying recurrence patterns on a model instance.

## Contributed Columns

No columns are added to the using model's table. Repetition records (storing recurrence patterns and occurrence data) live in the `repetitions` table.

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `repetitions()` | `MorphMany` | `Modules\Repetition\Models\Repetition` | All repetition records for this model instance. |

## Contributed Scopes

| Scope | Signature | Description |
|-------|-----------|-------------|
| `scopeWhereOccursOn()` | `(Builder, Carbon $date, ?string $group = null): Builder` | Records that have a repetition occurring on `$date`, optionally filtered by group name. |
| `scopeWhereOccursBetween()` | `(Builder, Carbon $start, Carbon $end, ?string $group = null): Builder` | Records that have at least one repetition occurrence in `[$start, $end]`, optionally filtered by group. |

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `repetitionBaseDate()` | `(?RepetitionType $type = null): Carbon` | Returns the base date from which repetition start times are calculated. Defaults to `created_at ?? now()`. Override per model. |
| `repeat()` | `(): Repeat` | Returns a new `Repeat` fluent builder for this model — the primary API for configuring and interacting with repetition patterns. |
| `doesGroupAllowSave()` | `(string $group = 'default', bool $canOverwrite = false): bool` | Checks whether the given repetition group allows saving (delegates to `Repeat::daily()->group($group)->canOverwrite($canOverwrite)->doesGroupAllowSave()`). |
| `registerRepetitionGroups()` | `(): void` | Defines the model's repetition groups. Default implementation adds a `'default'` single-repetition group. Override to add multiple named groups. |
| `addRepetitionGroup()` | `(string $group): RepetitionGroup` | Creates and registers a named `RepetitionGroup` on the model. Returns the group for chaining. |
| `getRepetitionGroup()` | `(string $group = 'default'): RepetitionGroup` | Returns the named repetition group after calling `registerRepetitionGroups()`. Throws `InvalidArgumentException` if not found. |

## Public Property

| Property | Type | Description |
|----------|------|-------------|
| `$repetitionGroups` | `array` | Runtime registry of `RepetitionGroup` instances keyed by group name. |

## Configuration / Contract

No interface required. Override `registerRepetitionGroups()` to define custom groups and their configurations. Override `repetitionBaseDate()` to use a different column as the anchor date.

## Used By

Discoverable by grepping `traits:` frontmatter for `Repeatable` across model docs, or `use Repeatable` in Everspot source.
