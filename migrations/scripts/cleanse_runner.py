"""The cleanse orchestration glue: value-cache → deterministic tier → (LLM tier).

This is the thin runner that wires the Tier-3 value cache (SPEC §5.3) into the
cleanse path. The cleanse of a single cell is::

    value-cache lookup → deterministic tier → (if needs_llm) LLM tier writes back

:func:`cleanse_with_cache` implements the first two steps and the cache write-back
for deterministic results; the LLM tier itself is **not** called here — it is the
``cleanse --llm`` path (:mod:`llm_fallback`, SPEC §8 stage 8), driven by the
`/migrate` command. A cell that the
deterministic tier marks ``needs_llm`` is returned **as-is** (it stays in
``residuals.jsonl`` for the LLM stage). After the LLM stage produces and *re-validates*
a value, it calls :meth:`TransformCache.store` itself, so any distinct string is
parsed at most once per transform version — across rows and across drops.

Spec & knowledge that specify the rules:
    SPEC.md §5.3                          (lookup-before-deterministic, write-back-after-llm)
    knowledge/topics/name-parsing.md      (the deterministic-then-LLM cleanse tier)
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from cellcontract import Cell
from transform_cache import TransformCache

DeterministicFn = Callable[[Any], Cell]


def cleanse_with_cache(
    transform_name: str,
    transform_version: str,
    input_value: Any,
    deterministic_fn: DeterministicFn,
    context_signature: str = "",
    cache: Optional[TransformCache] = None,
) -> Cell:
    """Cleanse one cell through the value cache, then the deterministic tier.

    Flow (operating-model §5.3):

    1. **Lookup** the value cache. On a hit, return the cached :class:`Cell`
       immediately (already stamped ``method="cache"`` / ``"cache:pinned"``) — no
       deterministic work, and no LLM call even if other cells in the row changed.
    2. On a miss, run ``deterministic_fn`` (the primitive's ``clean``).
       - If the result wants the LLM (``needs_llm``), return it untouched and do
         **not** cache it — it belongs to the LLM tier, which will write back after
         re-validating (``cache.store`` from the ``cleanse --llm`` path).
       - Otherwise it is a confident deterministic result: **store** it (for
         cross-row / cross-drop dedup) and return it.

    Args:
        transform_name: The transform's name (e.g. ``"parse_name"``), part of the key.
        transform_version: The primitive's ``VERSION`` — part of the key and what a
            version bump invalidates.
        input_value: The raw cell value.
        deterministic_fn: The primitive ``clean``-style fn returning a :class:`Cell`.
        context_signature: Column-level decisions that change the output
            (e.g. ``"name_order=last_first"``); empty for context-free transforms.
        cache: An open :class:`TransformCache`. If ``None``, the cache is bypassed and
            ``deterministic_fn`` is called directly (useful for tests / cache-off runs).

    Returns:
        A :class:`Cell`. ``needs_llm`` is preserved so the orchestrator can route
        residuals to the LLM tier exactly as before.
    """
    if cache is None:
        return deterministic_fn(input_value)

    hit = cache.lookup(transform_name, transform_version, input_value, context_signature)
    if hit is not None:
        return hit

    result = deterministic_fn(input_value)
    if not result.needs_llm:
        cache.store(transform_name, transform_version, input_value, result, context_signature)
    return result
