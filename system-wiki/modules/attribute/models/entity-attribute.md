---
model: EntityAttribute
module: Attribute
table: entity_attributes
connection: tenant
primary_source: modules/Attribute/Models/EntityAttribute.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Attribute/Models/AttributeArea.php
  - modules/Attribute/Models/Attribute.php
  - modules/Attribute/Models/AttributeValue.php
traits:
  - SoftDeletes
related_models: [Attribute, AttributeArea, AttributeValue]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# EntityAttribute

## Overview

The EntityAttribute model is the binding layer in the Everspot EAV system. While an [Attribute](./attribute.md) defines what a custom field *is*, and an [AttributeValue](./attribute-value.md) stores what it *contains*, the EntityAttribute ties an attribute definition to a specific model class and optionally a specific entity instance. In essence it answers: "for this model class (and optionally for this particular record), in this area, should attribute X be present, what type should it be, and what constraints apply?"

The binding can be at two granularities:
- **Class-level binding** (`model_class` is set, `entity_type`/`entity_id` are null): the attribute appears for every instance of that model class.
- **Instance-level binding** (`entity_type`/`entity_id` are set via the polymorphic `entity()` relationship): the attribute is scoped to one specific entity record.

`attribute_area_id` places the binding within an [AttributeArea](./attribute-area.md) grouping region. The `type` column (cast to the `EntityAttributeType` enum) allows the binding to override or specialise the source attribute's type for this context. `is_required`, `enable_multiple`, `group`, and `sort_order` control validation and display behaviour. The `advanced_loading` JSON array holds configuration for deferred or conditional rendering. `default_value` overrides the attribute definition's own default; `getEffectiveDefaultValue()` resolves the cascade. Similarly `getEffectiveConfig()` resolves the cascade for the `config_data` configuration blob.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| model_class | varchar | Yes | - | Fully-qualified PHP class name the binding applies to (class-level) |
| entity_type | varchar | Yes | - | Polymorphic entity class name (instance-level binding) |
| entity_id | bigint | Yes | - | Polymorphic entity id (instance-level binding) |
| area | varchar | Yes | - | Legacy area string; superseded by `attribute_area_id` |
| attribute_area_id | bigint | Yes | - | FK → attribute_areas: the display area for this binding |
| type | varchar | No | - | Attribute type override for this binding (cast to EntityAttributeType enum) |
| attribute_id | bigint | Yes | - | FK → attributes: the attribute definition being bound |
| is_required | tinyint | No | 0 | Whether the attribute is required for this binding |
| enable_multiple | tinyint | No | 0 | Whether multiple values are allowed for this binding |
| group | varchar | Yes | - | Optional display group label |
| sort_order | int | No | 0 | Display sort order within the area |
| advanced_loading | json | Yes | - | Configuration for deferred/conditional rendering (cast to array) |
| default_value | text | Yes | - | Default value override for this binding (cascades to attribute's default) |
| config_data | json | Yes | - | Type-config override for this binding (cast via AttributeConfigCast) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `attribute_area_id` → `attribute_areas.id`; `attribute_id` → `attributes.id`

**Indexes:** composite index on `(entity_type, entity_id)`; individual indexes on `attribute_area_id`, `attribute_id`

## Casts

- `type` → `EntityAttributeType::class` — casts the type string to the `EntityAttributeType` enum
- `advanced_loading` → `array` — decodes JSON to a PHP array
- `config_data` → `AttributeConfigCast::class` — deserialises the JSON config blob into a typed `AttributeConfigInterface` instance

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Fillable:** `['model_class', 'entity_type', 'entity_id', 'attribute_area_id', 'area', 'attribute_id', 'type', 'is_required', 'enable_multiple', 'group', 'sort_order', 'advanced_loading', 'default_value', 'config_data']`
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._ (column defaults `is_required = 0`, `enable_multiple = 0`, `sort_order = 0` are enforced at the DB level)

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — entity-attribute bindings are soft-deleted, never hard-deleted

## Relationships

- `entity()` — morphTo: the specific entity instance this binding is scoped to (instance-level bindings only; null for class-level bindings)
- `attributeArea()` — belongs to [AttributeArea](./attribute-area.md) (`attribute_area_id`): the display area for this binding
- `attribute()` — belongs to [Attribute](./attribute.md) (`attribute_id`): the attribute definition being bound
- `attributeValues()` — has many [AttributeValue](./attribute-value.md) (`source_entity_attribute_id`): all stored values for this binding

## Scopes

- `scopeForArea($query, $area): Builder` — filters by the legacy `area` string column (`'custom'` matches `null`); eager-loads `attribute` for convenience
- `scopeForAttributeArea($query, AttributeArea $attributeArea): Builder` — filters to bindings whose `attribute_area_id` matches the given [AttributeArea](./attribute-area.md)

## Events

_None defined on the model._

## Observers

_None registered._

## Key Methods

- `getEffectiveDefaultValue(): ?string` — resolves the cascading default: returns `$this->default_value` if set; otherwise falls back to `$this->attribute?->default_value`
- `getEffectiveConfig(): ?AttributeConfigInterface` — resolves the cascading config: returns `$this->config_data` if set; otherwise falls back to `$this->attribute?->config_data`

## Common Usage

```php
// Get all entity-attribute bindings for the Customer class in a specific area
$bindings = EntityAttribute::forAttributeArea($area)
    ->where('model_class', \Modules\Customer\Models\Customer::class)
    ->with('attribute')
    ->get();

// Get bindings scoped to a specific entity instance (instance-level)
$bindings = EntityAttribute::where('entity_type', \Modules\Customer\Models\Customer::class)
    ->where('entity_id', $customer->id)
    ->get();

// Resolve effective defaults / config (cascades from attribute definition)
$defaultValue = $binding->getEffectiveDefaultValue();
$config       = $binding->getEffectiveConfig();

// Get all attribute values recorded for this binding
$values = $binding->attributeValues()->with('attributeArea')->get();

// Legacy area scope
$legacyBindings = EntityAttribute::forArea('demographics')->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
