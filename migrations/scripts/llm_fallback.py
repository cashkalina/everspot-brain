"""Stage-4 LLM fallback: resolve the messy residual the deterministic tier flagged.

This is the structured-output LLM tier of the cleanse stage (SPEC §8 stage 8).
The deterministic Python tier (``parse_name`` / ``normalize_date`` /
``normalize_phone`` / address) already resolved the predictable 80–90% of cells;
this module operates **only** on residual cells flagged ``needs_llm`` and:

    1. groups residuals by ``field_type`` and batches them into structured-output
       (forced-tool-use) model calls — one typed object per input, in order;
    2. **re-validates every model proposal through the same deterministic library**
       that flagged the cell (``cellcontract.revalidate`` + the matching ``clean``),
       so the Python library — not the model — stays the source of truth;
    3. scores confidence by blending the model's self-confidence with the validator
       outcome, routes anything below threshold to ``exceptions``;
    4. enforces a per-run cost ceiling (``max_batches`` / token-estimate circuit
       breaker), stopping cleanly and marking the remainder as exceptions;
    5. logs every model response to ``llm_log.jsonl`` **before** merging (so a resume
       replays from the log instead of re-calling the model — idempotency);
    6. writes resolved cells back to the Tier-3 value cache (``cache.store``) at/above
       :data:`transform_cache.LLM_CACHE_CONFIDENCE_FLOOR`, so the exact input string
       is never sent to the LLM again — across rows and across drops.

API surface (authoritative per the build spec — do not "tune" these off):
    - Official Anthropic Python SDK: ``from anthropic import Anthropic`` / ``Anthropic()``.
    - Model via :data:`MODEL` (env ``MIGRATION_LLM_MODEL``, default ``claude-opus-4-8``).
    - Structured output via **forced tool use** (``tool_choice={"type":"tool",...}``),
      one tool per field type whose single ``results`` array carries a typed object
      per input item in order. No ``thinking`` (``budget_tokens`` 400s on opus-4-8),
      no ``temperature``/``top_p``/``top_k`` (they 400 on opus-4-8), no ``effort``.
    - Errors: catch ``anthropic.RateLimitError`` / ``anthropic.APIError`` (the SDK
      auto-retries 429/5xx; we only surface/skip on terminal failure).

Spec & knowledge that specify the rules:
    SPEC.md §8 stage 8                          (the cleanse stage + held LLM tier)
    knowledge/topics/name-parsing.md           (per-field cleansing rules & contract)
    SPEC.md §5.3                               (Tier-3 cache, confidence floor)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from cellcontract import Cell, low, revalidate
from transform_cache import LLM_CACHE_CONFIDENCE_FLOOR, TransformCache

try:  # The SDK is a hard dep at runtime, but the dry-run path must import cleanly.
    import anthropic
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - exercised by the no-key dry-run smoke test.
    anthropic = None  # type: ignore
    Anthropic = None  # type: ignore

VERSION = "1.0.0"

# For high-volume parsing, ``claude-haiku-4-5`` is the cost-effective choice and is a
# drop-in one-line switch — set MIGRATION_LLM_MODEL=claude-haiku-4-5 in the env.
MODEL = os.environ.get("MIGRATION_LLM_MODEL", "claude-opus-4-8")

# Non-streaming create is fine at this size; opus-4-8 rejects thinking/sampling params,
# so we send neither (see the module docstring).
MAX_TOKENS = 8192

DEFAULT_BATCH_SIZE = 50

# Per-run circuit breaker. A rough $/token estimate is accumulated from each
# response's ``usage`` and the run stops cleanly once it exceeds the ceiling.
DEFAULT_TOKEN_CEILING = 5_000_000
"""Soft cap on total tokens (input+output) for a single ``resolve_residuals`` run."""

# Coarse self-confidence we assign to a model proposal *before* the deterministic
# validator gets the final say (``revalidate`` multiplies this by the validator's
# structural confidence). A library-rejected proposal therefore stays low regardless.
_BASE_LLM_CONFIDENCE = 0.85

_LOG_FILENAME = "llm_log.jsonl"


# --------------------------------------------------------------------------- #
# Field-type tool schemas (forced tool use → structured output)               #
# --------------------------------------------------------------------------- #
# Each tool's single property ``results`` is an array of typed objects, ONE PER
# INPUT ITEM IN ORDER. We force the model to call exactly this tool, then read the
# array back from the ``tool_use`` block's ``.input["results"]``.
def _array_tool(name: str, item_properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": (
            f"Return one structured {name.replace('parse_', '').replace('_batch', '')} "
            "object per input line, in the same order as the numbered input list. "
            "Never invent data: if a field is not present in the input, use null "
            "(or false for booleans). Do not perform arithmetic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": item_properties,
                        "required": required,
                    },
                }
            },
            "required": ["results"],
        },
    }


_STR = {"type": ["string", "null"]}
_INT = {"type": ["integer", "null"]}
_BOOL = {"type": "boolean"}

_TOOLS: dict[str, dict[str, Any]] = {
    "name": _array_tool(
        "parse_name_batch",
        {"first": _STR, "middle": _STR, "last": _STR, "suffix": _STR},
        ["first", "middle", "last", "suffix"],
    ),
    "date": _array_tool(
        "parse_date_batch",
        {"year": _INT, "month": _INT, "day": _INT, "estimated": _BOOL},
        ["year", "month", "day", "estimated"],
    ),
    "address": _array_tool(
        "parse_address_batch",
        {"line_one": _STR, "line_two": _STR, "city": _STR, "state": _STR, "zip": _STR},
        ["line_one", "line_two", "city", "state", "zip"],
    ),
    "phone": _array_tool(
        "parse_phone_batch",
        {"digits": _STR, "extension": _STR},
        ["digits", "extension"],
    ),
}

# The transform name each field type writes back to in the Tier-3 cache. Must match
# the deterministic primitive's transform name + VERSION (so the LLM write-back
# short-circuits the *same* cache key the deterministic tier would have missed).
_TRANSFORM: dict[str, tuple[str, str]] = {
    "name": ("parse_name", "1.0.0"),
    "date": ("normalize_date", "1.0.0"),
    "address": ("standardize_address", "1.0.0"),
    "phone": ("normalize_phone", "1.0.0"),
}


def build_tool(field_type: str) -> dict[str, Any]:
    """Return the forced-tool-use schema for ``field_type`` (raises on unknown type)."""
    try:
        return _TOOLS[field_type]
    except KeyError:
        raise ValueError(f"no LLM tool schema for field_type {field_type!r}")


def supported_field_types() -> set[str]:
    """Field types this module can resolve via the LLM tier."""
    return set(_TOOLS)


# --------------------------------------------------------------------------- #
# Re-validation adapters: structured LLM output → deterministic clean()        #
# --------------------------------------------------------------------------- #
# The deterministic ``clean`` validators take a raw *string*; the LLM emits typed
# parts. Per the spec ("re-run through parse_name to confirm round-trip stability"),
# we render the typed parts back into a canonical string and re-run the same library.
# A validator therefore takes the LLM's structured dict and returns a re-validated
# ``Cell`` (value, structural confidence, needs_llm).
def _validate_name(parts: dict[str, Any]) -> Cell:
    import parse_name

    rendered = " ".join(
        str(parts.get(k)).strip()
        for k in ("first", "middle", "last", "suffix")
        if parts.get(k)
    ).strip()
    if not rendered:
        return low({"first": None, "last": None}, confidence=0.0, method="nameparser", reason="empty-llm-name")
    cell = parse_name.clean(rendered)
    # Keep the LLM's discrete parts as the value (the round-trip only gauges stability).
    return Cell(
        value={k: parts.get(k) for k in ("first", "middle", "last", "suffix")},
        confidence=cell.confidence,
        method=cell.method,
        needs_llm=cell.needs_llm,
        meta=cell.meta,
    )


def _validate_date(parts: dict[str, Any]) -> Cell:
    import normalize_date

    year, month, day = parts.get("year"), parts.get("month"), parts.get("day")
    estimated = bool(parts.get("estimated"))
    if year is None and month is None and day is None:
        return low(
            normalize_date.partial(None, None, None, estimated),
            confidence=0.0, method="dateutil", reason="empty-llm-date",
        )
    # Render the most specific string the parts support, then re-run normalize_date
    # so impossible dates (month=13, day=32) are rejected by the library, not us.
    if year and month and day:
        rendered = f"{year:04d}-{month:02d}-{day:02d}"
    elif year and month:
        rendered = f"{year:04d}-{month:02d}"
    elif year:
        rendered = f"{year:04d}"
    else:
        rendered = "-".join(str(p) for p in (month, day, year) if p)
    cell = normalize_date.clean(rendered)
    value = cell.value if isinstance(cell.value, dict) else normalize_date.partial(year, month, day, estimated)
    if isinstance(value, dict):
        value["estimated"] = estimated
    return Cell(value=value, confidence=cell.confidence, method=cell.method, needs_llm=cell.needs_llm, meta=cell.meta)


def _validate_phone(parts: dict[str, Any]) -> Cell:
    import normalize_phone

    digits = (parts.get("digits") or "").strip()
    extension = (parts.get("extension") or "").strip() or None
    if not digits:
        return low(None, confidence=0.0, method="phonenumbers", reason="empty-llm-phone")
    cell = normalize_phone.clean(digits)
    value: dict[str, Any] = {"digits": cell.value, "extension": extension}
    return Cell(value=value, confidence=cell.confidence, method=cell.method, needs_llm=cell.needs_llm, meta=cell.meta)


def _validate_address(parts: dict[str, Any]) -> Cell:
    # ``standardize_address.py`` is planned (requirements.txt: usaddress) but not yet
    # in the script library. If/when it lands, prefer its ``clean``; until then do a
    # self-contained structural validation: an address resolves only with a usable
    # line_one plus either a city or a zip (otherwise it is an exception).
    try:
        import standardize_address  # type: ignore

        rendered = ", ".join(
            str(parts.get(k)).strip()
            for k in ("line_one", "line_two", "city", "state", "zip")
            if parts.get(k)
        )
        return standardize_address.clean(rendered)  # type: ignore[attr-defined]
    except ImportError:
        pass

    line_one = (parts.get("line_one") or "").strip()
    city = (parts.get("city") or "").strip()
    zip_code = (parts.get("zip") or "").strip()
    value = {k: (parts.get(k) or None) for k in ("line_one", "line_two", "city", "state", "zip")}
    if line_one and (city or zip_code):
        confidence = 0.9 if (city and zip_code) else 0.8
        return Cell(value=value, confidence=confidence, method="address-structural", needs_llm=False)
    return low(value, confidence=0.3, method="address-structural", reason="insufficient-address-parts")


_VALIDATORS: dict[str, Callable[[dict[str, Any]], Cell]] = {
    "name": _validate_name,
    "date": _validate_date,
    "address": _validate_address,
    "phone": _validate_phone,
}


# --------------------------------------------------------------------------- #
# Idempotent log (log-before-write + replay)                                  #
# --------------------------------------------------------------------------- #
def _cell_key(residual: dict[str, Any]) -> tuple[str, str, str]:
    """Idempotency key per the spec: ``{table, source_id, column}``."""
    return (
        str(residual.get("table", "")),
        str(residual.get("source_id", "")),
        str(residual.get("column", "")),
    )


def _load_log(log_path: Optional[Path]) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Read ``llm_log.jsonl`` into a ``{cell_key: record}`` map for replay."""
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    if log_path is None or not log_path.exists():
        return seen
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = (str(rec.get("table", "")), str(rec.get("source_id", "")), str(rec.get("column", "")))
        seen[key] = rec
    return seen


