---
title: Interment Module
purpose: Overview of the Interment module and its documentation
last_updated: 2026-06-14
---

# Interment Module

The Interment module manages cemetery burial and placement services. It tracks the full interment lifecycle from initial record creation through scheduling, documentation, and completion. Core concepts include the identification of the deceased and associated parties (next of kin, funeral home, funeral director), partial-date storage for dates of birth/death/interment, scheduling via Events, and workflow status progression.

## Models

- [Interment](./models/interment.md) — the central burial record with deceased demographics, scheduling, property linkage, and workflow.

## Module-owned traits

_None._

## Related modules

- [Customer](../customer/index.md) — deceased, NOK, funeral home, and funeral director are all Customer records
- [Event](../event/index.md) — scheduling events linked to interments
- [Property](../property/index.md) — the interment space (property)
- [Certificate](../certificate/index.md) — burial certificates linked to interments
- [Memorial](../memorial/index.md) — memorials created from interment records
- [WorkOrder](../work-order/index.md) — work orders for interment preparation
