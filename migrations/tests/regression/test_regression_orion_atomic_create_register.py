"""Regression — A1: NEW-record creation registers the external_id ATOMICALLY in the
create/batch payload — there is NO separate ``external-ids`` registration call, and the
``external_id -> internal id`` map is built from the create RESPONSE.

THE CHANGE: the Orion entity controllers now accept a top-level ``external_id`` in the
create/batchStore payload and register it via ``HasExternalIds`` in the SAME transaction.
So the loader sends external_id inline (one round-trip, no orphan window) and stops making
the separate ``batch_store('external-ids')`` call for newly-created records. It still
PREFETCHES existing external-ids (skip vs create vs PATCH) and keeps the orphan-repair
belt-and-suspenders pass for crash/legacy rows.

A reversion (a separate external-ids batch call for new records, or building id_map from
anything but the response) trips the assertions below.
"""

import orion_load
from external_ids import ExternalIdLedger


class _AtomicClient:
    """Records create payloads + the (forbidden) external-ids call; serves the create id."""

    def __init__(self):
        self._next_id = 700
        self.create_payloads: list[tuple[str, dict]] = []   # (resource, payload)
        self.external_ids_batch_calls = 0

    def paginate(self, resource, **kwargs):
        if resource == "cemeteries":
            return iter([{"id": 1, "name": "Test"}])
        if resource == "property-types":
            return iter([{"id": 2, "name": "Lot"}])
        return iter(())  # empty tenant: nothing pre-existing

    def create(self, resource, payload):
        self._next_id += 1
        self.create_payloads.append((resource, payload))
        return {"id": self._next_id}

    def update(self, resource, rid, payload):  # pragma: no cover
        return {"id": rid}

    def batch_store(self, resource, rows):
        if resource == "external-ids":
            self.external_ids_batch_calls += 1
            return list(rows)
        out = []
        for r in rows:
            self._next_id += 1
            self.create_payloads.append((resource, r))
            out.append({"id": self._next_id})
        return out


class _FakeLedger:
    def everspot_id(self, ref):
        return None

    def attach_everspot_ids(self, mapping):
        pass

    def save(self):
        pass


def _customer(ext, source_id):
    return {
        "external_id": ext, "status": "customer",
        "first_name": "A", "last_name": "B",
        "_provenance": {"table": "T", "row": 1, "source_id": source_id},
        "_confidence": 1.0,
    }


def _loader(client):
    ld = orion_load.OrionLoader(client, _FakeLedger(), cemetery_name="Test")
    ld.cemetery_id = 1
    ld.property_type_id = 2
    return ld


def test_create_payload_carries_external_id_no_separate_register_batch():
    client = _AtomicClient()
    ld = _loader(client)
    records = [_customer(f"src:customer:{i}", f"T:{i}") for i in range(3)]

    ld.load_entity("customer", records)

    # Each create payload carries its own top-level external_id.
    customer_creates = [p for (res, p) in client.create_payloads if res == "customers"]
    assert len(customer_creates) == 3
    assert sorted(p["external_id"] for p in customer_creates) == [
        "src:customer:0", "src:customer:1", "src:customer:2",
    ]

    # NO separate external-ids batch call was made for the new records (server registers
    # atomically from the create payload).
    assert client.external_ids_batch_calls == 0, (
        "new-record creation must not make a separate external-ids registration call"
    )

    # All three counted as created.
    assert ld.result.created["customer"] == 3
    assert ld.result.failed["customer"] == 0


def test_id_map_built_from_create_response():
    client = _AtomicClient()
    ld = _loader(client)
    records = [_customer("src:customer:1", "T:1")]

    ld.load_entity("customer", records)

    # The internal id came back in the create RESPONSE; the loader must map external_id to
    # exactly that returned id (not a guess, not a sentinel).
    created_id = client._next_id  # the last id the client handed back
    assert ld.id_map["src:customer:1"] == created_id
    assert ld.existing["src:customer:1"] == created_id


def test_create_payload_excludes_external_id_from_the_model_projection():
    """external_id is a create-only field; it must NOT pollute the reconcile/PATCH oracle."""
    rec = _customer("src:customer:9", "T:9")
    projection = orion_load.project_payload(
        "customer", rec, cemetery_id=1, property_type_id=2, resolve_ref=lambda r: None,
    )
    assert "external_id" not in projection, (
        "project_payload (the PATCH + reconcile oracle) must not carry external_id"
    )
    # But the create payload DOES carry it.
    ld = _loader(_AtomicClient())
    create_payload = ld._create_payload("customer", rec)
    assert create_payload["external_id"] == "src:customer:9"
