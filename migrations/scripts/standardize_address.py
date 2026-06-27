"""Cleansing primitive: standardize a freeform US address cell into parts.

Library: ``usaddress`` (CRF tagger, US-only). Returns a :class:`cellcontract.Cell`
whose ``value`` is ``{line_one, line_two, city, state, zip}`` (plan §7 —
``address→{line_one,line_two,city,state,zip}``). ``libpostal``/``postal`` would give
a stronger international parse, but it is a heavy native dependency, so it is imported
lazily and guarded — if it is not importable we degrade to ``usaddress``-only and never
hard-crash on import.

usaddress tag → field mapping:
    AddressNumber + StreetName* (+ pre/post directionals/types)  → line_one
    OccupancyType + OccupancyIdentifier (Apt/Ste/Unit/Fl …)      → line_two
    PlaceName                                                    → city
    StateName (resolved to 2-letter where possible)             → state
    ZipCode                                                      → zip

LLM-fallback triggers (plan §7):
    - ``usaddress.RepeatedLabelError`` — the tagger saw a label twice (ambiguous parse).
    - plot / section / lot / grave designations bleeding into the address line.
    - PO boxes vs rural routes (USPSBoxType / rural-route tokens) — kept, lower
      confidence, flagged for review.
    - missing / garbage components (no street number, no city, no state, no zip).
    - tokens usaddress tags as ``Recipient`` or otherwise unparseable.
Confidence reflects tag coverage (how many of the canonical fields we resolved).

everspot-brain doc that specifies the rules:
    system-wiki/system/data-cleansing.md  (§ address standardization)
"""

from __future__ import annotations

import re
from typing import Any, Optional

from cellcontract import Cell, empty, low, ok

try:
    import usaddress
except ImportError:  # pragma: no cover
    usaddress = None  # type: ignore

# libpostal is an optional, heavy native dependency. Import lazily / guarded so a
# machine without it (the common case) still runs the usaddress path. We only flip
# this on when both the python binding and its native lib actually import.
try:  # pragma: no cover - environment dependent
    from postal.parser import parse_address as _libpostal_parse  # type: ignore

    _HAS_LIBPOSTAL = True
except Exception:  # pragma: no cover - ImportError or native-lib load failure
    _libpostal_parse = None  # type: ignore
    _HAS_LIBPOSTAL = False

VERSION = "1.0.0"

_METHOD = "usaddress"

# Cemetery plot/section/lot/grave designations that frequently bleed into the
# address column on legacy exports and must not be treated as a street.
_PLOT_RE = re.compile(
    r"\b(sec(?:tion)?|lot|blk|block|grave|plot|tier|niche|crypt|range|space|garden)\b",
    re.IGNORECASE,
)
# PO box / rural-route style tokens — deliverable, but a different shape than a
# street address; the LLM tier should confirm the box/route normalization.
_PO_BOX_RE = re.compile(r"\b(p\.?\s*o\.?\s*box|po\s*box|post\s*office\s*box)\b", re.IGNORECASE)
_RURAL_RE = re.compile(r"\b(r\.?r\.?|rural\s*route|h\.?c\.?\d|hc\s*\d|star\s*route)\b", re.IGNORECASE)

# usaddress label → which canonical field it contributes to.
_LINE_ONE_LABELS = (
    "AddressNumber",
    "AddressNumberPrefix",
    "AddressNumberSuffix",
    "StreetNamePreDirectional",
    "StreetNamePreModifier",
    "StreetNamePreType",
    "StreetName",
    "StreetNamePostType",
    "StreetNamePostDirectional",
    "StreetNamePostModifier",
    "USPSBoxType",
    "USPSBoxID",
    "USPSBoxGroupType",
    "USPSBoxGroupID",
)
_LINE_TWO_LABELS = (
    "OccupancyType",
    "OccupancyIdentifier",
    "SubaddressType",
    "SubaddressIdentifier",
    "BuildingName",
)

# 2-letter resolution for spelled-out state names usaddress sometimes returns whole.
_STATE_ABBR = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
    "puerto rico": "PR",
}
_STATE_ABBRS = set(_STATE_ABBR.values())


def _blank_address() -> dict:
    """The canonical address shape with every field empty."""
    return {"line_one": None, "line_two": None, "city": None, "state": None, "zip": None}


def _resolve_state(raw_state: Optional[str]) -> Optional[str]:
    """Resolve a state token to its 2-letter USPS abbreviation where possible."""
    if not raw_state:
        return None
    token = raw_state.strip().strip(".,").upper()
    if token in _STATE_ABBRS:
        return token
    full = _STATE_ABBR.get(raw_state.strip().lower())
    return full or raw_state.strip() or None


