---
trait: HasDateStatusFields
owning_module: Common
source_paths:
  - modules/Common/Traits/HasDateStatusFields.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasDateStatusFields

**Source:** `modules/Common/Traits/HasDateStatusFields.php`
**Registry entry:** [system/traits/index.md#hasdatestatusfields](../../../system/traits/index.md#hasdatestatusfields)

## Purpose

Adds a date-driven status system to models that track delivery and fulfillment lifecycle through dated events (delivered, constructive delivery, cancellation, deed/certificate issuance). Status is inferred from which date columns are set: the presence of a value in a date column activates its corresponding status.

The default `$dateStatusFields` map is: `delivery_date → delivered`, `constructive_date → constructive`, `cancellation_date → canceled`, `certificate_issuance_date → deeded`. When none of these dates are set, the status defaults to `available`.

The default `$dateStatuses` badge config covers `delivered`, `constructive`, `canceled`, `deeded`, and `available`.

## Contributed Columns

This trait does not define columns itself. It expects the using model's table to include the date columns referenced in `$dateStatusFields` (defaults: `delivery_date`, `constructive_date`, `cancellation_date`, `certificate_issuance_date`). Models may override `$dateStatusFields` to use different column names.

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

| Scope | Signature | Description |
|-------|-----------|-------------|
| `scopeOpen()` | `($query)` | Records where `delivery_date`, `cancellation_date`, and `constructive_date` are all null (not yet fulfilled or canceled). |
| `scopeNotCanceled()` | `($query)` | Records where `cancellation_date` is null. |

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getDateStatusBadgeAttribute()` | `(): string` | Accessor: builds an HTML string of Bootstrap badge spans for all active statuses. |
| `getDateDeliveryStatus()` | `(): string` | Returns a single canonical status string: `'canceled'`, `'delivered'`, `'constructive'`, or `'pending'` (in priority order). |
| `getDateStatuses()` | `(): array` | Returns array of all currently active status strings based on which date columns are set. Returns `['available']` when none are set. |
| `isDateDelivered()` | `(): bool` | `delivery_date` is set. |
| `isDateConstructive()` | `(): bool` | `constructive_date` is set. |
| `isDateCanceled()` | `(): bool` | `cancellation_date` is set. |
| `isDateDeeded()` | `(): bool` | `certificate_issuance_date` is set. |
| `isDateAvailable()` | `(): bool` | No fulfillment dates are set. |
| `isDateFulfilled()` | `(): bool` | `getDateDeliveryStatus()` is not `'pending'`. |

## Configuration / Contract

No interface required. Using models may override:

```php
protected array $dateStatusFields = [
    'delivery_date'           => 'delivered',
    'constructive_date'       => 'constructive',
    'cancellation_date'       => 'canceled',
    'certificate_issuance_date' => 'deeded',
];

protected array $dateStatuses = [
    'delivered'   => ['label' => 'Delivered',          'color' => 'secondary'],
    'constructive' => ['label' => 'Stored Del.',        'color' => 'info'],
    'canceled'    => ['label' => 'Canceled',            'color' => 'danger'],
    'deeded'      => ['label' => 'Certificate Issued',  'color' => 'info'],
    'available'   => ['label' => 'Available',           'color' => 'success'],
];
```

## Used By

Discoverable by grepping `traits:` frontmatter for `HasDateStatusFields` across model docs, or `use HasDateStatusFields` in Everspot source.
