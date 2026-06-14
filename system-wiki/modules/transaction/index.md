---
title: Transaction Module
purpose: Financial transactions and payment processing
last_updated: 2026-06-12
---

# Transaction Module

The Transaction module is the core financial engine of the Everspot cemetery management system. It handles all monetary transactions including payments, refunds, charges, credits, and various other transaction types. The module implements Single Table Inheritance (STI) to manage different transaction types within a unified transactions table while providing type-specific behavior through specialized model classes.

## Overview

This module manages the complete lifecycle of financial transactions:
- **Payment processing** through multiple methods (cash, check, credit card, ACH)
- **Refund management** including automatic and manual refunds
- **Transaction posting** to accounting systems via journal entries
- **Payment method storage** and management
- **Deposit batching** for bank reconciliation
- **Reversals and adjustments** to correct or void transactions

The Transaction module integrates with payment processors for live payment processing and supports both tenant-specific and multi-tenant payment gateway configurations.

## Models

This module contains 6 concrete Eloquent models:

### Core Transaction Models
- **Transaction** — Base transaction model using Single Table Inheritance *(doc pending Bootstrap)*
- **Payment** — Customer payment transactions (extends Transaction) *(doc pending Bootstrap)*
- **Refund** — Refund transactions (extends Transaction) *(doc pending Bootstrap)*

### Supporting Models
- **[PaymentMethod](./models/payment-method.md)** — Stored payment methods (credit cards, bank accounts)
- **[PaymentMethodRequest](./models/payment-method-request.md)** — Requests for adding new payment methods
- **[DepositBatch](./models/deposit-batch.md)** — Batches of transactions for bank deposits

## Key Features

### Single Table Inheritance
The Transaction base model uses STI to store multiple transaction types in a single table:
- `payment` — Customer payments
- `refund` — Refunds issued to customers
- `charge` — Charges applied to customer accounts
- `credit` — Credits applied to customer accounts
- `interest` — Interest charges
- `processing-fee` — Payment processing fees
- `financing-transfer` — Transfer between financing arrangements
- `cancellation-credit` — Credits from cancelled services

Each type has a dedicated model class (Payment, Refund) or uses the base Transaction model directly.

### Transaction Status Flow
Transactions progress through a standardized status lifecycle:
1. **pending** — Initial state
2. **processing** — Being processed
3. **action-required** — Requires user intervention
4. **posted** — Successfully completed and posted
5. **failed** — Processing failed
6. **refunded** — Fully refunded
7. **reversed** — Voided/reversed

### Payment Methods
The module supports multiple payment methods:
- **Cash** — Physical cash payments
- **Check** — Check payments with check number tracking
- **Credit Card** — Card payments via integrated gateways
- **ACH** — Bank account debits
- **Other** — Custom payment methods

Credit card and ACH payments are considered "live" methods and integrate with payment processors for real-time processing.

### Relationships & Integration
- **Polymorphic associations** — Transactions can belong to Orders, PaymentPlans, or other entities via `transactionable`
- **Customer linkage** — All transactions link to the Customer who originated them
- **Journal entries** — Integration with Accounting module for double-entry bookkeeping
- **Deposit batches** — Grouping for bank reconciliation workflows

## Architecture Notes

### Global Scopes
Payment and Refund models use `TransactionByTypeScope` to automatically filter queries to their respective types, ensuring type safety when working with STI models.

### Traits Used
- `HasModelNumbering` — Auto-generates transaction numbers
- `HasByUserFields` — Tracks created_by and updated_by users
- `HasMoneyFields` — Handles money arithmetic and formatting
- `HasSearch` — Enables search functionality
- `HasSyncables` — Supports external system synchronization

### Events
The module dispatches events for key transaction lifecycle moments:
- `PaymentSuccessful` — Payment completed
- `PaymentFailed` — Payment processing failed
- `PaymentRequiresAction` — User action needed for payment
- `RefundFailed` — Refund processing failed
- `RefundRequiresAction` — User action needed for refund

## Coverage

**Pending Bootstrap:**
- Transaction, Payment, Refund, PaymentMethod, PaymentMethodRequest, DepositBatch — Listed in module inventory; full documentation generated during Bootstrap.

## Related Modules
- **Customer** — Customer entities making payments
- **Order** — Orders that payments are applied to
- **PaymentPlan** — Payment plans with scheduled payments
- **Accounting** — Journal entries and financial posting
- **Autopay** — Automated recurring payment processing
