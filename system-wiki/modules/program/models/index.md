---
title: Program Module — Models Index
module: Program
last_updated: 2026-06-14
---

# Program Module — Models

This directory contains documentation for all concrete Eloquent models in the Everspot `Program` module (`modules/Program/Models/`). All models use the **tenant** database connection.

## Model List

| Model | Table | Description |
|-------|-------|-------------|
| [Program](./program.md) | `programs` | Program template defining a recurring-service offering (type, pricing, scheduling defaults) |
| [ProgramEnrollment](./program-enrollment.md) | `program_enrollments` | A customer's enrollment in a specific program at a cemetery |
| [ProgramObligation](./program-obligation.md) | `program_obligations` | A single scheduled service obligation arising from an enrollment |
| [ProgramObligationPreference](./program-obligation-preference.md) | `program_obligation_preferences` | A single customer preference selection within a preference-collection response |
| [ProgramObligationPreferenceCollection](./program-obligation-preference-collection.md) | `program_obligation_preference_collections` | Per-obligation response container for a preference-collection workflow |
| [ProgramPreferenceCollection](./program-preference-collection.md) | `program_preference_collections` | Template defining when and how preferences are collected for a program's obligations |
| [ProgramPreferenceCollectionOption](./program-preference-collection-option.md) | `program_preference_collection_options` | A single selectable option within a preference-collection template |

## Model Relationships Overview

```
Program
  ├── has many → ProgramPreferenceCollection
  ├── belongs to many → Cemetery
  ├── morph to many → GlAccount
  └── belongs to → Product

ProgramEnrollment (belongs to Program, Customer, Cemetery, Product)
  ├── has many → ProgramObligation
  └── morph to many → GlAccount

ProgramObligation (belongs to ProgramEnrollment)
  └── has one → ProgramObligationPreferenceCollection

ProgramObligationPreferenceCollection (belongs to ProgramObligation, ProgramPreferenceCollection)
  └── [inverse: ProgramObligationPreference.popc_id]

ProgramPreferenceCollection (belongs to Program)
  └── has many → ProgramPreferenceCollectionOption

ProgramPreferenceCollectionOption (belongs to ProgramPreferenceCollection)
  └── [inverse: ProgramObligationPreference.ppco_id]

ProgramObligationPreference (belongs to ProgramObligationPreferenceCollection, ProgramPreferenceCollectionOption)
```

## Observers Registered

| Model | Observer | Registration |
|-------|----------|-------------|
| Program | `ProgramObserver` | `ProgramServiceProvider::registerObservers()` |
| ProgramEnrollment | `ProgramEnrollmentObserver` | `ProgramServiceProvider::registerObservers()` |
| ProgramObligation | `ProgramObligationObserver` | `ProgramServiceProvider::registerObservers()` |
| ProgramObligationPreference | — | _None registered_ |
| ProgramObligationPreferenceCollection | — | _None registered_ |
| ProgramPreferenceCollection | — | _None registered_ |
| ProgramPreferenceCollectionOption | — | _None registered_ |
