"""Regression (L4) — schema validation must NOT depend on jsonschema.RefResolver.

``jsonschema.RefResolver.from_schema`` is deprecated as of jsonschema 4.18 (4.26 is
installed here — it still works but warns; a future jsonschema REMOVES it, turning the
call into an ``AttributeError`` raised AFTER the canonical artifact is already written,
crashing the assemble stage). Both validate.py and assemble.py built their validators
on it.

The fix migrates both call sites to the modern ``referencing`` library and broadens the
soft-validate guard to also catch ``AttributeError`` (so a RefResolver-removed future
still degrades to "skip schema check", never crashes after writing canonical).

Tests:
  1. ``test_validate_resolves_refs_without_refresolver`` — the canonical schema's
     ``$ref``s (partialDate, externalId, …) resolve and validate a real record WITHOUT
     RefResolver: a record with a bad partialDate (referenced via ``$ref``) is rejected,
     a good one accepted. Proves the $ref machinery works via ``referencing``.
  2. ``test_soft_validate_survives_refresolver_removed`` — with RefResolver deleted from
     the jsonschema module (simulating its future removal) and ``referencing`` likewise
     hidden, ``assemble._soft_validate`` does NOT raise — it degrades safely.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import assemble as assemble_mod  # noqa: E402
import validate as validate_mod  # noqa: E402

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2] / "schemas" / "canonical-record.schema.json"
)


def _remove_refresolver(monkeypatch) -> None:
    """Simulate a FUTURE jsonschema that has removed RefResolver.

    In 4.26 ``RefResolver`` is served via the module ``__getattr__`` (a deprecated lazy
    attribute), not a real ``__dict__`` entry — so ``delattr`` can't remove it. We patch
    ``__getattr__`` to raise ``AttributeError`` for it, exactly as a release that dropped
    it would (any code calling ``jsonschema.RefResolver`` then gets ``AttributeError``).
    """
    import jsonschema

    original = getattr(type(jsonschema), "__getattr__", None) or jsonschema.__dict__.get("__getattr__")

    def fake_getattr(name):
        if name == "RefResolver":
            raise AttributeError("module 'jsonschema' has no attribute 'RefResolver'")
        if original is not None:
            return original(name)
        raise AttributeError(name)

    monkeypatch.setattr(jsonschema, "__getattr__", fake_getattr, raising=False)
    # Belt-and-suspenders: also drop any cached real entry if present.
    monkeypatch.delitem(jsonschema.__dict__, "RefResolver", raising=False)


def test_validate_resolves_refs_without_refresolver(monkeypatch):
    """The $ref-bearing canonical schema validates records — without RefResolver."""
    # Simulate a future jsonschema that has REMOVED RefResolver: if the validator builder
    # still reaches for it, this raises AttributeError and the test fails loudly.
    _remove_refresolver(monkeypatch)

    validate = validate_mod._schema_validator(SCHEMA_PATH)
    assert validate is not None, "a validator must be built without RefResolver"

    # A well-formed interment with a $ref-validated partialDate (doi) — must pass.
    good = {
        "external_id": "src:interment:register-1",
        "deceased_ref": "src:customer:DECEDENT-1",
        "property_ref": "src:property:register-A-1",
        "status": "completed",
        "doi": {"year": 1981, "month": 11, "day": 2, "estimated": False},
        "_provenance": {"table": "register", "row": 1, "source_id": "register:1"},
        "_confidence": 1.0,
    }
    assert validate("interment", good) == [], "a valid record (with $ref fields) must pass"

    # A partialDate (resolved via $ref to #/$defs/partialDate) that violates the ref'd
    # constraint (month 13) must be REJECTED — proving the $ref actually resolved.
    bad = dict(good)
    bad["doi"] = {"year": 1981, "month": 13, "day": 2, "estimated": False}
    errors = validate("interment", bad)
    assert errors, "an out-of-range partialDate (via $ref) must be caught — proves $ref resolution"


def test_soft_validate_survives_refresolver_removed(monkeypatch, tmp_path):
    """``_soft_validate`` must not crash when BOTH RefResolver and referencing are gone."""
    # Future jsonschema: RefResolver removed.
    _remove_refresolver(monkeypatch)
    # And no `referencing` available either → the builder cannot construct a $ref-aware
    # validator, so it must degrade (skip) rather than raise after canonical is written.
    monkeypatch.setitem(sys.modules, "referencing", None)
    monkeypatch.setitem(sys.modules, "referencing.jsonschema", None)

    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir(parents=True)
    rec = {
        "external_id": "src:customer:DECEDENT-1", "status": "customer",
        "first_name": "Jane", "last_name": "New",
        "_provenance": {"table": "register", "row": 1, "source_id": "register:1"},
        "_confidence": 1.0,
    }
    (canonical_dir / "customer.ndjson").write_text(json.dumps(rec) + "\n", encoding="utf-8")

    result = assemble_mod.AssembleResult(canonical_dir=canonical_dir)
    result.entity_counts = {"customer": 1}

    # Must NOT raise (the bug: AttributeError from RefResolver.from_schema escapes the
    # ImportError-only guard and crashes assemble AFTER canonical is on disk).
    assemble_mod._soft_validate(canonical_dir, result)
