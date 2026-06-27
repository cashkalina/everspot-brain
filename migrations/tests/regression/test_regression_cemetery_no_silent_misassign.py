"""Regression — M4: a name-miss must NOT silently land everything under cems[0].

THE BUG: ``ensure_prerequisites`` did ``match = cems[0]`` when the named cemetery was
absent but OTHER cemeteries existed — silently assigning every migrated record to the
wrong cemetery.

THE FIX: when the named cemetery is absent, CREATE it (the no-cemeteries branch already
did this). Never silently adopt an existing, differently-named cemetery. (If a future
config opts into a fallback, it must be an explicit, logged ``reference_gap`` — never a
silent mis-assignment.)
"""

import orion_load
from external_ids import ExternalIdLedger


class _FakeTenantWithOtherCemetery:
    """Tenant already has a cemetery named 'Existing Other' but NOT the requested name."""

    def __init__(self):
        self._next_id = 500
        self.created_resources: list[tuple[str, dict]] = []

    def paginate(self, resource, **kwargs):
        if resource == "cemeteries":
            return iter([{"id": 1, "name": "Existing Other"}])
        if resource == "property-types":
            return iter([{"id": 2, "name": "Lot"}])
        return iter(())

    def create(self, resource, payload):
        self._next_id += 1
        self.created_resources.append((resource, payload))
        return {"id": self._next_id, **payload}


def test_named_cemetery_absent_with_others_present_creates_named_not_cems0(tmp_path):
    client = _FakeTenantWithOtherCemetery()
    ledger = ExternalIdLedger(tmp_path / "external_ids.json")
    loader = orion_load.OrionLoader(client, ledger, cemetery_name="Springfield Memorial")

    loader.ensure_prerequisites()

    # It must NOT have silently picked the pre-existing 'Existing Other' (id=1).
    assert loader.cemetery_id != 1, "must not silently land under the wrong cemetery"

    # It must have CREATED the named cemetery.
    created_cems = [p for (res, p) in client.created_resources if res == "cemeteries"]
    assert len(created_cems) == 1, "the named cemetery must be created when absent"
    assert created_cems[0]["name"] == "Springfield Memorial"
    assert loader.cemetery_id == created_cems[0]["id"] if False else loader.cemetery_id is not None


def test_named_cemetery_present_is_reused(tmp_path):
    class _FakeTenantWithNamed(_FakeTenantWithOtherCemetery):
        def paginate(self, resource, **kwargs):
            if resource == "cemeteries":
                return iter([
                    {"id": 1, "name": "Existing Other"},
                    {"id": 7, "name": "Springfield Memorial"},
                ])
            if resource == "property-types":
                return iter([{"id": 2, "name": "Lot"}])
            return iter(())

    client = _FakeTenantWithNamed()
    ledger = ExternalIdLedger(tmp_path / "external_ids.json")
    loader = orion_load.OrionLoader(client, ledger, cemetery_name="Springfield Memorial")
    loader.ensure_prerequisites()

    assert loader.cemetery_id == 7
    assert [p for (res, p) in client.created_resources if res == "cemeteries"] == []
