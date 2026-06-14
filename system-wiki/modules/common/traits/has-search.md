---
trait: HasSearch
owning_module: Common
source_paths:
  - modules/Common/Traits/HasSearch.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasSearch

**Source:** `modules/Common/Traits/HasSearch.php`
**Registry entry:** [system/traits/index.md#hassearch](../../../system/traits/index.md#hassearch)

## Purpose

Integrates a model with Laravel Scout for full-text search indexing. The trait uses Scout's `Searchable` trait internally and provides a structured `toSearchableArray()` implementation with:

1. A set of standard columns that are included by default (configurable per model via `$searchableColumns`).
2. Global special-case handling (e.g. auto-including `customer_full_name` for any model with a `customer_id` column).
3. Model-specific overrides via `addToSearchData()` (keys to add) and `removeFromSearchData()` (keys to remove) hooks.
4. A `model_full_title` field always included, sourced from `getModelFullTitle()` (typically defined on BaseModel).

## Contributed Columns

No database columns are contributed. Scout maintains a separate search index outside the database.

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

Laravel Scout's `Searchable` trait adds its own scopes (e.g. `search()`) inherited through `HasSearch`.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `toSearchableArray()` | `(): array` | Entry point for Scout; delegates to `getStandardFields()`. |
| `getStandardFields()` | `(): array` | Builds the search payload: intersects table columns with `$searchableColumns`, adds `model_full_title`, applies global and model-specific special cases. |
| `handleGlobalSpecialCases()` | `(array $data, array $tableColumns): array` | Adds `customer_full_name` when the table has a `customer_id` column. |
| `handleModelSpecialCases()` | `(array $data): array` | Merges `addToSearchData()` additions and removes `removeFromSearchData()` keys. |
| `getSearchDataToAdd()` | `(): array` | Calls `addToSearchData()` on the model if it exists; otherwise returns `[]`. |
| `getSearchFieldsToRemove()` | `(): array` | Calls `removeFromSearchData()` on the model if it exists; otherwise returns `[]`. |
| `getStandardColumnsToInclude()` | `(): array` | Returns `$searchableColumns` if defined on the model, otherwise `['model_no', 'memo', 'name', 'title']`. |

## Configuration / Contract

Using models may optionally define:

```php
// Override standard columns to include in the search index:
protected array $searchableColumns = ['model_no', 'name', 'description'];

// Add extra fields to the search payload:
public function addToSearchData(): array
{
    return ['customer_full_name' => $this->customer?->full_name];
}

// Remove fields from the search payload:
public function removeFromSearchData(): array
{
    return ['internal_notes'];
}
```

Laravel Scout must be configured in the application (driver, index settings, etc.).

## Used By

Discoverable by grepping `traits:` frontmatter for `HasSearch` across model docs, or `use HasSearch` in Everspot source.
