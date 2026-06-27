"""Regression — H2 / A1: the orphan-repair pass must REPAIR a mid-transaction orphan
on re-run rather than CREATE a DUPLICATE.

THE EXPOSURE: under A1 the external_id rides inside the create payload and the server
registers it ATOMICALLY (HasExternalIds, same transaction), so a normal create has no
orphan window. But a crash AFTER the row insert and BEFORE the registration commit (a
process kill / DB failover mid-transaction), or a legacy row created before A1, can still
leave a model row with NO external_id link — invisible to the next run's
``prefetch_existing_external_ids``. A naive re-run would fall into ``to_create`` again →
DUPLICATE.

THE FIX (pipeline-side belt-and-suspenders, retained from H2): a REPAIR PASS runs before
creating — for any canonical record not yet linked to an external_id, the loader searches
the live entity for a row matching the projected payload (an orphan) and REGISTERS it in
place (an explicit ``external-ids`` batch_store, the one path that still needs it) instead
of creating a duplicate.

This test mocks the FIRST run as a mid-transaction crash: rows persist but their
external_ids never registered. The SECOND run finds the orphans and repairs them —
creating ZERO duplicate model rows.
"""

import orion_load
from external_ids import ExternalIdLedger


class _RegisterFailsThenPersistsClient:
    """Models persist across runs; the first run leaves them UNREGISTERED (crash-mid-txn).

    - ``create``/``batch_store`` on a model resource persists a row (monotonic id) into
      ``self.rows[resource]`` and returns it. While ``self.fail_register`` is True (the
      first run) the external_id carried in the create payload is DROPPED (simulating a
      crash after the row insert, before the atomic registration committed) — so the row
      persists with no external_id link.
    - ``batch_store('external-ids')`` is the REPAIR path (orphan adoption): it records
      registrations into ``self.external_ids``.
    - ``paginate`` reflects persisted rows + registered external-ids, so the second run's
      prefetch + repair search see exactly what the tenant holds.
    """

    def __init__(self):
        self._next_id = 1000
        self.rows: dict[str, list[dict]] = {}
        self.external_ids: list[dict] = []
        self.fail_register = True

    # -- read --
    def paginate(self, resource, **kwargs):
        if resource == "cemeteries":
            return iter([{"id": 1, "name": "Test"}])
        if resource == "property-types":
            return iter([{"id": 2, "name": "Lot"}])
        if resource == "external-ids":
            return iter(list(self.external_ids))
        return iter(list(self.rows.get(resource, [])))

    # -- write --
    def _persist(self, resource, payload):
        self._next_id += 1
        row = dict(payload)
        if self.fail_register:
            # Crash mid-transaction: the row lands but the atomic external_id register is
            # lost, so the persisted row has no external_id link.
            row.pop("external_id", None)
        row["id"] = self._next_id
        self.rows.setdefault(resource, []).append(row)
        return row

    def create(self, resource, payload):
        return self._persist(resource, payload)

    def update(self, resource, resource_id, payload):
        return {"id": resource_id, **payload}

    def batch_store(self, resource, rows):
        if resource == "external-ids":
            # The repair path explicitly registers adopted orphans.
            for r in rows:
                self.external_ids.append(r)
            return list(rows)
        return [self._persist(resource, p) for p in rows]


def _customer(ext, source_id):
    return {
        "external_id": ext,
        "status": "customer",
        "first_name": "A",
        "last_name": "B",
        "_provenance": {"table": "T", "row": 1, "source_id": source_id},
        "_confidence": 1.0,
    }


def _new_loader(client, tmp_path):
    ledger = ExternalIdLedger(tmp_path / "external_ids.json")
    ld = orion_load.OrionLoader(client, ledger, cemetery_name="Test")
    ld.cemetery_id = 1
    ld.property_type_id = 2
    return ld


def test_register_failure_then_rerun_does_not_duplicate(tmp_path):
    client = _RegisterFailsThenPersistsClient()
    records = [_customer(f"src:customer:{i}", f"T:{i}") for i in range(3)]

    # --- First run: a crash mid-transaction — rows persist but lose their external_id. ---
    ld1 = _new_loader(client, tmp_path)
    ld1.prefetch_existing_external_ids()
    ld1.load_entity("customer", records)

    # The model rows really exist in the tenant now (the create returned an id), but the
    # atomic registration was lost to the crash, so the tenant holds no external_ids.
    assert len(client.rows.get("customers", [])) == 3
    assert client.external_ids == []
    # None of the persisted rows carries an external_id link (the orphan condition).
    assert all("external_id" not in r for r in client.rows["customers"])

    # --- Second run: the crash is over; the repair pass must adopt the orphans. ---
    client.fail_register = False
    ld2 = _new_loader(client, tmp_path)
    ld2.prefetch_existing_external_ids()
    ld2.load_entity("customer", records)

    # CRITICAL: no duplicate model rows were created.
    assert len(client.rows.get("customers", [])) == 3, (
        "re-run must REPAIR (register orphans), never CREATE duplicates"
    )
    # All three external_ids are now registered exactly once.
    registered = [e["external_id"] for e in client.external_ids]
    assert sorted(registered) == ["src:customer:0", "src:customer:1", "src:customer:2"]
    assert len(registered) == len(set(registered))
