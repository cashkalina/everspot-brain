---
title: Transaction Models
purpose: Model documentation for Transaction module
last_updated: 2026-06-12
---

# Transaction Module Models

This directory contains documentation for all models in the Transaction module.

## Documented Models

### Phase 4 — Complete Vertical Slice
- **[Payment](./payment.md)** — Customer payment transactions *(completeness: partial)*

### Pending Documentation
The following models have been discovered in the Transaction module but not yet documented:

- **Transaction** — Base transaction model (STI parent) — `modules/Transaction/Models/Transaction.php`
- **Refund** — Refund transactions — `modules/Transaction/Models/Refund.php`
- **PaymentMethod** — Stored payment methods — `modules/Transaction/Models/PaymentMethod.php`
- **PaymentMethodRequest** — Payment method addition requests — `modules/Transaction/Models/PaymentMethodRequest.php`
- **DepositBatch** — Transaction deposit batches — `modules/Transaction/Models/DepositBatch.php`

## Model Enumeration Notes

All models listed follow the enumeration rules from `meta/conventions.md` §"Model Enumeration Rules":
- Concrete (non-abstract) Eloquent classes only
- Located in `modules/Transaction/Models/`
- Exclude traits and abstract base classes
- Include STI child models (Payment, Refund extend Transaction)

## Relationships Map

```
Transaction (base STI model)
  ↳ Payment (extends Transaction)
      → refunds (has many Refund)
      → customer (belongs to Customer)
      → paymentMethod (belongs to PaymentMethod)
      → transactionable (morph to: Order, PaymentPlan, etc.)
      → depositBatch (belongs to DepositBatch)

  ↳ Refund (extends Transaction)
      [inherits all Transaction relationships]

PaymentMethod
  → customer (belongs to Customer)
  → transactions (has many Transaction)
  → autopays (has many Autopay)

DepositBatch
  → transactions (has many Transaction)
```

## Connection Information

All Transaction module models use the **tenant** database connection, as this is a tenant-scoped module managing customer financial transactions within each cemetery's isolated database.
