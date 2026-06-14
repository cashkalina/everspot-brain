---
title: Commission Module
module: Commission
last_updated: 2026-06-14
---

# Commission Module

The Commission module manages sales commission structures, calculations, and payouts for cemetery sales representatives. It covers the full lifecycle from defining commission plans and rates, tracking what is owed per sale, through batched approval and payment disbursement.

## Models

See [models/index.md](./models/index.md) for the full model list.

**7 models:**
- [Commission](./models/commission.md) — individual payout record
- [CommissionApproval](./models/commission-approval.md) — batched approval/release event
- [CommissionCalculation](./models/commission-calculation.md) — per-sale per-rep accounting record
- [CommissionCategory](./models/commission-category.md) — reference data categories
- [CommissionPlan](./models/commission-plan.md) — plan grouping reps and rate rules
- [CommissionRate](./models/commission-rate.md) — rate rule defining commission structure
- [RepAssociation](./models/rep-association.md) — polymorphic rep-to-sale link

## Observers

| Observer | Model | Registered in |
|----------|-------|---------------|
| `CommissionObserver` | Commission | `CommissionServiceProvider` |
| `CommissionCalculationObserver` | CommissionCalculation | `CommissionServiceProvider` |
| `CommissionRateObserver` | CommissionRate | `CommissionServiceProvider` |
| `RepAssociationObserver` | RepAssociation | `CommissionServiceProvider` |

## Key Module Files

- **Service Provider:** `modules/Commission/Providers/CommissionServiceProvider.php`
- **Observers:** `modules/Commission/Observers/`
- **Enums:** `modules/Commission/Enums/` (`Role`, `Type`, `PaidAt`, `PaidOn`)
- **Pivots:** `modules/Commission/Pivots/` (`CommissionPlanUserPivot`, `CommissionPlanCommissionRatePivot`)
- **Commands:** `CommissionsCheck`, `ReprocessAllCommissions`
