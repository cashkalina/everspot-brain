---
title: Recognition Module — Models
module: Recognition
last_updated: 2026-06-14
---

# Recognition Module — Models

This directory documents all concrete Eloquent models in `modules/Recognition/Models/`. All models use the **tenant** database connection.

## Models

| Model | Table | Description |
|-------|-------|-------------|
| [RecognitionApproval](./recognition-approval.md) | `recognition_approvals` | Batch approval record authorizing a set of recognition elements for GL posting |
| [RecognitionArrangement](./recognition-arrangement.md) | `recognition_arrangements` | Central record for a single recognition obligation; tracks lifecycle from deferral to full recognition |
| [RecognitionElement](./recognition-element.md) | `recognition_elements` | A single discrete recognition posting within an arrangement; progresses through ready → approved → posted states |
| [RecognitionRule](./recognition-rule.md) | `recognition_rules` | Reusable recognition schedule template; attached to products and other entities via the polymorphic `recognition_rulables` pivot |

## Key Relationships

```
RecognitionRule ──── recognition_rulables (pivot) ──── Product (and others)
        │
        └─ snapshot → RecognitionArrangement.rule (JSON)
                             │
                             ├─ recognizable (morphTo) → any HasRecognition entity
                             ├─ cancellable (morphTo)  → cancellation entity
                             ├─ GlAccount (×3: deferral / recognition / offset)
                             ├─ JournalEntry (deferral)
                             └─ RecognitionElement (hasMany)
                                       │
                                       ├─ recognizable (morphTo)
                                       ├─ RecognitionApproval (belongsTo)
                                       └─ JournalEntry (belongsTo, posted)
```

## Trait

The [HasRecognition](../../../system/traits/index.md#hasrecognition) trait (deep doc: [`modules/recognition/traits/has-recognition.md`](../traits/has-recognition.md)) is owned by this module and added to any model that participates as a recognizable entity. It wires up the polymorphic `recognitionArrangements` / `recognitionElements` relationships and the `updatedRecognizable()` cascade.
