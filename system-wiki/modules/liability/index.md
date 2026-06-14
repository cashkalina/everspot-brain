---
title: Liability Module
purpose: Overview of the Liability module and its documentation
last_updated: 2026-06-14
---

# Liability Module

The Liability module manages individual line items on sales liabilities — products and services sold to customers through the Everspot ordering system. It handles the full item lifecycle from sale through delivery or cancellation, including pricing, date tracking, customer role assignments, certificate issuance, and commission tracking.

## Models

- [LiabilityLine](./models/liability-line.md) — a single sold product or service, with fulfillment lifecycle dates, money fields, and multi-customer pivot support.

## Module-owned traits

_None._

## Related modules

- [Order](../order/index.md) — orders and order lines that generate liability lines
- [Product](../product/index.md) — the products referenced by liability lines
- [Property](../property/index.md) — properties and property groups linked to lines
- [Certificate](../certificate/index.md) — certificates issued via liability lines
- [Delivery](../delivery/index.md) — delivery records for liability lines
- [Cancellation](../cancellation/index.md) — cancellation records for liability lines
- [Recognition](../recognition/index.md) — recognition module integrated via `HasRecognition`
- [Trust](../trust/index.md) — trust module integrated via `HasTrusting`
