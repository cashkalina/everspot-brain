---
trait: HasModelNumbering
owning_module: Common
source_paths:
  - modules/Common/Traits/HasModelNumbering.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasModelNumbering

**Source:** `modules/Common/Traits/HasModelNumbering.php`
**Registry entry:** [system/traits/index.md#hasmodelnumbering](../../../system/traits/index.md#hasmodelnumbering)

## Purpose

Generates user-facing sequential record numbers (stored in the `model_no` column) for Everspot models such as Customers, Orders, and Work Orders. After a record is created, `generateModelNumber()` is called automatically. It looks up a `ModelNumberConfiguration` row for the model's class and type, constructs the number from a prefix/suffix template (supporting `{{relation.field}}` interpolation), zero-pads the sequence number to the configured minimum digits, and increments the configuration's `next_number` counter atomically after saving.

An existing `model_no` is not overwritten unless `$force = true`.

## Contributed Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `model_no` | varchar | Yes | User-facing record number generated from the `ModelNumberConfiguration`. Model docs carry `(via HasModelNumbering — see trait doc)` in their Schema table. |

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `generateModelNumber()` | `(bool $force = false): void` | Resolves the configuration for this model/type, builds `prefix + zero-padded sequence + suffix`, saves quietly if the value changed, and increments `next_number`. No-op if `model_no` is already set and `$force` is `false`. |
| `resolveTemplate()` | `(string $template): string` | Expands `{{path.to.relation}}` placeholders by traversing relationship results and properties on `$this`. |
| `getModelNumberConfiguration()` | `(string $type = 'default'): ?ModelNumberConfiguration` | Queries `ModelNumberConfiguration` for the matching `model_type` + `type` row. |
| `getModelNumberType()` | `(): string` | Returns `$this->modelNumberDefaultType ?? 'default'`. Override in models with multiple number series. |

## Boot Behavior

`bootHasModelNumbering()` registers an `created` event hook that calls `$model->generateModelNumber()` after every insert.

## Configuration / Contract

Requires a `ModelNumberConfiguration` row in the database for the model class (matched by `model_type = Model::class` and `type`). The configuration stores:
- `prefix` / `suffix` — template strings (may contain `{{relation.field}}` placeholders)
- `next_number` — the current sequence counter
- `min_digits` — minimum digit width for zero-padding
- `interval` — increment step (typically 1)

Models that need multiple number series (e.g. different prefixes per customer type) override `getModelNumberType()` to return a dynamic type string. No interface is required.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasModelNumbering` across model docs, or `use HasModelNumbering` in Everspot source.
