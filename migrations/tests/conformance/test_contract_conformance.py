"""Contract-conformance test (SPEC §6.5 / §12) — LIVE.

Re-runs the codebase-derived Target Contract generator in CHECK mode against the
sandbox tenant and asserts NO drift vs the committed ``contract/target_schema.json``
AND the derived ``schemas/canonical-record.schema.json``. A stale artifact fails.

    php artisan migration:generate-contract --check --pipeline-root=<this pipeline>
        → exit 0  "Contract is up to date"   (no drift)
        → exit 1   on drift (diff printed)

The artisan command lives in the **Everspot** repo, but this pipeline lives in its own
repo — so we resolve the Everspot codebase path via ``scripts/config.py``
(``EVERSPOT_CODEBASE_PATH`` env → ``pipeline.toml`` → default) and tell the command
where to write via ``--pipeline-root``. This requires the live Laravel app + the sandbox
tenant to be reachable, so it is ``@pytest.mark.live`` and SKIPPED by default (the core
suite runs fully OFFLINE and green). Run it with::

    ./.venv/bin/pytest -m live

It self-skips (rather than failing) if ``php``/artisan or the tenant is unreachable.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Resolve the Everspot codebase via the pipeline config (works post-repo-extraction).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import config  # noqa: E402

pytestmark = pytest.mark.live


def _artisan_available() -> bool:
    return config.has_php() and config.artisan_path().exists()


@pytest.mark.skipif(not _artisan_available(), reason="php/artisan not available (offline)")
def test_committed_contract_matches_sandbox_codebase():
    """`migration:generate-contract --check` exits 0 ⇔ committed contract is current."""
    try:
        proc = subprocess.run(
            config.generate_contract_argv(check=True),
            cwd=str(config.everspot_codebase_path()),
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:  # pragma: no cover
        pytest.skip(f"artisan/sandbox unreachable: {exc}")

    output = (proc.stdout or "") + (proc.stderr or "")

    # If the sandbox tenant itself is unreachable, skip rather than fail (the test
    # EXISTS and passes against a live sandbox; it must not redden an offline run).
    if proc.returncode != 0 and any(sig in output.lower() for sig in (
        "connection refused", "could not find driver", "unknown database",
        "no such host", "tenant not found",
    )):
        pytest.skip(f"sandbox tenant unreachable; live check not run:\n{output[:500]}")

    assert proc.returncode == 0, (
        "Target Contract drift: the committed contract/target_schema.json (or the derived "
        "canonical-record.schema.json) is stale vs the sandbox codebase. Re-run "
        "`php artisan migration:generate-contract --pipeline-root=<pipeline>`.\n"
        f"{output}"
    )
    assert "up to date" in output.lower()
