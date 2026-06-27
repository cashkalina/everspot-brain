"""Cleansing primitive: money string → integer cents (exact, never float).

Library: ``decimal.Decimal``. Everspot stores money as integer cents; arithmetic
is done in code, never by an LLM (plan §7 — "extract, never LLM-arithmetic").
Parentheses-negatives (``(1,200.00)``) and currency symbols are handled. Non-numeric
free text (``"paid in full"``) → ``needs_llm`` to *extract* a number, not compute one.

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (§ currency normalization)
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from cellcontract import Cell, empty, low, ok

VERSION = "1.0.0"

_METHOD = "decimal"
_CURRENCY_STRIP_RE = re.compile(r"[^\d.\-()]")
_PARENS_NEG_RE = re.compile(r"^\((.*)\)$")


def clean(raw: Any) -> Cell:
    """Convert ``raw`` to integer cents following the cell contract."""
    if raw is None or str(raw).strip() == "":
        return empty(method=_METHOD)
    text = str(raw).strip()

    negative = False
    m = _PARENS_NEG_RE.match(text)
    if m:
        negative = True
        text = m.group(1)

    stripped = _CURRENCY_STRIP_RE.sub("", text)
    if stripped in ("", "-", ".", "()"):
        return low(None, confidence=0.1, method=_METHOD, reason="non-numeric", raw=str(raw))

    if stripped.startswith("-"):
        negative = True
        stripped = stripped.lstrip("-")

    try:
        amount = Decimal(stripped)
    except InvalidOperation:
        return low(None, confidence=0.1, method=_METHOD, reason="unparseable-amount", raw=str(raw))

    if negative:
        amount = -amount
    cents = int((amount * 100).to_integral_value(rounding="ROUND_HALF_UP"))
    return ok(cents, confidence=0.99, method=_METHOD)
