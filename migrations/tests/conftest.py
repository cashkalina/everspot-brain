"""Shared pytest fixtures + path wiring for the §12 migration-pipeline test suite.

Makes ``scripts/`` importable (the modules import each other by bare name, e.g.
``import contract``, ``from identity import ...``), and exposes paths to the
committed contract / schemas / golden fixtures.

The whole default suite is OFFLINE: it never boots Laravel, never hits Orion, never
calls an LLM. Live-only tests are marked ``@pytest.mark.live`` and skipped unless the
sandbox is reachable (see ``tests/conformance/test_contract_conformance.py``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# --------------------------------------------------------------------------- #
# Path wiring                                                                  #
# --------------------------------------------------------------------------- #
PIPELINE_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PIPELINE_ROOT / "scripts"
CONTRACT_PATH = PIPELINE_ROOT / "contract" / "target_schema.json"
SCHEMAS_DIR = PIPELINE_ROOT / "schemas"
CANONICAL_SCHEMA_PATH = SCHEMAS_DIR / "canonical-record.schema.json"
GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
FIXTURES_DIR = GOLDEN_DIR / "fixtures"

# The spine modules import each other by bare name — they must be on sys.path.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Keep the DEFAULT run fully OFFLINE: skip ``live`` tests unless explicitly selected.

    A test marked ``@pytest.mark.live`` requires the live Laravel app + sandbox tenant.
    It runs ONLY when the marker is requested via ``-m live`` (e.g. ``pytest -m live``);
    a bare ``pytest`` skips it so the core suite is green offline / in CI.
    """
    marker_expr = config.getoption("-m", default="")
    if "live" in marker_expr:
        return  # the user explicitly asked for live tests
    skip_live = pytest.mark.skip(reason="live test (needs app + sandbox); run with `-m live`")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session")
def pipeline_root() -> Path:
    return PIPELINE_ROOT


@pytest.fixture(scope="session")
def contract_path() -> Path:
    return CONTRACT_PATH


@pytest.fixture(scope="session")
def canonical_schema() -> dict:
    return json.loads(CANONICAL_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def target_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
