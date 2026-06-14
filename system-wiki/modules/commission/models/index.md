---
title: Commission Module — Models Index
module: Commission
last_updated: 2026-06-14
---

# Commission Module — Models

This directory contains documentation for all 7 concrete Eloquent models in the Commission module.

| Model | Table | Description |
|-------|-------|-------------|
| [Commission](./commission.md) | `commissions` | Individual commission payout record for a sales rep |
| [CommissionApproval](./commission-approval.md) | `commission_approvals` | Batched approval event that releases commission payouts |
| [CommissionCalculation](./commission-calculation.md) | `commission_calculations` | Core accounting record tracking what commission is owed, paid, and due |
| [CommissionCategory](./commission-category.md) | `commission_categories` | Reference data: named categories for organizing commissions |
| [CommissionPlan](./commission-plan.md) | `commission_plans` | Named plan associating reps and rate rules with date-range effectivity |
| [CommissionRate](./commission-rate.md) | `commission_rates` | Rate rule defining how much commission is earned and under what conditions |
| [RepAssociation](./rep-association.md) | `rep_associations` | Polymorphic link between a sales rep and a saleable entity |

## Commission Lifecycle

1. A sale is recorded (e.g. a [LiabilityLine](../../liability/models/liability-line.md))
2. A **RepAssociation** is created linking the rep(s) to the sale
3. The applicable **CommissionPlan** and **CommissionRate** are resolved for each rep
4. A **CommissionCalculation** is created tracking `eligible_amt`, `paid_amt`, and `due_amt`
5. A manager creates a **CommissionApproval** batch
6. Individual **Commission** payout records are issued under the approval, paying down the calculation's `due_amt`
