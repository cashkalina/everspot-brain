"""Cleansing primitive: parse a person-name cell into structured parts.

Library: ``nameparser`` (HumanName). Returns a :class:`cellcontract.Cell` whose
``value`` is ``{title, first, middle, last, suffix, nickname}``.

LLM-fallback triggers (plan §7):
    - reversed ``"Last, First"`` — handled deterministically here (we detect &
      un-reverse), but flagged in meta.
    - multi-word / hyphenated surnames — kept, lower confidence.
    - **two people in one cell** (``"John & Mary Smith"``, ``"John and Mary"``) —
      we cannot reliably split → ``needs_llm=True``.

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (§ name parsing)
"""

from __future__ import annotations

import re
from typing import Any

from cellcontract import Cell, empty, low, ok

try:
    from nameparser import HumanName
except ImportError:  # pragma: no cover
    HumanName = None  # type: ignore

VERSION = "1.0.0"

_METHOD = "nameparser"

# "John & Mary", "John and Mary Smith", "Bob/Sue" → two people in one cell.
_TWO_PEOPLE_RE = re.compile(r"\s(?:&|and|/|\+)\s|(?<=\w)\s*&\s*(?=\w)", re.IGNORECASE)
_REVERSED_RE = re.compile(r"^\s*[^,]+,\s*[^,]+")


def _is_two_people(raw: str) -> bool:
    if _TWO_PEOPLE_RE.search(raw):
        # "Smith, John & Mary" still two people; but "Smith, John" is reversed-one.
        return True
    return False


def clean(raw: Any) -> Cell:
    """Parse ``raw`` into structured name parts following the cell contract."""
    if raw is None or (isinstance(raw, float)) or str(raw).strip() == "":
        return empty(method=_METHOD)
    text = str(raw).strip()

    if HumanName is None:
        return low(
            {"first": None, "last": text}, confidence=0.2, method=_METHOD,
            reason="nameparser not installed",
        )

    if _is_two_people(text):
        return low(
            {"raw": text}, confidence=0.25, method=_METHOD,
            reason="two-people-in-one-cell", two_people=True,
        )

    reversed_form = bool(_REVERSED_RE.match(text)) and text.count(",") == 1
    name = HumanName(text)
    parts = {
        "title": name.title or None,
        "first": name.first or None,
        "middle": name.middle or None,
        "last": name.last or None,
        "suffix": name.suffix or None,
        "nickname": name.nickname or None,
    }

    confidence = 0.95
    meta: dict[str, Any] = {}
    if reversed_form:
        meta["reversed_input"] = True
    if not parts["first"] or not parts["last"]:
        # A bare single token or odd structure — usable but worth a second look.
        confidence = 0.55
    elif parts["middle"] and " " in (parts["middle"] or ""):
        confidence = 0.8  # multi-word middle/surname ambiguity
    elif parts["last"] and ("-" in parts["last"] or " " in parts["last"]):
        confidence = 0.85

    if confidence < 0.8:
        return low(parts, confidence=confidence, method=_METHOD, reason="ambiguous-structure", **meta)
    return ok(parts, confidence=confidence, method=_METHOD, **meta)


def cleanse(raw: Any, context_signature: str = "", cache: Any = None) -> Cell:
    """Cleanse a name through the value cache → deterministic tier (operating-model §5.3).

    Thin wrapper over :func:`cleanse_runner.cleanse_with_cache` so the cleanse path
    is "value-cache lookup → :func:`clean` → (if ``needs_llm``) LLM tier". On a cache
    hit the parse is reused (no re-parse, no second LLM call even when other cells in
    the row changed); a confident deterministic result is written back for cross-row
    dedup; a ``needs_llm`` residual is returned untouched for the LLM stage, which
    writes back after re-validating. ``cache=None`` bypasses the cache.

    ``context_signature`` carries any column-level name decision that changes the
    output (e.g. ``"name_order=last_first"``).
    """
    from cleanse_runner import cleanse_with_cache

    return cleanse_with_cache("parse_name", VERSION, raw, clean, context_signature, cache)
