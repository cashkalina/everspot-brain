"""Cleansing primitive: resolve a raw code/label to a tenant list_option id.

Library: ``rapidfuzz``. Fuzzy-matches a raw value against a passed tenant-snapshot
option list (operating-model W0 introspection → ``reference_data.json``). Exact
match → full confidence; strong fuzzy → medium; unknown → ``needs_llm`` so it
becomes a Gate-1 value-set question (plan §7, §4.1 — value-sets resolve to **real
tenant IDs**).

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (§ list-option resolution)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence

from cellcontract import Cell, empty, low, ok

try:
    from rapidfuzz import fuzz, process
except ImportError:  # pragma: no cover
    fuzz = None  # type: ignore
    process = None  # type: ignore

VERSION = "1.0.0"

_METHOD = "rapidfuzz"

_STRONG_MATCH = 90.0  # ≥ → confident
_WEAK_MATCH = 75.0    # ≥ but < strong → low-confidence, route to LLM/question


@dataclass(slots=True)
class ListOption:
    """One tenant list_option from the Wave-0 snapshot."""

    id: int
    key: str
    name: str

    @property
    def search_terms(self) -> list[str]:
        return [t for t in {self.key, self.name} if t]


def _normalize(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def clean(raw: Any, options: Sequence[ListOption]) -> Cell:
    """Resolve ``raw`` to a list_option id against the tenant ``options``.

    Args:
        raw: The source code/label, e.g. ``"Jr"`` or ``"active"``.
        options: Tenant list_options for the relevant type (from reference_data).

    Returns:
        A :class:`Cell` whose ``value`` is the resolved ``id`` (int) or ``None``.
    """
    if raw is None or str(raw).strip() == "":
        return empty(method=_METHOD)
    text = _normalize(raw)

    # Exact key/name match first (case-insensitive).
    for opt in options:
        for term in opt.search_terms:
            if _normalize(term) == text:
                return ok(opt.id, confidence=1.0, method=_METHOD, matched=term)

    if fuzz is None or process is None or not options:
        return low(None, confidence=0.0, method=_METHOD, reason="unknown-code", raw=str(raw))

    # Fuzzy match against the flattened term → option map.
    term_to_opt: dict[str, ListOption] = {}
    for opt in options:
        for term in opt.search_terms:
            term_to_opt.setdefault(_normalize(term), opt)

    best = process.extractOne(text, list(term_to_opt.keys()), scorer=fuzz.WRatio)
    if best is None:
        return low(None, confidence=0.0, method=_METHOD, reason="unknown-code", raw=str(raw))

    match_term, score, _ = best
    opt = term_to_opt[match_term]
    norm_score = score / 100.0
    if score >= _STRONG_MATCH:
        return ok(opt.id, confidence=norm_score, method=_METHOD, matched=match_term, fuzzy=True)
    if score >= _WEAK_MATCH:
        return low(
            opt.id, confidence=norm_score, method=_METHOD,
            reason="weak-fuzzy-match", matched=match_term, candidate_id=opt.id,
        )
    # No usable match → Gate-1 value-set question.
    return low(None, confidence=0.0, method=_METHOD, reason="unknown-code", raw=str(raw))


def build_options(rows: Sequence[dict[str, Any]]) -> list[ListOption]:
    """Build :class:`ListOption`s from reference_data.json rows (id/key/name)."""
    return [ListOption(id=int(r["id"]), key=str(r.get("key", "")), name=str(r.get("name", ""))) for r in rows]
