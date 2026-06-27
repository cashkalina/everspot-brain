"""Pipeline configuration resolver — where the Everspot codebase lives on disk.

The pipeline needs the path to the Everspot codebase to:

  1. introspect the target schema (codebase-memory-mcp / grep self-introspection), and
  2. run ``php artisan migration:generate-contract`` (cd into that path).

Today the pipeline lives at ``docs/migration-pipeline/`` *inside* the Everspot repo, so
the default is the repo root computed relative to this file. But the general layer is
slated to move into its own repo (SPEC §16), at which point that relative default no
longer points at Everspot — so the path is resolved with precedence:

    env var ``EVERSPOT_CODEBASE_PATH``
      → an optional config file (``pipeline.toml`` beside the pipeline root,
        key ``everspot_codebase_path`` under ``[paths]`` or top-level)
        → a sensible default (two levels up from this file = the repo root for the
          current in-Everspot checkout).

Everything is stdlib-only (``tomllib`` on 3.11+, with a tiny fallback parse otherwise).

Spec & knowledge:
    SPEC.md §16 (Directory Structure — the eventual relocation hook)
    SPEC.md §18 (Environment — the configurable codebase path)
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

VERSION = "1.0.0"

ENV_VAR = "EVERSPOT_CODEBASE_PATH"

# This file: docs/migration-pipeline/scripts/config.py
#   parents[0] = scripts/   parents[1] = migration-pipeline/   parents[2] = docs/
#   parents[3] = <repo root>  ← the default for the current in-Everspot checkout.
_THIS = Path(__file__).resolve()
PIPELINE_ROOT = _THIS.parents[1]
_DEFAULT_CODEBASE_PATH = _THIS.parents[3]

# Optional config file lives beside the pipeline root (tracked with the general layer).
CONFIG_FILENAME = "pipeline.toml"
CONFIG_PATH = PIPELINE_ROOT / CONFIG_FILENAME

_CONFIG_KEY = "everspot_codebase_path"


def _load_toml(path: Path) -> dict:
    """Parse a small TOML config file with stdlib only.

    Uses :mod:`tomllib` (Python 3.11+). If unavailable, fall back to a minimal
    line parser that handles ``key = "value"`` and a ``[paths]`` table — enough for
    this one key, with no third-party dependency.
    """
    try:
        import tomllib  # type: ignore

        with path.open("rb") as fh:
            return tomllib.load(fh)
    except ModuleNotFoundError:  # pragma: no cover - only on <3.11
        data: dict = {}
        section: Optional[str] = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                section = line[1:-1].strip()
                data.setdefault(section, {})
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if section:
                data[section][key] = value
            else:
                data[key] = value
        return data


def _config_file_path() -> Optional[str]:
    """Return the codebase path from the config file, or ``None`` if absent/unset.

    Accepts either a top-level ``everspot_codebase_path`` or one under ``[paths]``.
    """
    if not CONFIG_PATH.exists():
        return None
    try:
        data = _load_toml(CONFIG_PATH)
    except Exception:
        return None
    value = data.get(_CONFIG_KEY)
    if value is None and isinstance(data.get("paths"), dict):
        value = data["paths"].get(_CONFIG_KEY)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def everspot_codebase_path() -> Path:
    """Resolve the absolute path to the Everspot codebase.

    Precedence: env ``EVERSPOT_CODEBASE_PATH`` → ``pipeline.toml`` → default (the repo
    root, two levels above the pipeline root). The returned path is absolute but is NOT
    asserted to exist — call :func:`everspot_codebase_exists` to check that.
    """
    env = os.environ.get(ENV_VAR)
    if env and env.strip():
        return Path(env.strip()).expanduser().resolve()

    from_file = _config_file_path()
    if from_file:
        candidate = Path(from_file).expanduser()
        if not candidate.is_absolute():
            # A relative path in the config is resolved against the pipeline root.
            candidate = PIPELINE_ROOT / candidate
        return candidate.resolve()

    return _DEFAULT_CODEBASE_PATH


def everspot_codebase_exists() -> bool:
    """True if the resolved codebase path is an existing directory."""
    return everspot_codebase_path().is_dir()


def artisan_path() -> Path:
    """Absolute path to the ``artisan`` binary inside the resolved codebase."""
    return everspot_codebase_path() / "artisan"


def artisan_command(*args: str, php: str = "php") -> list[str]:
    """Build an ``artisan`` argv to run *in* the codebase dir (use ``cwd=...``).

    Example::

        import subprocess
        from config import artisan_command, everspot_codebase_path
        subprocess.run(
            artisan_command("migration:generate-contract"),
            cwd=everspot_codebase_path(),
        )

    The ``php`` binary is configurable for unusual environments; the artisan path is
    relative (``"artisan"``) because the command is meant to run with ``cwd`` set to the
    codebase, matching how ``php artisan migration:generate-contract`` is invoked by hand.
    """
    return [php, "artisan", *args]


def has_php() -> bool:
    """True if a ``php`` binary is on PATH (the artisan runner needs it)."""
    return shutil.which("php") is not None


def generate_contract_argv(*, check: bool = False, tenant: Optional[str] = None,
                           php: str = "php") -> list[str]:
    """Build the ``migration:generate-contract`` argv, passing this pipeline's root.

    The artisan command lives in the Everspot repo but writes the contract INTO this
    pipeline (``contract/`` + ``schemas/``); since the pipeline now lives in its own
    repo, we tell the command where we are via ``--pipeline-root``. Run with
    ``cwd=everspot_codebase_path()``.
    """
    args = ["migration:generate-contract", f"--pipeline-root={PIPELINE_ROOT}"]
    if tenant:
        args.append(f"--tenant={tenant}")
    if check:
        args.append("--check")
    return artisan_command(*args, php=php)
