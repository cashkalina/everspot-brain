---
title: Update Command
purpose: Force-regenerate a single existing model document, ignoring freshness
last_updated: 2026-06-14
---

# Update

**Purpose:** Force-regenerate a single existing model document, ignoring freshness.

**Operation type:** Write

**Inputs:**
- Model document path (e.g., `modules/transaction/models/payment.md`) OR model name (e.g., `Payment`)
- Implicit: same as [Generate](./generate.md)

**Preconditions:**
- The document exists
- Schema snapshots exist and are current

**Process:**

1. If input is a model name, locate the document by grepping frontmatter for `model: <name>`.
2. Perform the same regeneration as [Generate](./generate.md), but for an existing file:
   - Re-derive `primary_source`, `source_paths`, `traits`, and `related_models`
   - Re-render Schema from snapshot (with trait-column provenance markers)
   - Re-parse relationships, methods, attributes, scopes, events, observers
   - Preserve human-content blocks (same as [Sync › Human-content reconciliation](./sync.md#human-content-reconciliation))
   - Validate
   - Stamp `built_at` with current `origin/main` commit
3. Write the updated file.

**Use cases:**
- Manual refresh of a single document after reviewing it
- Fixing a document with known issues
- Testing template changes on a single document before a full sync

**Outputs:**
- Updated `.md` file, validated and stamped

**Error handling:**
- Document not found — fail with clear error
- Same validation and error handling as [Generate](./generate.md)
