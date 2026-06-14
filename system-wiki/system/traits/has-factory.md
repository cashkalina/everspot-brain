---
trait: HasFactory
owning_module: framework
framework: Illuminate\Database\Eloquent\Factories\HasFactory
source_paths:
  - vendor/laravel/framework/src/Illuminate/Database/Eloquent/Factories/HasFactory.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasFactory

**Namespace:** `Illuminate\Database\Eloquent\Factories\HasFactory`
**Package:** Laravel Framework (`laravel/framework`)
**Registry entry:** [index.md#hasfactory](./index.md#hasfactory)

## Purpose

Laravel's standard model-factory hook. Adds a static `factory()` method to a model, enabling the fluent factory API for test data creation. By default, Laravel discovers the factory class by convention (`Database\Factories\<ModelName>Factory`); models can override `newFactory()` to return a specific factory instance when they are in a non-standard namespace (as most Everspot module models are).

## Contributed Columns

None. The factory system is purely a testing/seeding utility; it does not add database columns.

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `factory()` | `static (int\|null $count = null, array $state = []): Factory` | Returns a new factory builder for the model, optionally pre-configured with a count and/or state. |
| `newFactory()` | `static (): Factory` | Override this in the model to return a specific factory instance (common in Everspot module models, e.g. `return CustomerFactory::new()`). |

## Configuration / Contract

No database columns or interface required. For module models whose factories are not in the default `Database\Factories\` namespace, override `newFactory()` to return the correct factory class. Example:

```php
protected static function newFactory(): Factory
{
    return \Modules\Customer\Database\Factories\CustomerFactory::new();
}
```

## Used By

Discoverable by grepping `traits:` frontmatter for `HasFactory` across model docs, or `use HasFactory` / `use Illuminate\Database\Eloquent\Factories\HasFactory` in Everspot source.
