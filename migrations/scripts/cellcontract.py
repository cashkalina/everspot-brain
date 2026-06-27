"""The uniform cell contract that every cleansing primitive returns.

Each deterministic cleansing script takes a raw cell value and returns a
``Cell`` — ``{value, confidence, method, needs_llm}``. The orchestrator reads
``needs_llm`` (and a confidence floor) to decide which cells fall through to the
structured-output LLM tier (stage 4). LLM output is then *re-validated* through
the same Python library via :func:`revalidate`, so the library — not the model —
remains the source of truth.

Design references:
    - operating-model §3 (the cell contract, stage 3/4 routing)
    - operating-model §7-A (cleansing primitives implement this contract)
    - plan §3 stage 3/4, §7 (the growing script library, house rule)

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (per-field cleansing rules & contract)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, TypedDict

VERSION = "1.0.0"

DEFAULT_CONFIDENCE_FLOOR = 0.80
"""Cells at or below this confidence are routed to the LLM tier even if a
primitive did not explicitly set ``needs_llm``."""


class CellDict(TypedDict):
    """JSON-serializable shape of a cell (what lands in clean/*.parquet rows)."""

    value: Any
    confidence: float
    method: str
    needs_llm: bool


@dataclass(slots=True)
class Cell:
    """A single cleansed cell.

    Attributes:
        value: The normalized value. May be a scalar (``"4155551234"``), a
            structured dict (``{"first": "John", "last": "Smith"}``), or ``None``
            when the primitive could not produce anything usable.
        confidence: 0.0–1.0 self-assessed confidence in ``value``.
        method: Short identifier of how the value was produced, e.g.
            ``"nameparser"``, ``"dateutil"``, ``"llm:gpt"``, ``"override"``.
        needs_llm: True when the primitive wants the LLM tier to take a pass.
        meta: Optional free-form provenance (flags, sub-scores, alternatives).
    """

    value: Any = None
    confidence: float = 0.0
    method: str = "unknown"
    needs_llm: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Clamp confidence into [0, 1] so downstream histograms never break.
        if self.confidence < 0.0:
            self.confidence = 0.0
        elif self.confidence > 1.0:
            self.confidence = 1.0

    def to_dict(self) -> CellDict:
        """The contract view (drops ``meta``, which is provenance-only)."""
        return {
            "value": self.value,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "needs_llm": self.needs_llm,
        }

    def with_meta(self, **kwargs: Any) -> "Cell":
        """Return a copy with merged ``meta`` (cheap immutable-style update)."""
        merged = {**self.meta, **kwargs}
        return Cell(self.value, self.confidence, self.method, self.needs_llm, merged)


def ok(value: Any, *, confidence: float = 1.0, method: str = "deterministic", **meta: Any) -> Cell:
    """A confidently-resolved cell that does not need the LLM."""
    return Cell(value=value, confidence=confidence, method=method, needs_llm=False, meta=meta)


def low(
    value: Any,
    *,
    confidence: float = 0.4,
    method: str = "deterministic",
    reason: str = "",
    **meta: Any,
) -> Cell:
    """A weakly-resolved cell that should fall through to the LLM tier.

    ``value`` is the best deterministic guess (kept so the LLM has a prior and so
    we degrade gracefully if the LLM tier is skipped).
    """
    if reason:
        meta["reason"] = reason
    return Cell(value=value, confidence=confidence, method=method, needs_llm=True, meta=meta)


def empty(*, method: str = "deterministic", reason: str = "empty-input") -> Cell:
    """A blank source cell: nothing to do, fully confident it's empty."""
    return Cell(value=None, confidence=1.0, method=method, needs_llm=False, meta={"reason": reason})


def needs_routing(cell: Cell, floor: float = DEFAULT_CONFIDENCE_FLOOR) -> bool:
    """Whether the orchestrator should send this cell to the LLM tier."""
    return cell.needs_llm or cell.confidence < floor


def revalidate(
    llm_value: Any,
    validator_fn: Callable[[Any], Cell],
    *,
    llm_confidence: Optional[float] = None,
    llm_method: str = "llm",
) -> Cell:
    """Re-validate an LLM-produced value through the same deterministic primitive.

    This is the house rule from plan §7 ("always re-validate LLM output through
    the same library"). The LLM proposes; ``validator_fn`` (the very same
    primitive, e.g. :func:`parse_name.clean`) re-parses the proposal.

    - If the primitive accepts it cleanly, we trust it but mark the method as
      LLM-sourced and blend the confidences (the primitive's structural
      confidence × the model's self-reported confidence when provided).
    - If the primitive *still* wants the LLM (``needs_llm``), the value remains an
      exception (stage 4 ``exceptions.jsonl``).

    Args:
        llm_value: The raw value the LLM returned (string, dict, etc.).
        validator_fn: A primitive ``clean``-style fn returning a :class:`Cell`.
        llm_confidence: The model's self-reported confidence, if it returned one.
        llm_method: Method label to stamp (e.g. ``"llm:claude-sonnet"``).

    Returns:
        A :class:`Cell` whose ``method`` records the LLM provenance and whose
        ``needs_llm`` reflects whether the value is *still* an exception.
    """
    revalidated = validator_fn(llm_value)
    blended = revalidated.confidence
    if llm_confidence is not None:
        blended = revalidated.confidence * max(0.0, min(1.0, llm_confidence))

    return Cell(
        value=revalidated.value,
        confidence=blended,
        method=f"{llm_method}+revalidated:{revalidated.method}",
        needs_llm=revalidated.needs_llm,
        meta={**revalidated.meta, "llm_raw": llm_value, "llm_confidence": llm_confidence},
    )
