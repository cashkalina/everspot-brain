---
title: Property Module
module: Property
last_updated: 2026-06-14
---

# Property Module

The Property module manages cemetery inventory — the interment spaces (lots, niches, mausoleum crypts, etc.) that a cemetery sells or reserves for customers.

## Structure

```
modules/Property/
├── Models/
│   ├── Property.php               → property.md
│   ├── PropertyCommitment.php     → property-commitment.md
│   ├── PropertyGroup.php          → property-group.md
│   └── PropertyType.php           → property-type.md
├── Observers/
│   ├── PropertyObserver.php
│   ├── PropertyCommitmentObserver.php
│   ├── PropertyGroupObserver.php
│   └── PropertyTypeObserver.php
└── Providers/
    └── PropertyServiceProvider.php
```

## Docs

- [Models](./models/index.md) — all 4 documented models
