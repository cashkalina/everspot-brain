---
trait: HasMoneyFields
owning_module: Common
source_paths:
  - modules/Common/Traits/HasMoneyFields.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasMoneyFields

**Source:** `modules/Common/Traits/HasMoneyFields.php`
**Registry entry:** [system/traits/index.md#hasmoneyfields](../../../system/traits/index.md#hasmoneyfields)

## Purpose

Provides transparent cents-to-dollars conversion for money columns. Values are stored in the database as integer cents (e.g. `12500` = $125.00); the trait intercepts `getAttribute` and `setAttribute` to convert automatically, so application code works in dollars (floats/strings) throughout.

The trait also supports a `shouldBeNegative($key)` hook: if a using model defines that method, values for the flagged key are negated on both read and write (useful for credit/debit sign conventions).

**Note:** A parallel copy exists at `central/Common/Traits/HasMoneyFields.php` for the central-database `PaymentProcessor` models. The `modules/Common/Traits/HasMoneyFields.php` copy (documented here) is what all tenant-side `modules/` models import.

## Contributed Columns

This trait does not define specific columns itself. Instead, each using model declares a `$moneyAttributes` array listing the column names that should be treated as cents:

```php
protected array $moneyAttributes = ['amount', 'fee', 'tax'];
```

Only columns listed in `$moneyAttributes` on the using model are converted. Model docs should note which columns are money-converted.

## Contributed Casts

None added via the `$casts` array. Conversion is handled by overriding `getAttribute` / `setAttribute` rather than via Eloquent casts.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getAttribute()` | `(string $key): mixed` | Overrides Eloquent's getter; divides by 100 for money attributes, negates if `shouldBeNegative()` applies. |
| `setAttribute()` | `(string $key, mixed $value): void` | Overrides Eloquent's setter; multiplies by 100 for money attributes, negates if `shouldBeNegative()` applies. |
| `formatMoney()` | `(mixed $value, bool $withSign = true): string` | Formats a numeric value as a currency string (`$1,234.56`). Accepts a raw value, a callable, or a string attribute name. Returns `$0.00` for non-numeric input. |
| `fromCents()` | `(int\|null $value): float\|null` | Divides by 100; returns `null` for null input. |
| `toCents()` | `(mixed $value): int\|null` | Multiplies by 100; returns `null` for null or empty or non-numeric input. |
| `getRawCentsValue()` | `(string $key): mixed` | Returns the raw integer cents value from `getRawOriginal()`, bypassing conversion. |

## Configuration / Contract

Using models must declare:
```php
protected array $moneyAttributes = ['amount', 'subtotal', /* ... */];
```

Optionally, a model may define `shouldBeNegative(string $key): bool` to negate specific columns on read and write.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasMoneyFields` across model docs, or `use HasMoneyFields` in `modules/` Everspot source.
