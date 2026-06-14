---
trait: HasModificationRules
owning_module: Common
source_paths:
  - modules/Common/Traits/HasModificationRules.php
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
---

# HasModificationRules

**Source:** `modules/Common/Traits/HasModificationRules.php`
**Registry entry:** [system/traits/index.md#hasmodificationrules](../../../system/traits/index.md#hasmodificationrules)

## Purpose

Provides a uniform gate for checking whether a model record can be edited, deleted, voided, submitted for approval, or is locked. The logic is delegated to a `ModificationStrategy` resolved by `ModificationStrategyFactory::create($this)`, keeping business rules about record lifecycle out of the model itself and into swappable strategy classes.

Applied on `BaseModel`, so all concrete Everspot models that extend `BaseModel` inherit it. Each model's strategy determines its rules (e.g. a posted transaction may be locked; a draft may be freely editable).

## Contributed Columns

None. Locking state is typically derived from model status fields or approval records, not a dedicated column contributed by this trait.

## Contributed Casts

None.

## Contributed Relationships

None.

## Contributed Scopes

None.

## Contributed Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `getModificationStrategy()` | `(): ModificationStrategy` | Resolves and returns the strategy instance for this model via `ModificationStrategyFactory`. |
| `canBeEdited()` | `(): bool` | Whether the record may be edited; delegates to strategy. |
| `canBeDeleted()` | `(): bool` | Whether the record may be deleted; delegates to strategy. |
| `canBeVoided()` | `(): bool` | Whether the record may be voided; delegates to strategy. |
| `canBeSubmittedForApproval()` | `(): bool` | Whether the record may be submitted for approval; delegates to strategy. |
| `isLocked()` | `(): bool` | Whether the record is currently locked; delegates to strategy. |

## Configuration / Contract

No interface required on the model. `ModificationStrategyFactory` must be able to resolve a strategy for the model class; factories typically fall back to a permissive default strategy for models without a specific one.

Applied on `BaseModel` — all concrete models inherit these methods automatically.

## Used By

Applied on `BaseModel` (inherited by all concrete models). Discoverable by `use HasModificationRules` in Everspot source.
