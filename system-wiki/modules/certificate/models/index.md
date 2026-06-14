---
title: Certificate Module — Models
module: Certificate
last_updated: 2026-06-14
---

# Certificate Module — Models

Three concrete Eloquent models in the Certificate module. All use the `tenant` connection.

| Model | Table | Description |
|-------|-------|-------------|
| [Certificate](./certificate.md) | `certificates` | Official cemetery certificate issued to one or more customers, tracking lifecycle from pending through issued/voided |
| [CertificateCustomer](./certificate-customer.md) | `certificate_customers` | Pivot-with-extras linking a Certificate to a Customer; holds a snapshot of the customer's name and an optional address |
| [CertificateLine](./certificate-line.md) | `certificate_lines` | Individual line item on a certificate; records a product or property right, with optional linkage to a LiabilityLine |
