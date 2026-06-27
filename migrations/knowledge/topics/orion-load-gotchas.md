# topics/orion-load-gotchas.md

> **triggers:** `orion-load`, `live-load`, `reference-write` · stages: wave-0, wave-0b, load, reconcile

Loaded for any stage that talks to the live Orion API (reference reads, Wave-0b writes,
the actual load, post-load reconcile). The hard-won facts from live loads.

## Connection

- **Prefix is `/api/v1`, NOT `/api`.** `orion_client.py` base URL ends in `/api/v1`.
- **`verify=False`** on the session for Herd's self-signed cert (`_session.verify=False`).
- **Use `paginate()` to yield rows.** `search()` returns the raw envelope, not the rows.

## Auth (THERE IS NO BUG — never "fix" it)

Token model: tenant `staff_api_token` = **sha256 of the plaintext** token, ≤7-day
expiry, IP-whitelisted; plus a **`user-id` header** for a user with the right Spatie
permissions. The middleware sets the user on the **web** guard; Sanctum resolves
`config('sanctum.guard')=['web']` first → policy-enforced reads/writes work. **Never
touch `AuthenticateTenantApiToken` or token generation without explicit approval.**

## Payload gotchas

- **Cemetery `attribute_data` / `config_data` must be JSON *strings* `"{}"`, not arrays** (json column + Spatie schemaless).
- **External-ids resource `model_type` = the FQCN** (no morphMap) when registering an external_id on the polymorphic `external-ids` resource.
- **Property location (section/lot/space) → Attribute engine, NOT `description`.** After a property is created, the loader resolves the `location-property` area + its section/lot/space attributes once (Orion `attribute-areas`/`attributes` reads, like list_options), then POSTs `attribute-values/batch-upsert` (`{entities:[{attributable_type:"property", attributable_id, attributes:[{key,value}]}]}`). The endpoint matches by attribute **key** and upserts in place → idempotent (re-runs don't duplicate AV rows). The short `attributable_type` is `"property"` (the controller's typeMap), and `value` is the raw scalar string. If the area/attribute is missing it surfaces as a Wave-0b `reference_gap` — never invent ids. Key-level failures come back in the response's `data[].errors`; entity-level (model not found) in top-level `errors`.

## Atomic batches (the duplication trap)

Orion batch-create is **non-atomic by default**. A batch that fails partway leaves orphan
inserts (rows with no external_id); the loader's per-record fallback then **re-inserts
them → duplicates** (observed as false multi-occupancy). **Fix: `config/orion.php`
`transactions.enabled=true`** → a failed batch rolls back → the per-record fallback is
safe. On a batch error, retry the chunk per-record to isolate the bad row.

## Load shape

Wave-ordered, idempotent: prefetch existing external-ids → skip already-loaded-unchanged,
PATCH delta-CHANGED, batch-create NEW (chunks of 100) + batch-register external_ids.
Resolve FKs via the external_id→internal-id map built as the load proceeds.

## Wave-0b reference writes

Mint missing list_options via `orion_client.create("list-options", {type,
list_option_type_id, name, key})`, then **write the new ids back to the ledger** and
re-resolve. Closes the round-trip: read → find-missing → create → re-resolve → assemble
clean. Never invent an id (see `value-set-resolution`).
