---
title: Attribute Module — Models
purpose: Index of all documented models in the Attribute module
last_updated: 2026-06-14
---

# Attribute Module — Models

The Attribute module implements a flexible EAV (Entity–Attribute–Value) system that allows dynamic custom attributes to be attached to any Everspot entity. Models in this module define the attribute schema (definitions), the placement bindings, and the stored values.

## Models

| Model | Table | Description |
|-------|-------|-------------|
| [Attribute](./attribute.md) | `attributes` | Defines a custom attribute: its type, label, key, validation rules, default, and type-specific config. Supports self-referential parent/child hierarchies for collection and array types. |
| [AttributeArea](./attribute-area.md) | `attribute_areas` | Defines a named grouping region for attributes within a specific model class. Controls ordering and visibility of attribute groups in the UI. |
| [AttributeValue](./attribute-value.md) | `attribute_values` | Stores the actual EAV value for a specific entity instance. Values are type-encoded via `ValueProcessor`; creation/update dispatches `AttributeValueUpdated` events. |
| [EntityAttribute](./entity-attribute.md) | `entity_attributes` | Binds an attribute definition to a model class or specific entity instance within an area. Controls required/multiple/sort behaviour and carries cascading default and config overrides. |

## Traits

Traits owned by the Attribute module are documented under [../traits/](../traits/index.md). The key module-owned trait is:

- [HasAttributes](../traits/has-attributes.md) — EAV integration trait applied to entity models; provides `attributeValues()` morphMany relationship and helper methods like `getAV()` / `getAVValue()`.

## Data Flow

```
Attribute          ← defines what a field IS
  └── EntityAttribute  ← binds the field to a model class / entity instance + area
        └── AttributeValue  ← stores the actual value for an entity instance
              └── AttributeArea  ← groups attribute slots in the UI
```

Any model using [HasAttributes](../traits/has-attributes.md) participates as the polymorphic `attributable` target of `AttributeValue`.
