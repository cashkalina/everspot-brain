"""Unit tests for the property-location → Attribute-engine write path (SPEC §13.3c).

The loader writes section/lot/space as structured custom-field values through the
idempotent ``attribute-values/batch-upsert`` Orion endpoint AFTER each property is
created, instead of concatenating them into the free-text ``description``. These tests
drive ``OrionLoader`` against a MOCK ``OrionClient`` (no Laravel, no network) and assert:

  * the batch-upsert payload carries the right entity link (``attributable_type=property``
    + the property's tenant internal id) and the right section/lot/space key/value pairs;
  * the property create payload NO LONGER contains a location ``description``;
  * re-running the same load re-asserts the values via upsert and never duplicates;
  * a missing ``location-property`` area / attribute surfaces as a Wave-0b reference gap
    (ids are never invented), and the location values are not silently written.
"""

from __future__ import annotations

import orion_load
from orion_client import OrionError


class FakeClient:
    """A minimal in-memory stand-in for OrionClient.

    Tracks every create/batch_store/post so tests can assert the exact payloads. The
    Attribute reference reads (``attribute-areas``/``attributes``) are configurable so a
    test can simulate the area/attrs being present or absent.
    """

    def __init__(self, *, has_area=True, attr_keys=("section", "lot", "space")):
        self._next_id = 100
        self.has_area = has_area
        self.attr_keys = attr_keys
        self.created: list[tuple[str, dict]] = []
        self.batched: list[tuple[str, list[dict]]] = []
        self.posts: list[tuple[str, dict]] = []

    # -- reads ------------------------------------------------------------- #
    def paginate(self, resource, *, filters=None, scopes=None, page_size=100):
        if resource == "cemeteries":
            return iter([{"id": 1, "name": "Test Cemetery"}])
        if resource == "property-types":
            return iter([{"id": 7, "name": "Lot"}])
        if resource == "external-ids":
            return iter([])
        if resource == "attribute-areas":
            return iter([{"id": 2, "code": "location-property"}] if self.has_area else [])
        if resource == "attributes":
            ids = {"section": 1, "lot": 2, "space": 3}
            return iter([{"id": ids[k], "key": k} for k in self.attr_keys])
        return iter([])

    # -- writes ------------------------------------------------------------ #
    def create(self, resource, payload):
        self.created.append((resource, payload))
        self._next_id += 1
        return {"id": self._next_id, **payload}

    def batch_store(self, resource, rows):
        self.batched.append((resource, list(rows)))
        out = []
        for r in rows:
            self._next_id += 1
            out.append({"id": self._next_id, **r})
        return out

    def post(self, path, payload):
        self.posts.append((path, payload))
        n = len(payload.get("entities", []))
        return {
            "summary": {"total": n, "successful": n, "failed": 0},
            "errors": [],
            "data": [{"attributable_id": e["attributable_id"], "errors": []}
                     for e in payload["entities"]],
            "message": "ok",
        }


class FakeLedger:
    def __init__(self):
        self.attached: dict[str, int] = {}

    def everspot_id(self, ref):
        return None

    def attach_everspot_ids(self, mapping):
        self.attached.update(mapping)

    def save(self):
        pass


def _prop(ext, section, lot, space):
    return {
        "external_id": ext,
        "property_group_ref": "src:property_group:G",
        "cemetery_ref": "src:cemetery:default",
        "section": section, "lot": lot, "space": space,
        "_provenance": {"table": "t", "row": 1, "source_id": f"sid:{ext}"},
        "_confidence": 1.0,
    }


def _loader(client):
    loader = orion_load.OrionLoader(client, FakeLedger(), cemetery_name="Test Cemetery")
    loader.ensure_prerequisites()
    loader.prefetch_existing_external_ids()
    # property_group must load first so the FK resolves.
    loader.load_entity("property_group", [{
        "external_id": "src:property_group:G", "name": "Default Section",
        "cemetery_ref": "src:cemetery:default",
        "_provenance": {"table": "t", "row": 1}, "_confidence": 1.0,
    }])
    return loader


def test_property_create_payload_has_no_location_description():
    client = FakeClient()
    loader = _loader(client)
    loader.load_entity("property", [_prop("src:property:A1-46", "A", "1", "46")])

    prop_payloads = [p for (res, rows) in client.batched if res == "properties" for p in rows]
    assert prop_payloads, "property should have been created"
    for payload in prop_payloads:
        assert "description" not in payload
        for k in ("section", "lot", "space"):
            assert k not in payload  # location is NOT a property column


