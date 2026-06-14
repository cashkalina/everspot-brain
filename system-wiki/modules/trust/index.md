---
title: Trust Module
module: Trust
last_updated: 2026-06-14
---

# Trust Module

The Trust module manages cemetery pre-need trust fund accounting. It provides the full lifecycle for tracking trust obligations: from schedule configuration and per-contract arrangements through element-level approval staging to posted transactions on the trust account.

## Directories

- [models/](./models/index.md) — 10 concrete Eloquent models (trust accounts, arrangements, elements, transactions, approvals, types, strategies, schedules)
- [traits/](./traits/has-trusting.md) — `HasTrusting` trait owned by this module; enables other models to participate as trust arrangeables

## Key Concepts

- **TrustAccount** — the root entity; a bank account classified as Merchandise/Services or Perpetual Care
- **TrustingSchedule** — defines calculation rules (fixed dollar, % revenue, % cost) for computing what goes into trust per product
- **TrustArrangement** — the per-contract trust record linking an arrangeable (order, property commitment, etc.) to a trust account
- **TrustElement** — atomic deposit/withdrawal line item generated when an arrangement trigger fires
- **TrustApproval** — batches ready elements for administrator review before posting
- **TrustAccountTransaction** — the finalized, posted ledger entry created from an approved batch

## Coverage

| Status | Count |
|--------|-------|
| Documented | 10 |
| Total models | 10 |
| Completeness | complete |
