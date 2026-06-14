---
title: Certificate Module
module: Certificate
last_updated: 2026-06-14
---

# Certificate Module

The Certificate module manages the creation, issuance, and lifecycle of official cemetery certificates. Certificates document property rights of interment granted to customers, going through an approval-controlled lifecycle (`pending` → `issued` or `voided`). The module provides rich property-grouping utilities for PDF rendering and integrates with the Liability, Property, Interment, and Customer modules.

## Models

See [models/](./models/index.md) for full documentation.

| Model | Table | Role |
|-------|-------|------|
| [Certificate](./models/certificate.md) | `certificates` | The primary certificate record |
| [CertificateCustomer](./models/certificate-customer.md) | `certificate_customers` | Customer-certificate association with name snapshot |
| [CertificateLine](./models/certificate-line.md) | `certificate_lines` | Individual line items (products / property rights) |

## Source Location

`modules/Certificate/` in the Everspot repository.
