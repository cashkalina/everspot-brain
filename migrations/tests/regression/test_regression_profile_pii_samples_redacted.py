"""Regression — L1: PII in profile samples is volume-capped, not redacted.

THE BUG: ``profile_column`` wrote up to 10 REAL sample values (and value-sets up to 50)
of name/phone/address columns VERBATIM into ``profile/*.json`` + ``summary.json``. The
"PII-aware" docstring overstated a mere COUNT cap — actual PII (people's names, phone
numbers, street addresses) leaked into committed profile artifacts.

THE FIX: for columns the profiler itself flags with a PII signal (name/phone/address/
etc.), the sample values are REDACTED/HASHED (a short stable hash) instead of emitted
verbatim. Non-PII columns keep real samples (they're useful for mapping). The redaction
is driven off the existing shape signals — no client column names.

A reversion (emitting verbatim PII samples) fails this: the real value appears in the
profile output.
"""

from __future__ import annotations

import pandas as pd

import profile as P


def test_pii_name_column_samples_are_redacted():
    df = pd.DataFrame({
        "decedent_name": ["Robert Johnson", "Mary Williams", "James Brown", "Patricia Davis"],
    })
    cp = P.profile_column(df["decedent_name"], "decedent_name", len(df))

    assert "name" in cp.signals, "column should be flagged PII (name)"
    out = cp.to_dict()
    # No verbatim PII in the serialized sample.
    for raw in ["Robert Johnson", "Mary Williams", "James Brown", "Patricia Davis"]:
        assert raw not in out["sample"], f"verbatim PII leaked: {raw}"
        assert all(raw not in s for s in out["sample"]), f"verbatim PII leaked inside sample: {raw}"
    # Sample is still present (count preserved) but redacted/hashed.
    assert len(out["sample"]) == 4
    assert all(isinstance(s, str) and s for s in out["sample"])


def test_pii_phone_and_address_columns_redacted():
    phones = ["(555) 123-4567", "555-987-6543", "555.111.2222", "5559998888"]
    addrs = ["123 Main St", "456 Oak Avenue", "789 Pine Road", "12 Elm Drive"]
    df = pd.DataFrame({"phone": phones, "home_addr": addrs})

    cp_phone = P.profile_column(df["phone"], "phone", len(df))
    cp_addr = P.profile_column(df["home_addr"], "home_addr", len(df))

    assert "phone" in cp_phone.signals
    assert "address" in cp_addr.signals

    for raw in phones:
        assert raw not in cp_phone.to_dict()["sample"]
    for raw in addrs:
        assert raw not in cp_addr.to_dict()["sample"]


def test_non_pii_column_keeps_real_samples():
    df = pd.DataFrame({"status": ["ACTIVE", "CLOSED", "PENDING", "ACTIVE"]})
    cp = P.profile_column(df["status"], "status", len(df))
    assert not (set(cp.signals) & {"name", "phone", "address"})
    out = cp.to_dict()
    # Real, useful values retained for non-PII columns.
    assert "ACTIVE" in out["sample"]
    assert "CLOSED" in out["sample"]


def test_redaction_is_stable_for_equal_values():
    """Same raw value → same redacted token (stable hash), so frequency structure shows."""
    df = pd.DataFrame({"sur_name": ["Smith", "Smith", "Jones", "Smith"]})
    cp = P.profile_column(df["sur_name"], "sur_name", len(df))
    assert "name" in cp.signals
    # sample is distinct values; redaction must be deterministic across calls.
    cp2 = P.profile_column(df["sur_name"], "sur_name", len(df))
    assert cp.to_dict()["sample"] == cp2.to_dict()["sample"]
    # And the redacted token for "Smith" must not equal the token for "Jones".
    tok_smith = P._redact_sample_value("Smith")
    tok_jones = P._redact_sample_value("Jones")
    assert tok_smith != tok_jones
    assert "Smith" not in tok_smith and "Jones" not in tok_jones
