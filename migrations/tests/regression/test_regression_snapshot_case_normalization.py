"""Regression — LESSONS.md #1: snapshot case-sensitivity dropped the declaration.

THE BUG: ``project.yaml`` declares a table by its natural (often UPPERCASE) name
(``CM_CONTACTS``) and a ``source_key`` in the source's casing (``CONTACT_ID``), but
ingest lowercases both the table name (filename → ``cm_contacts``) and the columns
(``contact_id``). The config map was keyed by the RAW declared name and looked up by
the NORMALIZED name, so the declaration silently dropped → identity fell back to a
hash with ``key_status=deferred`` / ``identity_fragile=True`` and no warning. A second
case bug then matched the declared key against lowercased columns → "source_key not
found".

THE FIX: ``snapshot.py`` applies ``normalize_column_name()`` at the ingest boundary to
BOTH the declared table key AND the ``source_key`` / hash columns, so the confirmed
key resolves and identity stays client-anchored.

A reversion (dropping either normalization) makes this fail loudly: the source_id
becomes a ``table:h:<hash>`` value, ``key_status`` becomes ``deferred``, and the row is
flagged fragile.
"""

import pandas as pd

from snapshot import SourceTableConfig, ingest_snapshot


def _write_csv(raw_dir, name, df):
    df.to_csv(raw_dir / name, index=False)


def test_regression_snapshot_case_normalization(tmp_path):
    snap = tmp_path / "snapshots" / "v1"
    raw = snap / "raw"
    raw.mkdir(parents=True)

    # File: CM_CONTACTS.csv with UPPERCASE column headers.
    _write_csv(raw, "CM_CONTACTS.csv", pd.DataFrame({
        "CONTACT_ID": ["A1", "A2"],
        "NAME": ["Alice", "Bob"],
    }))

    # Declaration uses the natural UPPERCASE table name + source key.
    configs = [SourceTableConfig(
        table="CM_CONTACTS",
        source_key=["CONTACT_ID"],
        key_status="confirmed",
    )]

    result = ingest_snapshot(snap, configs)

    # The table ingested under its normalized name.
    assert "cm_contacts" in result.tables

    # The confirmed key resolved → source_id is the human key, NOT a hash.
    index = pd.read_parquet(result.source_index_path)
    source_ids = sorted(index["source_id"].tolist())
    assert source_ids == ["cm_contacts:A1", "cm_contacts:A2"]
    assert not any(":h:" in sid for sid in source_ids)

    # key_status is confirmed (not the hash-based 'deferred' fallback) in the manifest.
    import json
    manifest = json.loads(result.manifest_path.read_text())
    table_entry = manifest["files"][0]["tables"][0]
    assert table_entry["key_status"] == "confirmed"


def test_regression_snapshot_case_normalization_table_parquet_not_fragile(tmp_path):
    snap = tmp_path / "snapshots" / "v1"
    raw = snap / "raw"
    raw.mkdir(parents=True)
    _write_csv(raw, "CM_CONTACTS.csv", pd.DataFrame({"CONTACT_ID": ["A1"], "NAME": ["Alice"]}))

    ingest_snapshot(snap, [SourceTableConfig(table="CM_CONTACTS", source_key=["CONTACT_ID"])])

    table = pd.read_parquet(snap / "tables" / "cm_contacts.parquet")
    assert table["key_status"].iloc[0] == "confirmed"
    assert bool(table["identity_fragile"].iloc[0]) is False
