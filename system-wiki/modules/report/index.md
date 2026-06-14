---
title: Report Module
module: Report
last_updated: 2026-06-14
---

# Report Module

The Report module provides a configurable reporting engine that allows users to build, save, share, and re-run queries against any Eloquent model in the system. It supports two report format generations (V1 legacy and V2 structured configuration) and an optional charting layer.

## Models

See [models/index.md](./models/index.md) for the full model list.

| Model | Table | Description |
|-------|-------|-------------|
| [Report](./models/report.md) | `reports` | Saved report definition |
| [ReportChart](./models/report-chart.md) | `report_charts` | Chart definition attached to a Report |

## Key Concepts

- **V1 vs V2 reports** — V1 reports use legacy `columns`, `filters`, `sort_by`, `group_by`, `criteria`, `related_records` JSON columns. V2 reports use `column_config`, `filter_config`, `sort_config`, `grouping_config`. The `Report::getVersion()` method detects the active format. Migration is performed by `Report::migrateToV2()`.
- **ReportInstance** — `Report::toReportInstance()` converts a saved definition to a `ReportInstance` value object used for query execution (see `modules/Report/Core/ReportInstance.php`).
- **ReportRegistry** — singleton registered in `ReportServiceProvider` that discovers and caches standard report definitions from all modules.
- **Sharing** — Reports use [HasSharing](../../system/traits/index.md#hassharing) for fine-grained access control.
