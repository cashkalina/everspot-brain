---
title: Recognition Module
module: Recognition
last_updated: 2026-06-14
---

# Recognition Module

The Recognition module implements revenue and expense recognition workflows for Everspot. It provides the infrastructure for deferring income/expenses at point-of-sale and progressively recognizing them over time (straight-line, event-triggered, or custom schedules), with full general-ledger integration.

## Purpose

Cemetery operations often involve pre-need contracts — goods and services paid in advance but delivered (and therefore recognizable) in the future. The Recognition module manages this lifecycle: capturing the obligation at sale time, tracking the trigger conditions and schedule that govern when amounts can be recognized, and generating the journal entries that move deferred amounts to income/expense accounts.

## Directory Structure

```
modules/recognition/
├── models/         # All model documentation (4 models)
│   ├── index.md
│   ├── recognition-approval.md
│   ├── recognition-arrangement.md
│   ├── recognition-element.md
│   └── recognition-rule.md
└── traits/         # Module-owned trait documentation
    └── has-recognition.md
```

## Models

See [models/index.md](./models/index.md) for the full model list and relationship diagram.

| Model | Role |
|-------|------|
| [RecognitionRule](./models/recognition-rule.md) | Template: defines trigger, period, and GL account configuration |
| [RecognitionArrangement](./models/recognition-arrangement.md) | Instance: one obligation per recognizable entity, tracks deferral→recognition lifecycle |
| [RecognitionElement](./models/recognition-element.md) | Posting: one entry per recognition event, gates GL posting via ready/approved states |
| [RecognitionApproval](./models/recognition-approval.md) | Batch approval: authorizes a group of elements for posting |

## Traits

| Trait | Owned here | Registry entry |
|-------|-----------|---------------|
| [HasRecognition](../../system/traits/index.md#hasrecognition) | Yes — `modules/Recognition/Traits/HasRecognition.php` | [has-recognition.md](./traits/has-recognition.md) |

## Observers

All model-level lifecycle events are dispatched from observers registered in `RecognitionServiceProvider::registerObservers()`:

| Observer | Model | Key events dispatched |
|----------|-------|----------------------|
| `RecognitionApprovalObserver` | RecognitionApproval | `RecognitionApprovalDeleting` |
| `RecognitionArrangementObserver` | RecognitionArrangement | `RecognitionArrangementSaved`, `RecognitionArrangementCreated`, `RecognitionArrangementDeleting` |
| `RecognitionElementObserver` | RecognitionElement | `RecognitionElementSaved`, `RecognitionElementDeleting` |

## Related Modules

- **Accounting** — `GlAccount` and `JournalEntry` models are the GL-side targets of recognition postings
- **Product** — products attach to `RecognitionRule` records via the `recognition_rulables` pivot
- Any module using [HasRecognition](../../system/traits/index.md#hasrecognition) (e.g. Order, Contract) generates arrangements through this module