def _assemble(tagged: dict[str, str]) -> dict:
    """Fold usaddress's ``{label: text}`` into the canonical address dict."""
    address = _blank_address()

    line_one_parts = [tagged[label] for label in _LINE_ONE_LABELS if label in tagged]
    if line_one_parts:
        address["line_one"] = " ".join(line_one_parts).strip() or None

    line_two_parts = [tagged[label] for label in _LINE_TWO_LABELS if label in tagged]
    if line_two_parts:
        address["line_two"] = " ".join(line_two_parts).strip() or None

    if "PlaceName" in tagged:
        address["city"] = tagged["PlaceName"].strip(" ,") or None
    if "StateName" in tagged:
        address["state"] = _resolve_state(tagged["StateName"])
    if "ZipCode" in tagged:
        address["zip"] = tagged["ZipCode"].strip(" ,") or None

    return address


def _coverage_confidence(address: dict) -> float:
    """Confidence as a function of how many canonical fields resolved.

    A clean US mailing address resolves line_one + city + state + zip. We weight the
    structurally-required pieces (street line, state, zip) and treat city as a bonus.
    """
    score = 0.0
    if address["line_one"]:
        score += 0.40
    if address["city"]:
        score += 0.15
    if address["state"]:
        score += 0.25
    if address["zip"]:
        score += 0.20
    return round(score, 4)


def clean(raw: Any) -> Cell:
    """Parse ``raw`` into a normalized US address dict following the cell contract."""
    if raw is None or (isinstance(raw, float)) or str(raw).strip() == "":
        return empty(method=_METHOD)
    text = str(raw).strip()

    if usaddress is None:
        return low(
            {**_blank_address(), "line_one": text}, confidence=0.2, method=_METHOD,
            reason="usaddress-not-installed",
        )

    has_plot = bool(_PLOT_RE.search(text))
    is_po_box = bool(_PO_BOX_RE.search(text))
    is_rural = bool(_RURAL_RE.search(text))

    try:
        tagged, address_type = usaddress.tag(text)
    except usaddress.RepeatedLabelError as exc:  # ambiguous parse
        # Best-effort: keep the raw line so the LLM has a prior.
        return low(
            {**_blank_address(), "line_one": text}, confidence=0.25, method=_METHOD,
            reason="repeated-label-ambiguous", raw=text,
            repeated_labels=[label for _, label in (exc.parsed_string or [])],
        )

    address = _assemble(tagged)

    # usaddress labels overflow / unrecognized tokens as Recipient — strong signal
    # the line did not parse as a deliverable street address.
    has_recipient = "Recipient" in tagged
    has_anything = any(address[field] for field in ("line_one", "city", "state", "zip"))

    confidence = _coverage_confidence(address)
    meta: dict[str, Any] = {"address_type": address_type, "libpostal": _HAS_LIBPOSTAL}

    if has_plot:
        return low(
            address, confidence=min(confidence, 0.45), method=_METHOD,
            reason="plot-designation-in-address", raw=text, **meta,
        )
    if has_recipient or not has_anything:
        return low(
            address if has_anything else {**_blank_address(), "line_one": text},
            confidence=min(confidence, 0.3), method=_METHOD,
            reason="recipient-or-unparseable", raw=text, **meta,
        )
    if is_po_box or is_rural:
        return low(
            address, confidence=min(confidence, 0.6), method=_METHOD,
            reason="po-box" if is_po_box else "rural-route", raw=text, **meta,
        )

    # Missing/garbage components: no street line, or no city/state/zip at all.
    if not address["line_one"] or not (address["state"] and address["zip"]):
        return low(
            address, confidence=min(confidence, 0.6), method=_METHOD,
            reason="missing-components", raw=text, **meta,
        )

    if confidence < 0.8:
        return low(address, confidence=confidence, method=_METHOD, reason="low-tag-coverage", **meta)
    return ok(address, confidence=confidence, method=_METHOD, **meta)


def cleanse(raw: Any, cache: Any = None, context_signature: str = "") -> Cell:
    """Cleanse an address through the value cache → deterministic tier (operating-model §5.3).

    Thin wrapper over :func:`cleanse_runner.cleanse_with_cache` so the cleanse path
    is "value-cache lookup → :func:`clean` → (if ``needs_llm``) LLM tier". On a cache
    hit the parse is reused (no re-tag, no second LLM call even when other cells in the
    row changed); a confident deterministic result is written back for cross-row dedup;
    an ambiguous / plot-bleed / missing-component residual is returned untouched for the
    LLM stage, which writes back after re-validating. ``cache=None`` bypasses the cache.

    ``context_signature`` carries any column-level address decision that changes the
    output (e.g. ``"country=US"`` or a known single-line vs multi-line column shape).
    """
    from cleanse_runner import cleanse_with_cache

    return cleanse_with_cache("standardize_address", VERSION, raw, clean, context_signature, cache)
