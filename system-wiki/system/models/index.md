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

- [User](./user.md) — System users with authentication and tenant access (central)
