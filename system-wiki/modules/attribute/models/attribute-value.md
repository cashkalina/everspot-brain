---
model: AttributeValue
module: Attribute
table: attribute_values
connection: tenant
primary_source: modules/Attribute/Models/AttributeValue.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Attribute/Models/AttributeArea.php
  - modules/Attribute/Models/AttributeValue.php
  - modules/Attribute/Models/EntityAttribute.php
  - modules/Attribute/Models/Attribute.php
  - modules/Attribute/Observers/AttributeValueObserver.php
  - modules/Attribute/Providers/AttributeServiceProvider.php
  - modules/Common/Models/ListOption.php
traits:
  - SoftDeletes
related_models: [Attribute, AttributeArea, AttributeValue, EntityAttribute, ListOption]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, core]
---

# AttributeValue

## Overview

The AttributeValue model is the leaf record of the Everspot EAV system — it stores the actual value that a specific entity instance (e.g. a Customer) holds for a particular custom attribute. The entity is identified polymorphically via `attributable_type` / `attributable_id`, linking this model to anything that uses [HasAttributes](../../../system/traits/index.md#hasattributes).

The raw persisted value lives in `raw_value` (always stored as text/JSON), and the `type` column mirrors the attribute type so that the `ValueProcessor` knows how to interpret the raw bytes. The `setRawValueAttribute` mutator routes the incoming value through `ValueProcessorFactory::create()` before storing it, applying any type-specific encoding. Reading back is symmetric: `getValueAttribute` calls `ValueProcessorFactory::createFromModel()` to decode and return the typed value, while `getValueForEditAttribute` returns a form-friendly representation.

Each value optionally links back to the [EntityAttribute](./entity-attribute.md) binding that spawned it (`source_entity_attribute_id`) and the bare [Attribute](./attribute.md) definition (`source_attribute_id`). It also optionally belongs to an [AttributeArea](./attribute-area.md) for placement. A `parent_attribute_value_id` self-reference supports nested/collection attribute values. The `config_data` column mirrors the attribute's config at the time the value was written; `hasOutdatedConfig()` detects drift from the current source config, and `syncConfigFromParent()` refreshes it.

When an AttributeValue is created or updated, `AttributeValueObserver` dispatches the `AttributeValueUpdated` event with old and new `raw_value` payloads, enabling downstream automations.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| attributable_type | varchar | No | - | Polymorphic owner model class |
| attributable_id | bigint | No | - | Polymorphic owner model id |
| parent_attribute_value_id | bigint | Yes | - | FK → attribute_values: parent value for nested/collection attributes |
| source_entity_attribute_id | bigint | Yes | - | FK → entity_attributes: the binding that defined this slot |
| source_attribute_id | bigint | Yes | - | FK → attributes: the attribute definition |
| area | varchar | Yes | - | Legacy area string (use `attribute_area_id` for new records) |
| attribute_area_id | bigint | Yes | - | FK → attribute_areas: display area this value belongs to |
| type | varchar | No | - | Attribute type (mirrors the source attribute's type) |
| label | varchar | No | - | Attribute label at the time the value was stored |
| key | varchar | No | - | Attribute key at the time the value was stored |
| raw_value | text | Yes | - | The serialised/encoded value (set via mutator through ValueProcessor) |
| raw_value_class | varchar | Yes | - | For `model-reference` type: the referenced model class |
| config_data | json | Yes | - | Snapshot of the attribute config at write time (cast via AttributeConfigCast) |
| validation_rules | text | Yes | - | Validation rules at the time the value was stored |
| is_active | tinyint | No | 1 | Whether this value is active |
| collection_model_type | varchar | Yes | - | For `collection` type: the referenced model class |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** `parent_attribute_value_id` → `attribute_values.id`; `source_entity_attribute_id` → `entity_attributes.id`; `source_attribute_id` → `attributes.id`; `attribute_area_id` → `attribute_areas.id`

**Indexes:** composite index on `(attributable_type, attributable_id)`; individual indexes on `parent_attribute_value_id`, `attribute_area_id`, `source_entity_attribute_id`, `source_attribute_id`, `raw_value_class`

## Casts

- `config_data` → `AttributeConfigCast::class` — deserialises the JSON config blob into a typed `AttributeConfigInterface` instance

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

- `setRawValueAttribute($value): void` — **mutator**: encodes the incoming value through `ValueProcessorFactory::create()` using `$this->attributes['type']` and the effective config; falls back to the source entity attribute or source attribute config if `config_data` is not set on this record
- `getValueAttribute(): mixed` — **accessor**: decodes `raw_value` via `ValueProcessorFactory::createFromModel()`, returning the typed value appropriate for the attribute type
- `getValueForEditAttribute(): mixed` — **accessor**: like `getValue` but returns a form-friendly representation (e.g. a date string suitable for an HTML `<input>`)
- `getConfigAttribute(): ?AttributeConfigInterface` — **accessor**: returns the cast `config_data` object as a named property
- `getReferencedModelAttribute(): ?Model` — for `model-reference` type: resolves and returns the referenced model instance via `app($this->raw_value_class)->find($this->raw_value)`; returns `null` if type is wrong or resolution fails
- `getReferencedListOptionAttribute(): ?ListOption` — for `list-option` type with a single (non-array) value: returns the resolved [ListOption](../../common/models/list-option.md); returns `null` for multi-select or missing values
- `getReferencedListOptionsAttribute(): Collection` — for `list-option` type: returns all resolved [ListOption](../../common/models/list-option.md) instances; handles both single and JSON-array values consistently

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — attribute values are soft-deleted, never hard-deleted

## Relationships

- `attributable()` — morphTo: the owning entity (any model using [HasAttributes](../../../system/traits/index.md#hasattributes), e.g. Customer)
- `attributeArea()` — belongs to [AttributeArea](./attribute-area.md) (`attribute_area_id`): the display area this value is placed in
- `parentAttributeValue()` — belongs to [AttributeValue](./attribute-value.md) (`parent_attribute_value_id`): the parent value in a nested collection
- `sourceEntityAttribute()` — belongs to [EntityAttribute](./entity-attribute.md) (`source_entity_attribute_id`): the entity-attribute binding that defined this value slot
- `sourceAttribute()` — belongs to [Attribute](./attribute.md) (`source_attribute_id`): the attribute definition

## Scopes

- `scopeForArea($query, $area): Builder` — filters to a given area string (`null` area for `'custom'`, otherwise matches `area` column); legacy scope for string-based area identification
- `scopeForAreaCode($query, $areaCode): Builder` — filters via the related `attributeArea` where `code = $areaCode`
- `scopeForEntityAttribute($query, $entityAttribute): Builder` — filters to values whose `source_entity_attribute_id` matches the given entity attribute's id
- `scopeReferencingModel($query, Model $model): Builder` — filters to `model-reference` values that point to the given model instance (matches `type`, `raw_value_class`, and `raw_value`)
- `scopeWithListOption($query, ListOption $listOption): Builder` — filters to `list-option` values whose `raw_value` matches the given [ListOption](../../common/models/list-option.md)'s id

## Events

_None defined on the model._ Lifecycle events are dispatched by `AttributeValueObserver` (see Observers).

## Observers

- `AttributeValueObserver` — registered in `AttributeServiceProvider::registerObservers()` (`AttributeValue::observe(AttributeValueObserver::class)`). Handles:
  - `created` — dispatches `AttributeValueUpdated` event with `old_value = null` and `new_value = $attributeValue->raw_value` (treats creation as transition from null)
  - `updated` — dispatches `AttributeValueUpdated` event with `old_value = getOriginal('raw_value')` and `new_value = $attributeValue->raw_value`
  - `deleted`, `restored`, `forceDeleted` — no-op stubs (present but empty)

## Key Methods

- `generateFieldName(): string` — returns a stable HTML field name for form rendering: `'av-id-{id}'` when persisted, or `'av-seaid-{source_entity_attribute_id}'` for unsaved instances
- `getValueProcessor(): ValueProcessor` — returns the `ValueProcessor` instance for this value record (via `ValueProcessorFactory::createFromModel($this)`); exposed publicly so callers can access the full processor API
- `hasOutdatedConfig(): bool` — compares the stored `config_data` against the current effective config from the source entity attribute or source attribute; returns `true` if they differ (detected via `toArray()` comparison)
- `syncConfigFromParent(): void` — refreshes `config_data` from the current effective config of the source entity attribute or source attribute, then saves; used to repair drift after the source attribute's config is updated

## Common Usage

```php
// Read a customer's attribute values for a given area
$values = $customer->attributeValues()
    ->forAreaCode('customer-demographics')
    ->with('sourceEntityAttribute.attribute')
    ->get();

// Read the typed value
echo $value->value;           // decoded; type-appropriate (e.g. Carbon for date, bool for boolean)
echo $value->value_for_edit;  // form-ready representation

// Write a value through the mutator (type-encodes automatically)
$value->type      = 'string';
$value->raw_value = 'some text';  // goes through setRawValueAttribute → ValueProcessor

// Resolve a list-option value
$option  = $value->referenced_list_option;   // single-select
$options = $value->referenced_list_options;  // multi-select (always a Collection)

// Resolve a model-reference value
$model = $value->referenced_model;

// Detect and repair config drift
if ($value->hasOutdatedConfig()) {
    $value->syncConfigFromParent();
}

// Find all values pointing to a specific model
$refs = AttributeValue::referencingModel($customer)->get();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
