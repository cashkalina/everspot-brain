"""C1 — the LLM tier is no longer prohibited by policy from seeing real client data.

User decision "option C": AI may process real client data per the user's standing
authorization. ``MIGRATION_LLM_DRYRUN`` is now an OPTIONAL cost/determinism switch, NOT a
mandatory PII gate.

CRITICAL SAFETY (also asserted here): with no ``ANTHROPIC_API_KEY`` and no explicit
client, the run stays deterministic — it must NEVER construct a client or fire a request.
This is what guarantees the test suite (and any default run) makes zero live calls.
"""

from __future__ import annotations

import llm_fallback


_RESIDUALS = [
    {"table": "t", "source_id": "1", "column": "name", "raw_value": "JANE DOE", "field_type": "name"},
    {"table": "t", "source_id": "2", "column": "name", "raw_value": "JOHN SMITH", "field_type": "name"},
]


def test_no_key_no_client_stays_deterministic_no_call(monkeypatch):
    """No key + no client → offline path, zero calls, all residuals → exceptions.

    The model is never instantiated or invoked, so no live call can fire by default.
    """
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MIGRATION_LLM_DRYRUN", raising=False)

    def _boom(*args, **kwargs):  # pragma: no cover - must never be reached
        raise AssertionError("a live model call was attempted with no key configured")

    monkeypatch.setattr(llm_fallback, "Anthropic", _boom)
    monkeypatch.setattr(llm_fallback, "_call_model", _boom)

    result = llm_fallback.resolve_residuals(list(_RESIDUALS), cache=None)

    assert result["stats"]["calls"] == 0
    assert result["resolved"] == []
    assert len(result["exceptions"]) == len(_RESIDUALS)
    assert all("no live call" in e["note"] for e in result["exceptions"])


def test_dryrun_is_optional_switch_not_pii_gate(monkeypatch):
    """MIGRATION_LLM_DRYRUN=1 still skips offline — labeled as a determinism switch."""
    monkeypatch.setenv("MIGRATION_LLM_DRYRUN", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = llm_fallback.resolve_residuals(list(_RESIDUALS), cache=None)

    assert result["stats"]["calls"] == 0
    assert all("dry-run" in e["note"] for e in result["exceptions"])
    # The note must NOT frame this as a PII prohibition.
    assert not any("PII" in e["note"] or "forbidden" in e["note"] for e in result["exceptions"])


def test_policy_allows_live_tier_when_authorized_and_key_present(monkeypatch):
    """With a key present (live opt-in) the gate does NOT forbid the tier by policy.

    We inject a fake client so no real network call fires, and assert the tier actually
    runs it (calls > 0) — i.e. the old "PII forbidden / --authorize-llm required" block
    is gone. The deterministic re-validation still governs the result.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    monkeypatch.delenv("MIGRATION_LLM_DRYRUN", raising=False)

    calls = {"n": 0}

    def _fake_call(client, model, field_type, batch):
        calls["n"] += 1
        results = [
            {"first": "Jane", "middle": None, "last": "Doe", "suffix": None}
            for _ in batch
        ]
        return results, {"input_tokens": 1, "output_tokens": 1}

    monkeypatch.setattr(llm_fallback, "_call_model", _fake_call)

    sentinel_client = object()
    result = llm_fallback.resolve_residuals(list(_RESIDUALS), cache=None, client=sentinel_client)

    assert calls["n"] >= 1
    assert result["stats"]["calls"] >= 1
    # Real client data was processed without any --authorize-llm gate.
    assert len(result["resolved"]) >= 1
