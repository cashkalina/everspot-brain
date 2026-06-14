---
title: Delivery Models
module: Delivery
last_updated: 2026-06-14
---

# Delivery Models

Models in the Delivery module manage the transfer of goods from inventory to their destination (customer or storage).

| Model | Table | Connection | Description |
|-------|-------|------------|-------------|
| [Delivery](./delivery.md) | `deliveries` | tenant | A delivery record grouping line items and tracking status |
| [DeliveryLine](./delivery-line.md) | `delivery_lines` | tenant | A single item line within a delivery, linked to a LiabilityLine |
