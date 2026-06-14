---
model: Report
module: Report
table: reports
connection: tenant
primary_source: modules/Report/Models/Report.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Report/Observers/ReportObserver.php
  - modules/Report/Providers/ReportServiceProvider.php
traits:
  - HasByUserFields
  - HasFactory
  - HasSearch
  - HasSharing
  - SoftDeletes
related_models: [ReportChart]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [reporting, admin]
---

# Report

## Overview

The Report model is the central configuration record for the Everspot reporting system. Each row represents a saved report definition that users can build, name, share, and re-run against live tenant data. Reports are built around a target `model_class` — the fully-qualified PHP class name of the Eloquent model being queried — and store all user-facing configuration as serialized JSON.

The module supports two report format generations side-by-side. V1 reports store their configuration in the legacy `columns`, `filters`, `sort_by`, `group_by`, `criteria`, and `related_records` JSON columns. V2 reports use the newer `column_config`, `filter_config`, `sort_config`, and `grouping_config` columns instead; a report is considered V2 only when it carries V2 configuration _and_ all V1 fields are null or empty. The `getVersion()` / `isV1()` / `isV2()` methods implement this detection logic, and `migrateToV2()` performs an in-place upgrade.

Reports may have one or more associated [ReportChart](./report-chart.md) records that apply chart-specific grouping and style configuration on top of the base report query. Sharing is fine-grained and managed through the [HasSharing](../../../system/traits/index.md#hassharing) trait. Soft deletes keep report definitions recoverable after accidental deletion. Activity logging (inherited from BaseModel) is supplemented by the model's own `getActivitylogOptions()` override and two `MorphMany` log accessors — `executionLogs()` and `exportLogs()` — that retrieve execution and export events from Spatie's activity log.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| title | varchar | No | - | User-facing report name |
| subtitle | varchar | Yes | - | Optional subtitle |
| description | text | Yes | - | Optional description |
| model_class | varchar | No | - | Fully-qualified PHP class of the target Eloquent model |
| column_config | json | Yes | - | V2 column configuration |
| filter_config | json | Yes | - | V2 filter configuration |
| sort_config | json | Yes | - | V2 sort configuration |
| grouping_config | json | Yes | - | V2 grouping configuration |
| filters | json | Yes | - | V1 legacy filter definitions |
| criteria | json | Yes | - | V1 legacy criteria |
| group_by | json | Yes | - | V1 legacy grouping |
| sort_by | json | Yes | - | V1 legacy sort order |
| columns | json | Yes | - | V1 legacy column definitions |
| related_records | json | Yes | - | V1 legacy related record configuration |
| default_tab_key | varchar | Yes | - | Default UI tab to show when opening the report |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Indexes:** `model_class` (`reports_report_class_index`), `title` (`reports_title_index`); FK-backing indexes on `created_by`, `updated_by`, `deleted_by`.

**Foreign keys:** `created_by`, `updated_by`, `deleted_by` → `users.id`

## Casts

- `criteria` → `array`
- `filters` → `array`
- `columns` → `array`
- `related_records` → `array`
- `group_by` → `array`
- `sort_by` → `array`
- `column_config` → `array`
- `filter_config` → `array`
- `sort_config` → `array`
- `grouping_config` → `array`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants:**
```php
const VERSION_1 = 'v1';
const VERSION_2 = 'v2';
```

## Accessors & Mutators

- `getFormattedModelAttribute(): string` — resolves `model_class` (or legacy `report_class`) to a human-readable title via `getModelNameTitle()`; returns `'Unknown'` if the class does not exist
- `getModelInferredName(): ?string` — returns `$this->title` (used by framework conventions for display naming)
- `getModelFullTitle(): ?string` — overrides BaseModel default; returns `$this->title` directly, omitting the `"Report #X - "` prefix

## Traits

- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps backed by `created_by` / `updated_by` / `deleted_by` columns
- [HasFactory](../../../system/traits/index.md#hasfactory) — model factory hook for test and seeder use
- [HasSearch](../../../system/traits/index.md#hassearch) — Scout search indexing for report titles and descriptions
- [HasSharing](../../../system/traits/index.md#hassharing) — fine-grained sharing of report definitions with users, roles, cemeteries, or departments
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — reports are soft-deleted (`deleted_at`), never hard-deleted

## Relationships

- `charts()` — has many [ReportChart](./report-chart.md): all charts attached to this report
- `activeCharts()` — has many [ReportChart](./report-chart.md) (filtered `is_active = true`, ordered by `position`): the charts displayed when the report is rendered
- `executionLogs()` — morphMany via `activities()` scoped to `event = 'executed'`: Spatie activity log entries for report executions
- `exportLogs()` — morphMany via `activities()` scoped to `event = 'exported'`: Spatie activity log entries for report exports

## Scopes

_None._

## Events

_None defined on the model._ Lifecycle behavior is handled by `ReportObserver` (see Observers). Activity logging is configured via `getActivitylogOptions()`.

## Observers

- `ReportObserver` — registered in `ReportServiceProvider::registerObservers()` (`Report::observe(ReportObserver::class)`). Handles:
  - `deleted` — deletes all `Metadata` records associated with this report (`on_type` / `on_id` match)
  - `restored` — restores soft-deleted `Metadata` records associated with this report
  - `forceDeleted` — permanently deletes all `Metadata` records (including trashed) for this report

## Key Methods

- `toReportInstance(): ReportInstance` — converts this model into a `ReportInstance` value object (via `ReportInstance::fromModel($this)`) for query execution
- `getVersion(): string` — returns `VERSION_1` or `VERSION_2`; V2 requires `column_config` non-null and all V1 fields null/empty
- `isV2(): bool` — convenience wrapper around `getVersion()`
- `isV1(): bool` — convenience wrapper around `getVersion()`
- `migrateToV2(): bool` — maps V1 fields to V2 equivalents (`columns` → `column_config`, `filters` → `filter_config`, `sort_by` → `sort_config`, `group_by` → `grouping_config`) and saves; no-op if already V2; throws on failure
- `lastExecutedAt(): ?Carbon` — global last-execution timestamp via `Metadata::getGlobalLastRun($this)`
- `lastExecutedByUser(User $user): ?Carbon` — per-user last-execution timestamp via `Metadata::getUserLastRun($this, $user)`
- `getLastRunBy(): ?User` — returns the `User` who most recently ran this report (across all users), by finding the per-user `Metadata` record with the latest `performed_at`
- `getActivitylogOptions(): LogOptions` — configures Spatie Activitylog to record all dirty fields, excluding `created_at` / `updated_at`

## Common Usage

```php
// Create a V2 report
$report = Report::create([
    'title'         => 'Monthly Payments',
    'model_class'   => \Modules\Transaction\Models\Payment::class,
    'column_config' => [/* V2 column definitions */],
    'filter_config' => [/* V2 filter definitions */],
]);

// Check version and execute
if ($report->isV2()) {
    $instance = $report->toReportInstance();
    // run query via $instance
}

// Migrate a legacy V1 report
if ($report->isV1()) {
    $report->migrateToV2();
}

// Get active charts in display order
$charts = $report->activeCharts()->get();

// Audit usage
$user = $report->getLastRunBy();
$when = $report->lastExecutedAt();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
