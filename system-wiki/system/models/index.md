---
title: System Models
purpose: Documentation for models in app/Models/
module: System
last_updated: 2026-06-14
---

# System Models

This directory contains documentation for Eloquent models in Everspot's `app/Models/` directory — the core Laravel models that are used across the entire application.

## Overview

System models typically include:
- User and authentication models
- Tenant models (for multi-tenancy)
- Plan and feature models
- System-wide foundational models

These models are distinguished from module-specific models which live in `modules/*/Models/`.

## Documented Models

| Model | Table | Connection | Description |
|-------|-------|------------|-------------|
| [Feature](./feature.md) | `features` | central | Capability flag / typed key-value pair belonging to a Plan |
| [Plan](./plan.md) | `plans` | central | Subscription tier; groups Feature records; assigned to each Tenant |
| [User](./user.md) | `users` | central | Central admin/staff account; auth, 2FA, Sanctum tokens (NOT the tenant-side user) |
