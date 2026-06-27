"""Cleansing primitive: normalize a phone cell to digits-only.

Library: ``phonenumbers``. Parses to E.164-ish digits; Everspot stores phones as
digits (plan §7 — ``phone→digits``). Multi-number / vanity / extension cells →
``needs_llm`` (plan §7 LLM trigger).

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (§ phone normalization)
"""

from __future__ import annotations

import re
from typing import Any

from cellcontract import Cell, empty, low, ok

try:
    import phonenumbers
except ImportError:  # pragma: no cover
    phonenumbers = None  # type: ignore

VERSION = "1.0.0"

_METHOD = "phonenumbers"
_MULTI_RE = re.compile(r"\b(ext|x|or|/|;|,)\b", re.IGNORECASE)


def clean(raw: Any, *, region: str = "US") -> Cell:
    """Normalize ``raw`` to a digits-only national/E.164 string."""
    if raw is None or str(raw).strip() == "":
        return empty(method=_METHOD)
    text = str(raw).strip()

    if _MULTI_RE.search(text):
        digits = re.sub(r"\D", "", text)
        return low(digits or None, confidence=0.4, method=_METHOD, reason="multi-number-or-extension", raw=text)

    if phonenumbers is None:
        digits = re.sub(r"\D", "", text)
        return low(digits or None, confidence=0.3, method=_METHOD, reason="phonenumbers-not-installed")

    try:
        parsed = phonenumbers.parse(text, region)
    except phonenumbers.NumberParseException:
        digits = re.sub(r"\D", "", text)
        return low(digits or None, confidence=0.25, method=_METHOD, reason="unparseable", raw=text)

    digits = f"{parsed.country_code}{parsed.national_number}"
    if phonenumbers.is_valid_number(parsed):
        return ok(digits, confidence=0.98, method=_METHOD, e164=phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164))
    return low(digits, confidence=0.5, method=_METHOD, reason="invalid-number")
