---
trait: HasColor
owning_module: Event
source_paths:
  - modules/Event/Traits/HasColor.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasColor

**Source:** `modules/Event/Traits/HasColor.php`
**Registry entry:** [system/traits/index.md#hascolor](../../../system/traits/index.md#hascolor)

## Purpose

Provides color management methods for models that store a hex color value (e.g. calendar events and calendars). Abstracts color retrieval and luminance-based text contrast calculation so UI components can consistently render colored elements with readable text.

## Contributed Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `color` | varchar | Yes | Hex color string (e.g. `'#3788d8'`). Expected to exist on the using model's table; model docs carry `(via HasColor — see trait doc)` if applicable. |

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getColor()` | `(): string` | Returns `$this->color` or the default `'#3788d8'` if not set. |
| `getTextColor()` | `(): string` | Returns `'#000000'` (black) for light backgrounds or `'#ffffff'` (white) for dark backgrounds, using perceived luminance (`(R*299 + G*587 + B*114) / 1000 > 155` threshold). |
| `getColorWithOpacity()` | `(float $opacity = 0.5): string` | Returns the color as `rgba(r, g, b, $opacity)` for use in CSS. |

## Configuration / Contract

No interface required. The using model's table should have a `color` varchar column. The default color `#3788d8` (a mid-blue) is used when the column is null.

## Used By

Discoverable by grepping `traits:` frontmatter for `HasColor` across model docs, or `use HasColor` in Everspot source.
