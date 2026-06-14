---
trait: HasAttributes
owning_module: Attribute
source_paths:
  - modules/Attribute/Traits/HasAttributes.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasAttributes

**Source:** `modules/Attribute/Traits/HasAttributes.php`
**Registry entry:** [system/traits/index.md#hasattributes](../../../system/traits/index.md#hasattributes)

## Purpose

Adds EAV (Entity-Attribute-Value) custom attribute support to a model. Using models can store arbitrary key-value pairs (typed, validated attribute values) through the `AttributeValue` model without adding table columns. Attributes are defined by an administrator and then stored per-entity instance.

On model delete, related `AttributeValue` rows are also deleted. On restore (soft-delete restore), `AttributeValue` rows are restored from trash via `withTrashed()->restore()`.

## Contributed Columns

No columns are added to the using model's table. Attribute values live in the `attribute_values` table (via `attributable` polymorphic morph).

## Contributed Casts

None.

## Contributed Relationships

| Method | Type | Target | Description |
|--------|------|--------|-------------|
| `attributeValues()` | `MorphMany` | `Modules\Attribute\Models\AttributeValue` | All EAV attribute values for this model instance. |
| `entityAttributes()` | `MorphMany` | `Modules\Attribute\Models\EntityAttribute` | The attribute definitions associated with this entity type. |

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getAttributeViewData()` | `(): array` | Returns formatted view data for all attributes, via `AttributeValueViewer`. |
| `getAV()` | `(string $key): ?AttributeValue` | Returns the first `AttributeValue` with `key = $key` for this model, or `null`. |
| `getAVValue()` | `(string $key): mixed` | Returns the typed value of the attribute (`$av->value`), or `null` if the attribute is not set. |
| `getAVRawValue()` | `(string $key): mixed` | Returns the raw stored value (`$av->raw_value`) before type casting, or `null`. |

## Boot Behavior

`bootHasAttributes()` registers:

- **`deleted`** — calls `$model->attributeValues()->delete()` to cascade-delete attribute values.
- **`restored`** — calls `$model->attributeValues()->withTrashed()->restore()` to restore attribute values when the model is un-soft-deleted.

## Configuration / Contract

No interface required. The Attribute module tables (`attribute_values`, `entity_attributes`) must exist. Attribute definitions are created via the admin UI; models do not need to declare anything beyond `use HasAttributes;`.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasAttributes` across model docs, or `use HasAttributes` in Everspot source.
