---
trait: HasSchemalessAttributes
owning_module: Common
source_paths:
  - modules/Common/Traits/HasSchemalessAttributes.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasSchemalessAttributes

**Source:** `modules/Common/Traits/HasSchemalessAttributes.php`
**Registry entry:** [system/traits/index.md#hasschemalessattributes](../../../system/traits/index.md#hasschemalessattributes)

## Purpose

Adds a `config_data` JSON column to a model backed by the [Spatie Schemaless Attributes](https://github.com/spatie/laravel-schemaless-attributes) package (`spatie/laravel-schemaless-attributes`). The package stores arbitrary key-value pairs in a single JSON column without requiring schema migrations for each new key. The column is cast to `SchemalessAttributes::class`, giving it a fluent dot-notation accessor.

Used on the Tenant model to store dynamic per-tenant configuration values (e.g. integration settings, feature toggles) without adding dedicated columns to the tenants table.

## Contributed Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `config_data` | json | Yes | Schemaless key-value store. Cast to `SchemalessAttributes`. Model docs carry `(via HasSchemalessAttributes — see trait doc)` in their Schema table. |

## Contributed Casts

| Attribute | Cast |
|-----------|------|
| `config_data` | `Spatie\SchemalessAttributes\Casts\SchemalessAttributes::class` |

The cast is applied dynamically inside `initializeHasSchemalessAttributes()` (an Eloquent initializer called at model instantiation time), not in a static `$casts` array.

## Contributed Relationships

None.

## Contributed Scopes

| Scope | Signature | Description |
|-------|-----------|-------------|
| `scopeWithExtraAttributes()` | `(Builder): Builder` | Delegates to `config_data->modelScope()` — the Spatie package scope for filtering by schemaless attribute values. |

## Contributed Methods

None beyond the scope above.

## Configuration / Contract

The using model's database table must have a `config_data` JSON column (added via migration). No interface is required. The Spatie `spatie/laravel-schemaless-attributes` package must be installed.

Reading and writing values:

```php
$tenant->config_data->set('quickbooks_company_id', 'abc123');
$tenant->save();

$tenant->config_data->get('quickbooks_company_id'); // 'abc123'
$tenant->config_data->quickbooks_company_id;         // same, via magic accessor
```

## Used By

Discoverable by grepping `traits:` frontmatter for `HasSchemalessAttributes` across model docs, or `use HasSchemalessAttributes` in Everspot source.
