---
model: ReportChart
module: Report
table: report_charts
connection: tenant
primary_source: modules/Report/Models/ReportChart.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Report/Models/Report.php
traits:
  - HasByUserFields
  - LogsActivity
related_models: [Report]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [reporting, admin]
---

# ReportChart

## Overview

ReportChart stores a visual chart definition attached to a parent [Report](./report.md). Each chart specifies a chart type (discriminated by the `ChartType` enum), an optional grouping configuration that overrides or extends the parent report's grouping, and style configuration for rendering. Charts are ordered by `position` and toggled with `is_active`.

The model's `toReportInstance()` method is the key integration point: it clones the parent report's `ReportInstance` and injects the chart's own `grouping_config` before returning, allowing a single underlying report definition to power multiple chart views with different aggregation axes.

`isCompatibleWithReport()` provides a runtime check that validates chart grouping field references against the current report definition — returning `false` when a previously valid field no longer exists (e.g., after the report's `model_class` is changed). The `duplicate()` method provides a convenience clone with an auto-incremented position.

Activity logging is configured explicitly on the class (not inherited from BaseModel alone) via `getActivitylogOptions()`, recording all dirty fields except timestamps.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| report_id | bigint | No | - | FK → reports: parent report |
| name | varchar | No | - | Display name for the chart |
| chart_type | varchar | No | - | Chart type discriminator (cast to `ChartType` enum) |
| grouping_config | json | Yes | - | Chart-specific grouping overrides; falls back to parent report groupings when null |
| style_config | json | Yes | - | Visual styling options (colors, labels, etc.) |
| is_active | tinyint | No | 1 | Whether the chart is shown when the report is rendered |
| position | int | Yes | - | Display order among charts on the same report |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp |

**Primary key:** `id`

**Indexes:** `report_id` (`report_charts_report_id_index`); composite `(report_id, position)` (`report_charts_report_id_position_index`); FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Foreign keys:** `report_id` → `reports.id` (cascade delete); `created_by`, `updated_by`, `deleted_by` → `users.id` (set null)

## Casts

- `chart_type` → `ChartType::class` (enum)
- `grouping_config` → `array`
- `style_config` → `array`
- `is_active` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** `is_active` defaults to `1` (active) at the database level.

## Accessors & Mutators

_None._

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backed by `created_by` / `updated_by` / `deleted_by` columns
- [LogsActivity](../../../system/traits/index.md#logsactivity) — Spatie Activitylog: explicitly declared on this class to override the inherited BaseModel configuration via `getActivitylogOptions()`

## Relationships

- `report()` — belongs to [Report](./report.md): the parent report this chart visualizes

## Scopes

_None._

## Events

_None._

## Observers

_None registered._

## Key Methods

- `getGroupingConfig(): GroupingCollection` — returns the chart's own `GroupingCollection` if `grouping_config` is set; otherwise delegates to the parent report's instance groupings
- `isCompatibleWithReport(): bool` — validates that all grouping fields in this chart still exist in the parent report's current definition; returns `false` on any missing field or exception
- `toReportInstance(): ReportInstance` — builds a `ReportInstance` from the parent report and injects this chart's `grouping_config`, producing a query-ready instance scoped to the chart's grouping
- `duplicate(): self` — replicates this chart with a `' (Copy)'` name suffix and position incremented past the current max; saves and returns the copy
- `getActivitylogOptions(): LogOptions` — configures Spatie Activitylog to record all dirty fields except `created_at` / `updated_at`

## Common Usage

```php
// Get all active charts for a report, in order
$charts = $report->activeCharts()->with('report')->get();

// Execute a chart's query
$instance = $chart->toReportInstance();
// run query via $instance

// Check compatibility before rendering
if (!$chart->isCompatibleWithReport()) {
    // warn user chart references deleted fields
}

// Get the effective grouping (chart-specific or inherited)
$groupings = $chart->getGroupingConfig();

// Duplicate a chart
$copy = $chart->duplicate();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
