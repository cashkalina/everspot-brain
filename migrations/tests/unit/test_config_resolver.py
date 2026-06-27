"""B4a — the Everspot-codebase-path resolver.

Precedence: env ``EVERSPOT_CODEBASE_PATH`` → ``pipeline.toml`` → default (repo root,
two levels above the pipeline root). Survives the planned extraction into a separate repo
because the env/config overrides win over the in-Everspot relative default.
"""

from __future__ import annotations

from pathlib import Path

import config


def test_env_override_wins(monkeypatch, tmp_path):
    target = tmp_path / "elsewhere"
    target.mkdir()
    monkeypatch.setenv("EVERSPOT_CODEBASE_PATH", str(target))

    assert config.everspot_codebase_path() == target.resolve()
    assert config.everspot_codebase_exists() is True


def test_falls_back_to_default_when_no_env_and_no_config(monkeypatch, tmp_path):
    """With BOTH the env var and the config file absent, the structural default wins.

    The default is two levels above the pipeline root. Post-repo-extraction that is NOT
    the Everspot codebase (which is why a machine-local pipeline.toml/env override is
    required) — so this test only asserts the resolver's fallback CONTRACT, never that the
    default happens to be Everspot.
    """
    monkeypatch.delenv("EVERSPOT_CODEBASE_PATH", raising=False)
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "absent.toml")

    resolved = config.everspot_codebase_path()

    assert resolved == config.PIPELINE_ROOT.parents[1]
    assert resolved.is_absolute()


def test_configured_codebase_is_a_real_everspot_checkout():
    """When this machine IS configured (env or pipeline.toml), the resolved path must be a
    real directory containing `artisan` — the contract generator runs there. Skips if the
    machine isn't configured (e.g. a fresh clone before pipeline.toml is set)."""
    import os

    configured = bool(os.environ.get(config.ENV_VAR)) or config.CONFIG_PATH.exists()
    if not configured:
        import pytest

        pytest.skip("no EVERSPOT_CODEBASE_PATH env and no pipeline.toml — machine not configured")

    assert config.everspot_codebase_exists() is True
    assert (config.everspot_codebase_path() / "artisan").is_file()


def test_artisan_command_shape():
    argv = config.artisan_command("migration:generate-contract")
    assert argv == ["php", "artisan", "migration:generate-contract"]
    assert config.artisan_path().name == "artisan"


def test_config_file_used_when_no_env(monkeypatch, tmp_path):
    """A ``pipeline.toml`` value is used when the env var is unset (env still wins)."""
    monkeypatch.delenv("EVERSPOT_CODEBASE_PATH", raising=False)

    cfg = tmp_path / "pipeline.toml"
    code_dir = tmp_path / "everspot-checkout"
    code_dir.mkdir()
    cfg.write_text(f'everspot_codebase_path = "{code_dir}"\n', encoding="utf-8")

    monkeypatch.setattr(config, "CONFIG_PATH", cfg)

    assert config.everspot_codebase_path() == code_dir.resolve()

    # env var still takes precedence over the file.
    other = tmp_path / "via-env"
    other.mkdir()
    monkeypatch.setenv("EVERSPOT_CODEBASE_PATH", str(other))
    assert config.everspot_codebase_path() == other.resolve()
