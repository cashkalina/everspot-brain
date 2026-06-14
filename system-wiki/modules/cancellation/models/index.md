---
title: Cancellation Models
module: Cancellation
last_updated: 2026-06-14
---

# Cancellation Models

Models in the Cancellation module manage the reversal of prior sales, unbinding liability lines and reversing financial totals.

| Model | Table | Connection | Description |
|-------|-------|------------|-------------|
| [Cancellation](./cancellation.md) | `cancellations` | tenant | A cancellation record grouping line items and tracking financial totals |
| [CancellationLine](./cancellation-line.md) | `cancellation_lines` | tenant | A single item line within a cancellation, linked to a LiabilityLine |