def test_batch_upsert_payload_links_entity_and_carries_location_values():
    client = FakeClient()
    loader = _loader(client)
    loader.load_entity("property", [_prop("src:property:A1-46", "A", "1", "46")])
    loader.flush_location_attributes()

    upserts = [body for (path, body) in client.posts if path == "attribute-values/batch-upsert"]
    assert len(upserts) == 1
    entities = upserts[0]["entities"]
    assert len(entities) == 1
    ent = entities[0]
    assert ent["attributable_type"] == "property"
    assert ent["attributable_id"] == loader.id_map["src:property:A1-46"]
    got = {a["key"]: a["value"] for a in ent["attributes"]}
    assert got == {"section": "A", "lot": "1", "space": "46"}
    assert loader.result.attribute_values_written == 1
    assert loader.result.attribute_values_failed == 0
    assert loader.result.reference_gaps == []


def test_blank_location_fields_are_omitted():
    client = FakeClient()
    loader = _loader(client)
    loader.load_entity("property", [_prop("src:property:A--", "A", "", None)])
    loader.flush_location_attributes()

    ent = client.posts[0][1]["entities"][0]
    got = {a["key"]: a["value"] for a in ent["attributes"]}
    assert got == {"section": "A"}  # blank lot + null space dropped


def test_idempotent_rerun_upserts_and_does_not_duplicate():
    client = FakeClient()
    loader = _loader(client)
    rec = _prop("src:property:A1-46", "A", "1", "46")
    loader.load_entity("property", [rec])
    loader.flush_location_attributes()

    # Simulate a re-run: the property now already exists (external-id present), so it is
    # skipped on create but its location is re-queued and upserted again.
    client2 = FakeClient()
    loader2 = orion_load.OrionLoader(client2, FakeLedger(), cemetery_name="Test Cemetery")
    loader2.ensure_prerequisites()
    pid = loader.id_map["src:property:A1-46"]
    loader2.existing["src:property:A1-46"] = pid
    loader2.load_entity("property", [rec])
    loader2.flush_location_attributes()

    # No new property created on the re-run, but location still upserted (idempotent).
    assert not [r for (res, _rows) in client2.batched if res == "properties" for r in [1]]
    upserts = [b for (p, b) in client2.posts if p == "attribute-values/batch-upsert"]
    assert len(upserts) == 1
    ent = upserts[0]["entities"][0]
    assert ent["attributable_id"] == pid
    assert {a["key"]: a["value"] for a in ent["attributes"]} == {"section": "A", "lot": "1", "space": "46"}


def test_missing_area_surfaces_reference_gap_and_writes_nothing():
    client = FakeClient(has_area=False)
    loader = _loader(client)
    loader.load_entity("property", [_prop("src:property:A1-46", "A", "1", "46")])
    loader.flush_location_attributes()

    assert not [b for (p, b) in client.posts if p == "attribute-values/batch-upsert"]
    gaps = loader.result.reference_gaps
    assert len(gaps) == 1 and gaps[0]["kind"] == "attribute_area"
    assert gaps[0]["area_code"] == "location-property"
    assert loader.result.attribute_values_failed == 1


def test_missing_single_attribute_surfaces_gap_but_writes_the_rest():
    client = FakeClient(attr_keys=("section", "lot"))  # 'space' attribute absent
    loader = _loader(client)
    loader.load_entity("property", [_prop("src:property:A1-46", "A", "1", "46")])
    loader.flush_location_attributes()

    gaps = loader.result.reference_gaps
    assert len(gaps) == 1 and gaps[0]["kind"] == "attribute" and gaps[0]["missing_keys"] == ["space"]
    ent = client.posts[0][1]["entities"][0]
    got = {a["key"]: a["value"] for a in ent["attributes"]}
    assert got == {"section": "A", "lot": "1"}  # space dropped, section/lot still written


def test_batch_upsert_endpoint_error_is_recorded_not_raised():
    client = FakeClient()

    def boom(path, payload):
        raise OrionError(500, "kaboom", path)

    client.post = boom  # type: ignore[assignment]
    loader = _loader(client)
    loader.load_entity("property", [_prop("src:property:A1-46", "A", "1", "46")])
    loader.flush_location_attributes()

    assert loader.result.attribute_values_failed == 1
    assert any(e.get("stage") == "attribute-values" for e in loader.result.errors)
