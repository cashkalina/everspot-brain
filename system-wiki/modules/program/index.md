---
title: Program Module
module: Program
last_updated: 2026-06-14
---

# Program Module

The Program module manages recurring-service programs offered by cemeteries — such as perpetual care or grounds-maintenance plans. It covers the full lifecycle from program template configuration through customer enrollment, obligation scheduling, and preference collection.

## Structure

```
modules/program/
└── models/        # 7 documented models (see models/index.md)
```

## Models

See [models/index.md](./models/index.md) for the full model list and relationship overview.

## Key Concepts

- **Program** — the configuration template (type, pricing, schedules). Cemeteries select which programs they offer.
- **ProgramEnrollment** — a customer's enrollment in a program at a specific cemetery. Created from a Program template; drives obligation generation.
- **ProgramObligation** — a single scheduled service event arising from an enrollment. Carries its own fulfillment tracking dates (via `HasDateStatusFields`).
- **Preference Collection** — a two-layer system for gathering customer service-preference selections:
  - **ProgramPreferenceCollection** / **ProgramPreferenceCollectionOption** — the template side (belongs to Program; defines when and what options are offered).
  - **ProgramObligationPreferenceCollection** / **ProgramObligationPreference** — the response side (per obligation; records customer selections).

## Module Provider

`modules/Program/Providers/ProgramServiceProvider.php` — registers observers for Program, ProgramEnrollment, and ProgramObligation; bootstraps migrations, config, views, components, and sub-providers (RouteServiceProvider, EventServiceProvider).

## Event Wiring

`modules/Program/Providers/EventServiceProvider.php` maps:
- `ProgramObligationCreated` → `CreateTrustArrangementForObligation`, `CreateRecArrangementForObligation`
- `ProgramEnrollmentCreated` → `CreateTrustArrangementForEnrollment`
