"""External-ID minting, lookup, and the post-load join to Everspot internal IDs.

The ``external_id`` is the permanent bridge between a client record and its
Everspot record. It is *derived from* and *bound to* the ``source_id`` so the same
client record always maps to the same Everspot record across every drop — which is
what makes loads idempotent (upsert by ``external_id``) and makes v2 update rather
than duplicate (operating-model §2, §5.3).

JSON-backed ledger file: ``ledger/external_ids.json`` (schemas/external-ids.schema.json)::

    {
      "schema_version": 1,
      "entries": {
        "MASTER_OWNERS:8841": {
          "external_id": "src:customer:1d1d3f...",   # opaque sha256(source_id) token
          "everspot_id": 50231,          # filled in post-load (Stage 9 ID-harvest)
          "entity": "customer",
          "minted_at": "...",
          "loaded_at": null
        }
      }
    }

The registry is keyed by ``source_id`` (or a ``canonical:<entity>:<n>`` id for
merged/entity-resolved records). The ``external_id`` uses the **full** entity name
(``src:customer:…``); the token is an **opaque** ``sha256(source_id)`` hex digest,
truncated to 20 chars. The token is therefore deterministic and stable (same
``source_id`` → same external_id forever, so upsert/v2-update stay idempotent) but
carries **no** recoverable source value — a client's composite source key can embed
PII (e.g. ``…|THOMPSON|LOIS``), which must never leak into the permanent id, logs,
URLs, the external-ids table, or load-report errors. The human-readable ``source_id``
stays internal: the ledger continues to map ``source_id ↔ external_id`` both ways.

everspot-brain doc that specifies the rules:
    system-wiki/system/has-external-ids.md  (external-id convention & upsert path)
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

VERSION = "2.0.0"

# Canonical entity names accepted by schemas/external-ids.schema.json. Aliases
# (snake/camel/plural) normalize to one of these so external_ids stay consistent.
_ENTITY_CANON = {
    "customer": "customer",
    "address": "address",
    "property": "property",
    "propertygroup": "property_group",
    "property_group": "property_group",
    "interment": "interment",
    "propertycommitment": "property_commitment",
    "property_commitment": "property_commitment",
    "ownerfile": "owner_file",
    "owner_file": "owner_file",
    "ownerfileline": "owner_file_line",
    "owner_file_line": "owner_file_line",
}


def _canon_entity(entity: str) -> str:
    key = entity.strip().lower()
    return _ENTITY_CANON.get(key, re.sub(r"[^a-z_]+", "_", key).strip("_") or "entity")


# sha256 hex truncated to this many chars (4 bits each → 80 bits of entropy).
# Birthday-bound: a 50% collision needs ~2**40 (~1.1e12) records; at a realistic
# per-entity ceiling of ~10M (2**23) records the collision probability is
# ~(2**23)**2 / 2**81 ≈ 3e-11 — negligible. Short enough to stay readable while
# satisfying the schema's non-empty ``.+`` token; opaque enough that no source
# value survives as a substring.
_TOKEN_LEN = 20


def _opaque_token(source_id: str) -> str:
    """A deterministic, opaque token derived from the whole ``source_id``.

    ``sha256(source_id)`` hex, truncated to :data:`_TOKEN_LEN` chars. Stable forever
    (pure function, no randomness/timestamps) so the same ``source_id`` always yields
    the same external_id — upsert/v2-update stay idempotent. Opaque: a client source
    key may embed PII (e.g. ``…|THOMPSON|LOIS``), and the hash guarantees no source
    substring leaks into the permanent id. The forward/reverse mapping lives in the
    ledger, not in the id itself.
    """
    return hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:_TOKEN_LEN]


def mint(source_id: str, entity: str) -> str:
    """Deterministically derive a stable, opaque ``external_id`` for a record.

    Pure function of ``(source_id, entity)`` so re-minting yields the identical
    value — there is no random component. Format: ``src:<entity>:<opaque-token>``,
    where the token is :func:`_opaque_token` of the ``source_id`` (no source value
    is recoverable from it).

    Example:
        ``mint("MASTER_OWNERS:8841", "customer") -> "src:customer:1d1d…"`` (20 hex)
    """
    return f"src:{_canon_entity(entity)}:{_opaque_token(source_id)}"


class ExternalIdLedger:
    """Load/save + mint/lookup the ``external_ids.json`` registry.

    On-disk shape is the schema-conformant ``{schema_version, entries}`` map keyed
    by ``source_id`` (schemas/external-ids.schema.json). An in-memory
    ``by_external_id`` reverse index is rebuilt on load for external→source lookups.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.entries: dict[str, dict] = {}  # source_id -> mint record
        self.by_external_id: dict[str, str] = {}  # external_id -> source_id
        self.schema_version = 1
        if self.path.exists():
            self.load()

    def load(self) -> "ExternalIdLedger":
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.schema_version = int(data.get("schema_version", 1))
        self.entries = data.get("entries", {})
        self.by_external_id = {
            rec["external_id"]: sid
            for sid, rec in self.entries.items()
            if rec.get("external_id")
        }
        return self

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"schema_version": self.schema_version, "entries": self.entries},
                indent=2,
            ),
            encoding="utf-8",
        )

    def mint_for(self, source_id: str, entity: str) -> str:
        """Mint (idempotently) and register an ``external_id`` for ``source_id``.

        If one already exists for this ``source_id`` it is returned unchanged —
        external_ids are minted exactly once (operating-model §5.4).
        """
        existing = self.entries.get(source_id)
        if existing is not None:
            return existing["external_id"]
        ext = mint(source_id, entity)
        self.entries[source_id] = {
            "external_id": ext,
            "everspot_id": None,
            "entity": _canon_entity(entity),
            "minted_at": datetime.now(timezone.utc).isoformat(),
            "loaded_at": None,
        }
        self.by_external_id[ext] = source_id
        return ext

    def lookup_by_source(self, source_id: str) -> Optional[str]:
        rec = self.entries.get(source_id)
        return rec["external_id"] if rec else None

    def lookup_by_external(self, external_id: str) -> Optional[dict]:
        source_id = self.by_external_id.get(external_id)
        return self.entries.get(source_id) if source_id else None

    def everspot_id(self, external_id: str) -> Optional[int]:
        rec = self.lookup_by_external(external_id)
        return rec.get("everspot_id") if rec else None

    def attach_everspot_ids(self, mapping_from_orion: dict[str, int]) -> int:
        """Post-load join: record the Everspot internal id for each external_id.

        Stage 9 harvests ``external_id -> everspot internal id`` either from the
        External-IDs Excel export or live via the Orion ``external-ids`` resource
        (plan §3 stage 9). Pass that ``{external_id: everspot_id}`` map here.

        Returns:
            The number of external_ids successfully resolved.
        """
        resolved = 0
        now = datetime.now(timezone.utc).isoformat()
        for ext, internal in mapping_from_orion.items():
            source_id = self.by_external_id.get(ext)
            rec = self.entries.get(source_id) if source_id else None
            if rec is not None:
                rec["everspot_id"] = int(internal)
                rec["loaded_at"] = now
                resolved += 1
        return resolved

    def unresolved(self) -> Iterable[str]:
        """external_ids minted but not yet linked to an Everspot id (pre-load)."""
        return (r["external_id"] for r in self.entries.values() if r.get("everspot_id") is None)
