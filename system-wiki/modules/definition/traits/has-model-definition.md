---
trait: HasModelDefinition
owning_module: Definition
source_paths:
  - modules/Definition/Traits/HasModelDefinition.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasModelDefinition

**Source:** `modules/Definition/Traits/HasModelDefinition.php`
**Registry entry:** [system/traits/index.md#hasmodeldefinition](../../../system/traits/index.md#hasmodeldefinition)

## Purpose

Provides a static `getModelDefinition()` method that resolves and returns the `ModelDefinition` instance for the calling model class. The `ModelDefinition` is a separate class (in a `Definitions/` directory by convention, mirroring the model's namespace) that centralises metadata about the model — field definitions, column types, validation rules, display labels, etc.

Resolution follows two strategies:
1. **Explicit** — if the model declares a static `$definitionClass` property, that class is used.
2. **Convention-based** — the model's namespace is transformed by replacing `\Models\` with `\Definitions\` to derive the definition class name.

An exception is thrown if the definition class does not exist or if it is configured for a different model class than the one that called `getModelDefinition()`.

Applied on `BaseModel`, so all concrete Everspot models that extend `BaseModel` inherit it.

## Contributed Columns

None.

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getModelDefinition()` | `static (): ModelDefinition` | Resolves the definition class (explicit or convention), instantiates it, validates it is for this model, and returns it. Throws `RuntimeException` on misconfiguration. |

## Configuration / Contract

No interface required on the using model. Either:
- Rely on the convention: `Modules\Foo\Models\Bar` → `Modules\Foo\Definitions\Bar` definition class.
- Or explicitly declare: `protected static string $definitionClass = MyDefinition::class;`

The definition class must exist and its `getModelClass()` must return the model's fully-qualified class name.

Applied on `BaseModel` — all concrete models inherit `getModelDefinition()` automatically.

## Used By

Applied on `BaseModel` (inherited by all concrete models). Discoverable by `use HasModelDefinition` in Everspot source.
