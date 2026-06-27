"""Cleansing primitive: strip everything but digits (trivial deterministic).

Used for ID-like fields where only the numeric content matters (account numbers,
zip+4 without the dash, etc.). Always confident; never routes to the LLM.

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (§ trivial normalizers)
"""

from __future__ import annotations

import re
from typing import Any

from cellcontract import Cell, empty, ok

VERSION = "1.0.0"

_METHOD = "digits_only"
_NON_DIGIT_RE = re.compile(r"\D")


def clean(raw: Any) -> Cell:
    """Return only the digit characters of ``raw``."""
    if raw is None or str(raw).strip() == "":
        return empty(method=_METHOD)
    digits = _NON_DIGIT_RE.sub("", str(raw))
    if digits == "":
        return empty(method=_METHOD, reason="no-digits")
    return ok(digits, confidence=1.0, method=_METHOD)
