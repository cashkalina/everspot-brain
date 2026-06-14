---
title: Module Documentation
purpose: Per-module model documentation
last_updated: 2026-06-12
---

# Module Documentation

This is the **primary focus** of the Everspot System Wiki. Each Everspot module has a subdirectory here containing documentation for all models in that module.

## Structure

```
modules/
  [module-name]/           # One directory per Everspot module (kebab-case)
    index.md               # Module overview
    models/                # Model documentation for this module
      index.md             # Model index for this module
      [model-name].md      # One file per model (kebab-case)
```

## Modules

Module directories will be created during bootstrap/sync operations as models are discovered in the Everspot codebase.

Each module directory maps to a module in Everspot's `modules/` directory.

## Coverage

To check which modules and models are documented, run the audit (see `meta/commands/audit.md`).

---

**Status:** Placeholder directory for Phase 1. Module subdirectories and model documents will be created during bootstrap/sync operations.
