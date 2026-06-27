"""Regression: minted external_ids must be OPAQUE — never leak source PII.

A client's source key can be a composite that embeds personal data, e.g.
``register:bells_chapel-A|1|46|THOMPSON|LOIS`` (section, row, grave, surname,
first name). The old token scheme rendered the raw source_id into the external_id,
so the decedent's name leaked verbatim into the permanent id (and from there into
logs, URLs, the external-ids table, and load-report errors).

The external_id must instead carry a deterministic, opaque hash of the source
identity — stable forever (so idempotency/upsert/v2-update keep working) but with
no recoverable source substring.
"""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from external_ids import ExternalIdLedger, mint  # noqa: E402

_NAME_BEARING_SOURCE_ID = "register:bells_chapel-A|1|46|THOMPSON|LOIS"


def test_mint_does_not_leak_source_pii():
    ext = mint(_NAME_BEARING_SOURCE_ID, "interment")
    assert "THOMPSON" not in ext, f"surname leaked into external_id: {ext}"
    assert "LOIS" not in ext, f"first name leaked into external_id: {ext}"
    # No source value at all should survive as a substring of the token.
    assert "bells_chapel" not in ext


def test_mint_keeps_entity_prefix():
    ext = mint(_NAME_BEARING_SOURCE_ID, "interment")
    assert ext.startswith("src:interment:"), ext
    # Schema pattern ^src:[a-z_]+:.+$ — token is non-empty.
    assert len(ext.split(":", 2)[2]) > 0


def test_mint_is_stable_across_calls():
    a = mint(_NAME_BEARING_SOURCE_ID, "interment")
    b = mint(_NAME_BEARING_SOURCE_ID, "interment")
    assert a == b, "mint must be deterministic — same source_id → same external_id"


def test_mint_is_distinct_for_distinct_source_ids():
    a = mint("register:bells_chapel-A|1|46|THOMPSON|LOIS", "interment")
    b = mint("register:bells_chapel-A|1|47|THOMPSON|LOIS", "interment")
    assert a != b, "distinct source_ids must produce distinct external_ids"


def test_mint_token_does_not_leak_via_ledger(tmp_path):
    ledger = ExternalIdLedger(tmp_path / "external_ids.json")
    ext = ledger.mint_for(_NAME_BEARING_SOURCE_ID, "interment")
    assert "THOMPSON" not in ext and "LOIS" not in ext, ext
    # Re-mint returns the SAME (idempotent) value, still opaque.
    assert ledger.mint_for(_NAME_BEARING_SOURCE_ID, "interment") == ext