def _append_log(log_path: Optional[Path], record: dict[str, Any]) -> None:
    """Append one model-response record to the log BEFORE merging it into clean/."""
    if log_path is None:
        return
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")


# --------------------------------------------------------------------------- #
# Batching / grouping                                                          #
# --------------------------------------------------------------------------- #
def _group_by_field_type(residuals: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in residuals:
        groups.setdefault(str(r.get("field_type", "")), []).append(r)
    return groups


def _chunks(items: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _build_user_message(batch: list[dict[str, Any]]) -> str:
    """The batch of input strings as a numbered list in the user message."""
    lines = [
        "Parse each of the following raw values. Return one structured object per "
        "line via the tool, in the same order. Use null for any field not present.",
        "",
    ]
    for idx, residual in enumerate(batch, start=1):
        lines.append(f"{idx}. {residual.get('raw_value', '')}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Result construction                                                         #
# --------------------------------------------------------------------------- #
def _exception(residual: dict[str, Any], note: str, cell: Optional[Cell] = None) -> dict[str, Any]:
    """An ``exceptions.jsonl`` record (question-round input)."""
    rec = {
        "table": residual.get("table"),
        "source_id": residual.get("source_id"),
        "column": residual.get("column"),
        "raw_value": residual.get("raw_value"),
        "field_type": residual.get("field_type"),
        "note": note,
    }
    if cell is not None:
        rec["cell"] = cell.to_dict()
        rec["confidence"] = round(cell.confidence, 4)
    return rec


def _resolved(residual: dict[str, Any], cell: Cell) -> dict[str, Any]:
    """A resolved-cell record carrying the cell contract + provenance."""
    return {
        "table": residual.get("table"),
        "source_id": residual.get("source_id"),
        "column": residual.get("column"),
        "raw_value": residual.get("raw_value"),
        "field_type": residual.get("field_type"),
        "cell": cell.to_dict(),
    }


def _revalidate_one(field_type: str, raw_parts: Any) -> Cell:
    """Re-validate one LLM proposal through the matching deterministic validator."""
    validator = _VALIDATORS[field_type]
    if not isinstance(raw_parts, dict):
        return low(None, confidence=0.0, method=f"llm:{MODEL}", reason="malformed-llm-item")
    return revalidate(
        raw_parts,
        validator,
        llm_confidence=_BASE_LLM_CONFIDENCE,
        llm_method=f"llm:{MODEL}",
    )


# --------------------------------------------------------------------------- #
# The model call                                                              #
# --------------------------------------------------------------------------- #
def _call_model(client: Any, model: str, field_type: str, batch: list[dict[str, Any]]) -> tuple[list[Any], dict[str, int]]:
    """One forced-tool-use call. Returns (results-in-order, usage tokens).

    Raises ``anthropic.APIError`` (incl. ``RateLimitError``) on terminal failure —
    the SDK has already auto-retried 429/5xx, so a raised error here is terminal.
    """
    tool = build_tool(field_type)
    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": _build_user_message(batch)}],
    )
    results: list[Any] = []
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool["name"]:
            results = list((block.input or {}).get("results", []))
            break
    usage = getattr(response, "usage", None)
    tokens = {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
    }
    return results, tokens


# --------------------------------------------------------------------------- #
# Public entrypoint                                                           #
# --------------------------------------------------------------------------- #
def resolve_residuals(
    residuals: list[dict[str, Any]],
    cache: Optional[TransformCache],
    client: Optional[Any] = None,
    model: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_batches: Optional[int] = None,
    log_path: Optional[str | Path] = None,
    token_ceiling: int = DEFAULT_TOKEN_CEILING,
) -> dict[str, Any]:
    """Resolve ``needs_llm`` residual cells via the structured-output LLM tier.

    Args:
        residuals: rows like ``{table, source_id, column, raw_value, field_type,
            context_signature}`` (the ``needs_llm:true`` cells from the deterministic tier).
        cache: an open :class:`TransformCache`. Resolved cells at/above
            :data:`transform_cache.LLM_CACHE_CONFIDENCE_FLOOR` are written back via
            :meth:`TransformCache.store`. ``None`` disables the cache write-back.
        client: an ``anthropic.Anthropic`` client. ``None`` + env ``MIGRATION_LLM_DRYRUN=1``
            takes the offline path (no API call) — an OPTIONAL cost/speed/determinism
            switch, not a PII gate (AI may process real client data per the user's
            standing authorization). ``None`` otherwise constructs ``Anthropic()`` — which
            itself requires ``ANTHROPIC_API_KEY``, so with no key the run physically
            cannot call the model and stays deterministic.
        model: model id override (defaults to :data:`MODEL`).
        batch_size: residuals per model call (grouped by field type first).
        max_batches: circuit-breaker cap on total model calls; remaining residuals
            become exceptions when hit. ``None`` = unbounded.
        log_path: path to ``llm_log.jsonl`` — every model response is appended here
            BEFORE merging, and cells already present are skipped (idempotent replay).
        token_ceiling: per-run token circuit breaker; the run stops cleanly once the
            accumulated input+output tokens exceed it.

    Returns:
        ``{"resolved": [...], "exceptions": [...], "stats": {calls, input_tokens,
        output_tokens, cached_writes}}``. ``resolved`` carries the cell contract
        (``method="llm:<model>+revalidated:<validator>"``, ``needs_llm=False``).
    """
    model = model or MODEL
    log_p = Path(log_path) if log_path is not None else None
    logged = _load_log(log_p)

    resolved: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []
    stats = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cached_writes": 0}

    # The LLM tier goes live ONLY when the caller opts in (an explicit ``client``) OR a
    # real key is present. Two offline paths keep the run deterministic otherwise:
    #
    #  - MIGRATION_LLM_DRYRUN=1 — an OPTIONAL cost/speed/determinism switch (NOT a PII
    #    safety gate; AI may process real client data per the user's standing
    #    authorization). When set, residuals become exceptions, no API call, no key needed.
    #  - no ANTHROPIC_API_KEY (and no explicit client) — the run *physically cannot* call
    #    the model, so we never construct one or fire a request. This is the hard
    #    safeguard that guarantees no accidental live call by default (incl. the suite).
    #
    # An explicitly-passed ``client`` always overrides both (deliberate live/mocked run).
    dry_run = client is None and os.environ.get("MIGRATION_LLM_DRYRUN") == "1"
    no_key = client is None and not os.environ.get("ANTHROPIC_API_KEY")
    if dry_run or no_key:
        note = (
            "dry-run: LLM tier skipped (MIGRATION_LLM_DRYRUN=1)"
            if dry_run
            else "deterministic: LLM tier skipped (no ANTHROPIC_API_KEY — no live call)"
        )
        for residual in residuals:
            exceptions.append(_exception(residual, note=note))
        return {"resolved": resolved, "exceptions": exceptions, "stats": stats}

    # The client is constructed lazily — only when a batch must actually be sent. A
    # run whose residuals are all replayable from the log (or all unsupported types)
    # makes zero calls and needs no SDK / API key.
    def _ensure_client() -> Any:
        nonlocal client
        if client is None:
            if Anthropic is None:
                raise RuntimeError(
                    "anthropic SDK not installed and no client provided. "
                    "Install `anthropic`, pass a client, or set MIGRATION_LLM_DRYRUN=1 for the offline path."
                )
            client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment.
        return client

    groups = _group_by_field_type(residuals)
    breaker_tripped = False

    for field_type, cells in groups.items():
        # Replay first: a cell already in the log with a confident result is reused.
        pending: list[dict[str, Any]] = []
        for residual in cells:
            key = _cell_key(residual)
            prior = logged.get(key)
            if prior is not None and prior.get("parts") is not None:
                _merge_one(field_type, residual, prior["parts"], cache, resolved, exceptions, stats)
                continue
            pending.append(residual)

        if field_type not in _TOOLS:
            for residual in pending:
                exceptions.append(_exception(residual, note=f"unsupported field_type {field_type!r} for LLM tier"))
            continue

        for batch in _chunks(pending, batch_size):
            if breaker_tripped or (max_batches is not None and stats["calls"] >= max_batches):
                breaker_tripped = True
                for residual in batch:
                    exceptions.append(_exception(residual, note="cost-ceiling: max_batches reached"))
                continue
            if stats["input_tokens"] + stats["output_tokens"] >= token_ceiling:
                breaker_tripped = True
                for residual in batch:
                    exceptions.append(_exception(residual, note="cost-ceiling: token budget exhausted"))
                continue

            try:
                results, tokens = _call_model(_ensure_client(), model, field_type, batch)
            except (anthropic.RateLimitError, anthropic.APIError) as exc:  # type: ignore[union-attr]
                # SDK already auto-retried 429/5xx; a raised error is terminal for this batch.
                for residual in batch:
                    exceptions.append(_exception(residual, note=f"llm-call-failed: {type(exc).__name__}"))
                continue

            stats["calls"] += 1
            stats["input_tokens"] += tokens["input_tokens"]
            stats["output_tokens"] += tokens["output_tokens"]

            # Map results back by position; a short/missing array → exception per item.
            for idx, residual in enumerate(batch):
                parts = results[idx] if idx < len(results) else None
                # Log BEFORE merging (idempotent replay on resume).
                key = _cell_key(residual)
                _append_log(
                    log_p,
                    {
                        "table": key[0],
                        "source_id": key[1],
                        "column": key[2],
                        "field_type": field_type,
                        "raw_value": residual.get("raw_value"),
                        "model": model,
                        "parts": parts,
                    },
                )
                _merge_one(field_type, residual, parts, cache, resolved, exceptions, stats)

    return {"resolved": resolved, "exceptions": exceptions, "stats": stats}


def _merge_one(
    field_type: str,
    residual: dict[str, Any],
    parts: Any,
    cache: Optional[TransformCache],
    resolved: list[dict[str, Any]],
    exceptions: list[dict[str, Any]],
    stats: dict[str, int],
) -> None:
    """Re-validate one proposal, route to resolved/exceptions, write back to cache."""
    if parts is None:
        exceptions.append(_exception(residual, note="llm returned no item for this cell"))
        return

    cell = _revalidate_one(field_type, parts)

    # A validator that still wants the LLM, or a below-floor confidence, is an exception.
    if cell.needs_llm or cell.confidence < LLM_CACHE_CONFIDENCE_FLOOR:
        exceptions.append(_exception(residual, note="validator-rejected-or-low-confidence", cell=cell))
        return

    resolved.append(_resolved(residual, cell))

    # Tier-3 write-back: identical input strings short-circuit in every later row/drop.
    if cache is not None:
        transform = _TRANSFORM.get(field_type)
        if transform is not None:
            wrote = cache.store(
                transform[0],
                transform[1],
                residual.get("raw_value"),
                cell,
                residual.get("context_signature", ""),
                model=MODEL,
            )
            if wrote:
                stats["cached_writes"] += 1
