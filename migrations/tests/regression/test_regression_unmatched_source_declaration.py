"""Regression — LESSONS.md #2: unmatched source declaration deferred silently.

THE BUG: a declared ``sources[].table`` that matched NO ingested table was silently
ignored (the defer that masked lesson #1). An operator typo in a filename or a stale
declaration would pass unnoticed — the declared key never applied and any
actually-ingested table without a declaration silently deferred to a hash.

THE FIX: ``snapshot.py`` WARNs on stderr AND records ``unmatched_source_declarations``
in the manifest, so the mismatch is loud and machine-checkable.

A reversion (dropping the warn/record) fails this: the manifest list goes empty.
"""

import json

import pandas as pd

from snapshot import SourceTableConfig, ingest_snapshot


def test_regression_unmatched_source_declaration(tmp_path, capsys):
    snap = tmp_path / "snapshots" / "v1"
    raw = snap / "raw"
    raw.mkdir(parents=True)

    # The actual file is owners.csv ...
    pd.DataFrame({"GUID": ["g1"], "NAME": ["Alice"]}).to_csv(raw / "owners.csv", index=False)

    # ... but the declaration names a table that does NOT exist (typo / stale).
    configs = [
        SourceTableConfig(table="owners", source_key=["GUID"]),
        SourceTableConfig(table="OWNRES_TYPO", source_key=["GUID"]),  # matches nothing
    ]

    result = ingest_snapshot(snap, configs)

    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["unmatched_source_declarations"] == ["ownres_typo"]

    # And it is loud on stderr.
    err = capsys.readouterr().err
    assert "matched no ingested file" in err
    assert "ownres_typo" in err


def test_regression_unmatched_source_declaration_empty_when_all_match(tmp_path):
    snap = tmp_path / "snapshots" / "v1"
    raw = snap / "raw"
    raw.mkdir(parents=True)
    pd.DataFrame({"GUID": ["g1"]}).to_csv(raw / "owners.csv", index=False)

    result = ingest_snapshot(snap, [SourceTableConfig(table="owners", source_key=["GUID"])])
    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["unmatched_source_declarations"] == []
