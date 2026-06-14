---
trait: HasPartialDateScopes
owning_module: Common
source_paths:
  - modules/Common/Traits/HasPartialDateScopes.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasPartialDateScopes

**Source:** `modules/Common/Traits/HasPartialDateScopes.php`
**Registry entry:** [system/traits/index.md#haspartialdatescopes](../../../system/traits/index.md#haspartialdatescopes)

## Purpose

Provides Eloquent query scopes for models that store dates as component columns (`{prefix}_year` / `{prefix}_month` / `{prefix}_day`). This pattern (called a "partial date") allows storing incomplete dates — a year only, a year and month, or a full date — without nullable full-date columns that hide what information is actually known.

All scopes accept the base column prefix (e.g. `'dob'` for `dob_year` / `dob_month` / `dob_day`) and a date value. Date values may be a Carbon instance, a `PartialDate` value object, or a date string (parsed via Carbon).

## Contributed Columns

No columns are added. The using model must already have the `{prefix}_year`, `{prefix}_month`, and `{prefix}_day` columns on its table.

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

All scopes accept `Builder $query` implicitly as the first parameter (Eloquent convention).

| Scope | Signature | Description |
|-------|-----------|-------------|
| `scopeOrderByPartialDate()` | `(Builder, string $column, string $direction = 'asc'): Builder` | Orders results by year, then month, then day for the given column prefix. |
| `scopeWherePartialDateAfter()` | `(Builder, string $column, string\|PartialDate\|Carbon $date): Builder` | Records where the partial date is strictly after `$date`. |
| `scopeWherePartialDateBefore()` | `(Builder, string $column, string\|PartialDate\|Carbon $date): Builder` | Records where the partial date is strictly before `$date`. |
| `scopeWherePartialDateOnOrAfter()` | `(Builder, string $column, string\|PartialDate\|Carbon $date): Builder` | Records where the partial date is on or after `$date` (inclusive). |
| `scopeWherePartialDateOnOrBefore()` | `(Builder, string $column, string\|PartialDate\|Carbon $date): Builder` | Records where the partial date is on or before `$date` (inclusive). |
| `scopeWherePartialDateYear()` | `(Builder, string $column, int $year): Builder` | Records where the year component matches. |
| `scopeWherePartialDateYearMonth()` | `(Builder, string $column, int $year, int $month): Builder` | Records where both year and month components match. |

## Contributed Methods

None beyond the scopes above.

## Configuration / Contract

No interface or property required. The model must have the appropriate `{prefix}_year` / `{prefix}_month` / `{prefix}_day` columns.

Usage example (from the trait's own docblock):

```php
Interment::orderByPartialDate('dob', 'desc')->get();
Interment::wherePartialDateYear('dob', 2000)->get();
Customer::wherePartialDateYearMonth('dob', 1950, 6)->get();
```

## Used By

Discoverable by grepping `traits:` frontmatter for `HasPartialDateScopes` across model docs, or `use HasPartialDateScopes` in Everspot source.
