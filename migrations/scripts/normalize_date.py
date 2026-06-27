"""Cleansing primitive: normalize a date cell to a partial-date structure.

Library: ``dateutil``. Returns a :class:`cellcontract.Cell` whose ``value`` is a
partial date ``{year, month, day, estimated}`` (plan §4.2 — DOB/DOD are partial
dates because cemetery records are frequently year- or month-only).

LLM-fallback triggers (plan §7):
    - ``"circa 1923"`` / ``"c. 1923"`` / ``"abt 1923"`` → estimated year, needs_llm
      review for the qualifier.
    - ambiguous DD/MM vs MM/DD when both components ≤ 12 → needs_llm.
    - 2-digit years (century ambiguity) → low confidence.
    - free text we can't parse → needs_llm.

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (§ date normalization, partial dates)
"""

from __future__ import annotations

import re
from typing import Any, Optional

from cellcontract import Cell, empty, low, ok

try:
    from dateutil import parser as dtparser
except ImportError:  # pragma: no cover
    dtparser = None  # type: ignore

VERSION = "1.0.0"

_METHOD = "dateutil"

_CIRCA_RE = re.compile(r"\b(c\.?|ca\.?|circa|abt|about|approx)\b", re.IGNORECASE)
_YEAR_ONLY_RE = re.compile(r"^\s*(\d{4})\s*$")
_YEAR_MONTH_RE = re.compile(r"^\s*(\d{4})[-/](\d{1,2})\s*$")
_AMBIGUOUS_NUMERIC_RE = re.compile(r"^\s*(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\s*$")
_TWO_DIGIT_YEAR_RE = re.compile(r"[-/](\d{2})\s*$")


def partial(year: Optional[int], month: Optional[int], day: Optional[int], estimated: bool) -> dict:
    """Construct the canonical partial-date dict."""
    return {"year": year, "month": month, "day": day, "estimated": bool(estimated)}


def clean(raw: Any) -> Cell:
    """Normalize ``raw`` to a partial date following the cell contract."""
    if raw is None or str(raw).strip() == "":
        return empty(method=_METHOD)
    text = str(raw).strip()

    estimated = bool(_CIRCA_RE.search(text))
    cleaned = _CIRCA_RE.sub("", text).strip(" .,")

    # Year-only — common and unambiguous.
    m = _YEAR_ONLY_RE.match(cleaned)
    if m:
        value = partial(int(m.group(1)), None, None, estimated)
        if estimated:
            return low(value, confidence=0.6, method=_METHOD, reason="circa-qualifier")
        return ok(value, confidence=0.97, method=_METHOD)

    # Year-month.
    m = _YEAR_MONTH_RE.match(cleaned)
    if m:
        value = partial(int(m.group(1)), int(m.group(2)), None, estimated)
        return ok(value, confidence=0.9 if not estimated else 0.6, method=_METHOD, estimated=estimated)

    # Ambiguous DD/MM where both ≤ 12 → can't tell order.
    m = _AMBIGUOUS_NUMERIC_RE.match(cleaned)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a <= 12 and b <= 12 and a != b:
            best = _safe_parse(cleaned)
            return low(
                best, confidence=0.4, method=_METHOD,
                reason="ambiguous-dd-mm", ambiguous_components=[a, b],
            )

    two_digit_year = bool(_TWO_DIGIT_YEAR_RE.search(cleaned))
    parsed = _safe_parse(cleaned)
    if parsed is None:
        return low(
            partial(None, None, None, estimated), confidence=0.15, method=_METHOD,
            reason="unparseable-free-text", raw=text,
        )

    confidence = 0.95
    if estimated:
        confidence = 0.6
    elif two_digit_year:
        confidence = 0.55  # century ambiguity
    value = {**parsed, "estimated": estimated}
    if confidence < 0.8:
        return low(value, confidence=confidence, method=_METHOD, reason="2-digit-year" if two_digit_year else "circa")
    return ok(value, confidence=confidence, method=_METHOD)


def cleanse(raw: Any, context_signature: str = "", cache: Any = None) -> Cell:
    """Cleanse a date through the value cache → deterministic tier (operating-model §5.3).

    Thin wrapper over :func:`cleanse_runner.cleanse_with_cache` so the cleanse path
    is "value-cache lookup → :func:`clean` → (if ``needs_llm``) LLM tier". On a cache
    hit the parse is reused; a confident deterministic result is written back for
    cross-row dedup; an ambiguous/free-text residual is returned untouched for the
    LLM stage, which writes back after re-validating. ``cache=None`` bypasses it.

    ``context_signature`` should carry the column's date interpretation when it
    affects the output (e.g. ``"date_format=MDY"`` vs ``"date_format=DMY"``), so a
    parse decided under one interpretation is never reused under another.
    """
    from cleanse_runner import cleanse_with_cache

    return cleanse_with_cache("normalize_date", VERSION, raw, clean, context_signature, cache)


def _safe_parse(text: str) -> Optional[dict]:
    if dtparser is None:
        return None
    try:
        dt = dtparser.parse(text, dayfirst=False, fuzzy=False)
    except (ValueError, OverflowError, TypeError):
        return None
    return {"year": dt.year, "month": dt.month, "day": dt.day}
