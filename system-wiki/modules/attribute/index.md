---
title: Attribute Module
purpose: Module overview for the Attribute (EAV) module
last_updated: 2026-06-14
---

# Attribute Module

The Attribute module provides a flexible EAV (Entity–Attribute–Value) system for Everspot. It allows administrators to define dynamic custom attributes and attach them to any entity that uses the [HasAttributes](../../system/traits/index.md#hasattributes) trait, without requiring schema migrations for each new field.

## Directory Structure

```
modules/attribute/
├── models/       # Model documentation (Attribute, AttributeArea, AttributeValue, EntityAttribute)
└── traits/       # Module-owned trait documentation (HasAttributes)
```

## Contents

- [Models](./models/index.md) — four models forming the EAV core
- [Traits](./traits/index.md) — `HasAttributes` trait that integrates entities with the EAV system

## Key Concepts

- **Attribute** — the definition of a custom field (type, label, validation, config)
- **AttributeArea** — a named grouping region within a model class for organising attribute fields
- **EntityAttribute** — the binding that places an attribute definition into an area for a model class or entity instance
- **AttributeValue** — the stored value for a specific entity instance

Changes to attribute values dispatch `AttributeValueUpdated` events (via `AttributeValueObserver`), enabling downstream automations to react to EAV data changes.
