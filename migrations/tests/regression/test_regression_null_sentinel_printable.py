"""Regression — LESSONS.md #3: the ``__NULL__`` sentinel was raw NUL bytes.

THE BUG: the missing-key-component sentinel embedded raw ``\\x00`` into source_ids /
external_ids. The sentinel is rendered LITERALLY into the human-meaningful key segment
of a ``source_id`` (and therefore into the minted ``external_id``), which is written to
wave Excel, logged, and used in the post-load id harvest. Control bytes crashed the
xlsx emitter and left non-printable bytes in ids (bad for logs/URLs).

THE FIX: ``identity._NULL_SENTINEL`` is the printable, xlsx/URL/log-safe token
``"__NULL__"`` — no NUL bytes, no control characters.

A reversion (back to a control-byte sentinel) fails these printability assertions.
"""

import pandas as pd

import identity
from identity import _NULL_SENTINEL, compute_identity


def test_regression_null_sentinel_printable():
    assert _NULL_SENTINEL == "__NULL__"
    # No NUL or other control bytes.
    assert "\x00" not in _NULL_SENTINEL
    assert all(ord(ch) >= 0x20 for ch in _NULL_SENTINEL)
    # Printable + URL/xlsx-safe (alnum + underscore only).
    assert _NULL_SENTINEL.isprintable()
    assert _NULL_SENTINEL.replace("_", "").isalnum()


def test_missing_key_component_renders_printable_sentinel_into_source_id():
    # A confirmed key whose value is blank → the sentinel appears in the source_id,
    # and that source_id must stay printable (it flows into the external_id + xlsx).
    df = pd.DataFrame({"k": [None], "v": ["x"]})
    out = compute_identity(df, ["k"], "tbl", key_status="confirmed")
    source_id = out[identity.SOURCE_ID_COL].iloc[0]
    assert source_id == "tbl:__NULL__"
    assert "\x00" not in source_id
    assert source_id.isprintable()
    # The row is flagged fragile (blank key component), never silently accepted.
    assert bool(out[identity.FRAGILE_COL].iloc[0]) is True
