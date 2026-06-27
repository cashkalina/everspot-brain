# Orion Write-Ergonomics Backlog — Specs for Approval

These specs cover the four §13.3 items (plus the two "optional Orion 1d" items) of
`docs/migration-pipeline/SPEC.md`. They touch the **Everspot repo** and/or are
**auth-adjacent**, so each must be approved before any code is written.

**Binding (applies to every item below):** none of these are implemented yet. None may
touch `AuthenticateTenantApiToken`, token generation, the Orion auth controllers, or the
Sanctum/web-guard wiring — there is no auth-guard bug to "fix" (SPEC §13.1). No PHP is to
be edited as part of producing this document.

How to read the "never blocks the acceptance run" sections: the loader
(`docs/migration-pipeline/scripts/orion_load.py`) already loads the canonical graph
correctly today using the public Orion REST surface only. Every item here is an
**ergonomics / fidelity** improvement, not a correctness prerequisite. Each section states
exactly how today's loader compensates.

---

## (a) Upsert-by-`external_id` (or `external_id` in the create payload) + atomic `HasExternalIds` registration

**Status:** ✅ LANDED 2026-06-27 (shape a1, greenlit). `external_id` is accepted in the create/`batchStore` payload of the Customer/Property/PropertyGroup/Interment/Cemetery/ListOption Orion controllers via `modules/Common/Traits/RegistersExternalIdOnWrite.php` (overrides `performStore` — the one seam shared by single store + each batch item; pops `external_id` before fill so it's never mass-assigned, then registers it on the just-saved model through `HasExternalIds::addExternalId`, inside Orion's store/batch transaction → atomic create+register). The six target models gained `HasExternalIds`. Idempotent (re-registering the same external_id on the same model is a no-op via `updateOrCreate`). Covered by Pest `modules/Common/Tests/Feature/Api/AtomicExternalIdRegistrationTest.php` (6 tests, incl. a mid-batch failure rolling back model + external_id together — no orphan). NO auth/token/guard touched. **Loader adoption DONE 2026-06-27:** `orion_load.py` now sends each NEW record's `external_id` inline in the create/`batchStore` payload (`_create_payload`) and builds the id_map from the create response (`_record_created`), dropping the separate `external-ids` call for new records — one round-trip, no orphan window. The `_repair_orphans`/`_register_orphans` pass is retained as belt-and-suspenders for a crash mid-transaction / legacy unlinked rows. So both halves of (a) — the endpoint and the loader using it — are complete.

### Problem / current behavior

The loader has no way to address a tenant record by its `external_id`, so it does a
prefetch-all + check-then-create dance:

1. `OrionLoader.prefetch_existing_external_ids()` paginates the **entire**
   `external-ids` resource up front (`GET`/`search` over every page) to build an
   `external_id → model_id` map (`orion_load.py:159-163`).
2. Per entity, `load_entity()` partitions records into "already present" vs. "to create"
   by membership in that prefetched map (`orion_load.py:249-256`).
3. NEW records are batch-created against the entity resource; then a **second** call
   (`_register()` → `client.batch_store("external-ids", …)`) registers each new
   `external_id` as a separate `external-ids` row (`orion_load.py:226-242`).

Costs: a full prefetch of the polymorphic `external-ids` table on every run (grows with
the tenant); two round-trips per created record (entity create + external-id register);
and a **non-atomic seam** — if the entity create succeeds but the external-id register
fails, the record exists with no external_id and the next run will not recognize it (it
re-creates → duplicate). The `external-ids` register failure today is only logged
(`orion_load.py:240-241`), not rolled back.

### Proposed change

Two acceptable shapes (pick one at approval):

- **(a1) Accept `external_id` (+ `system`) in the create/batch payload of the entity
  resources**, and have the resource register it atomically inside the same request.
  Concretely: in the entity Orion controllers
  (`modules/Customer/Controllers/Api/CustomerController.php`,
  `modules/Property/Controllers/Api/PropertyController.php` and `PropertyGroupController`,
  `modules/Interment/Controllers/Api/IntermentController.php`) add a guarded
  hook (Orion `afterStore`/`afterBatchStore`) that reads an `external_id`/`system`
  pair off the request and calls the existing
  `Modules\Common\Traits\HasExternalIds::addExternalId()` on the just-created model. All
  four target models already use `HasExternalIds` (trait is at
  `modules/Common/Traits/HasExternalIds.php`; it already does an idempotent
  `updateOrCreate` keyed on `system`). Because Orion batch runs inside a DB transaction
  when `orion.transactions.enabled=true` (see item (b)), the create + register become one
  atomic unit.

- **(a2) True upsert-by-`external_id`** — a dedicated lookup/upsert endpoint (or an Orion
  scope on `external-ids`, e.g. `filter external_id IN (…)`) so the loader can resolve a
  batch of `external_id`s to internal ids in **one** call instead of paginating the whole
  table, and PATCH-or-create accordingly.

Either way the loader drops `prefetch_existing_external_ids()` (full-table scan) and the
separate `_register()` round-trip. (a1) is the smaller, lower-risk change and reuses code
that already exists.

Files it would touch: the four entity Orion controllers above; optionally
`modules/Common/Controllers/Api/ExternalIdController.php` (only if (a2) adds a batch
lookup scope). The trait `HasExternalIds` is reused as-is — no change needed there. No
migration. Loader-side: `orion_load.py` (`prefetch_existing_external_ids`, `_register`,
`load_entity`).

### Why it never blocks the acceptance run

The loader already achieves idempotent, duplicate-free loading **without** this: the
prefetch map + check-then-create gives correct skip/PATCH/create decisions, and the
batch-then-per-record fallback (`orion_load.py:271-287`) isolates bad records. The only
thing missing is efficiency and a tighter atomic guarantee on the create↔register seam —
neither changes what ends up in the tenant on a clean run. The acceptance run loads
correctly today; this just removes a full-table prefetch and a round-trip.

### Risk / auth-sensitivity

Not auth-adjacent. The new hook runs inside the already-authorized Orion request (same
token + `user-id` + policy checks) and reuses the existing, idempotent
`HasExternalIds::addExternalId()`. Risk is contained to the four entity controllers; main
care item is making the register run inside the controller's transaction so the atomic
guarantee actually holds. Approval needed only because it edits Everspot Orion
controllers.

---

## (b) Batch transactions default-on for the migration token (scoped)

**Status:** ✅ LANDED 2026-06-27 (greenlit). A per-controller `transactionsAreEnabled(): bool => true` override was added to the six migration-target Orion controllers, pinning batch atomicity for the load path regardless of the global flag (global `config/orion.php` `transactions.enabled=true` retained). This is what makes (a)'s create+register atomic and what makes a wave re-POST safe for the H3 honest wave-level resume. Proven by the same Pest suite as (a).

### Problem / current behavior

Atomic batches are currently enabled **globally**: `config/orion.php` sets
`transactions.enabled => true` for the whole app (`config/orion.php:19-23`). The Orion
package reads this one flag in `HandlesTransactions::transactionsAreEnabled()`
(`vendor/tailflow/laravel-orion/src/Concerns/HandlesTransactions.php:75-78`) and applies
it to every resource's batch store/update/destroy. So today *every* Orion consumer — not
just the migration loader — gets transaction-wrapped batches.

The loader **depends** on this being on: its batch-then-per-record-fallback
(`orion_load.py:271-287`) is only safe because a failed batch rolls back cleanly (a
partial batch would orphan rows, and the per-record retry would then duplicate the
already-inserted ones). The risk is that the global flag is a shared setting someone could
flip off for unrelated reasons, silently breaking the loader's safety assumption.

### Proposed change

Make atomic batches **scoped/default-on for the migration path** rather than relying on a
global toggle that other consumers share:

- Override `transactionsAreEnabled()` (return `true`) on the four migration-target Orion
  controllers (Customer / Property / PropertyGroup / Interment) so atomicity for the
  load path is guaranteed regardless of the global config value; **or**
- Keep the global flag but document it as load-critical and add a guard/test asserting it
  stays `true` (lower effort, but still a shared setting).

Preferred: the per-controller override — it makes the guarantee local to the resources the
migration writes, decoupled from the global default, and self-documenting.

Files it would touch: the four entity Orion controllers (add a `transactionsAreEnabled():
bool` override); optionally a comment/test pinning `config/orion.php`. No migration, no
loader change (the loader already assumes atomic batches).

### Why it never blocks the acceptance run

It is already on globally today (`config/orion.php`), so the acceptance run already gets
atomic batches and the loader's fallback is already safe. This item only **hardens** the
guarantee against the global flag being changed elsewhere — it does not change current
behavior for the migration path.

### Risk / auth-sensitivity

Not auth-adjacent. Pure controller-behavior config. Risk is negligible: it strengthens an
already-present guarantee. If the per-controller override is chosen, double-check it does
not unexpectedly *narrow* atomicity for any other caller of those same resources (it
shouldn't — it only forces `true`).

---

## (c) First-class Attribute-engine write path for grave location (area `location-property`)

**Status:** Proposed — awaiting approval.

### Problem / current behavior

Grave location (section / lot / space) has **no first-class column** on `properties` — in
Everspot it belongs in the Attribute (custom-fields) engine under the area code
`location-property` (confirmed: `Property::scopeForAreaCode('location-property')`, used by
the Mapping module; declared in `contract/overlay.yaml:90-96`). The canonical record
already carries `section`/`lot`/`space` as first-class scalars, but the loader has nowhere
proper to put them, so it **punts them into the property `description`** as a
human-readable string (`orion_load.py:183-192`, e.g. `"Section A · Row 3 · Grave 12"`).
This is lossy: the values are not queryable as structured attributes, won't appear in
attribute-driven UI/reporting, and won't round-trip.

### Proposed change

Write section/lot/space through the Attribute engine instead of (or in addition to) the
`description` string. The engine pieces already exist and are already exposed over Orion:

- `attribute-areas` (`modules/Attribute/Controllers/Api/AttributeAreaController.php`),
  `entity-attributes` (`EntityAttributeController`), and `attribute-values`
  (`AttributeValueController`) are all registered Orion resources
  (`modules/Attribute/Routes/api.php:20-23`).
- An `AttributeValue` (`modules/Attribute/Models/AttributeValue.php`) carries a
  polymorphic `attributable` morph (`attribute_values.attributable_type/_id`), an
  `attribute_area_id`/`area`, a `type`, `label`, `key`, and `raw_value`
  (`modules/Attribute/Database/Migrations/2024_02_28_183725_create_attribute_values_table.php:15-26`).
  `setRawValueAttribute()` runs the value through the type's `ValueProcessor`.

Proposed loader behavior (after a property is created and its internal id known):

1. Resolve the `location-property` area + its three entity-attributes (section/lot/space)
   via the Orion read backbone (Wave-0 introspection) — these are tenant reference data,
   resolved once.
2. For each property with location scalars, batch-create the corresponding
   `attribute-values` rows (`attributable_type = Property`, `attributable_id = <id>`,
   `attribute_area_id = <location-property id>`, `key`/`type`/`raw_value` per field) via
   the existing `attribute-values` Orion resource.

This needs a new canonical→attribute payload builder in `orion_load.py` (a wave step after
`property`) and the contract overlay already declares the mapping
(`overlay.yaml` `attribute_areas.property.area_code: location-property`). It may also need
the entity-attribute definitions to exist in the tenant (a Wave-0b prerequisite —
create the `location-property` entity-attributes if absent, mirroring how
`ensure_prerequisites()` creates a cemetery/property_type today).

Likely Everspot touch points are **read/reference resolution only** if the
`attribute-values` resource already accepts the needed fields on create — verify whether
`AttributeValueController` exposes `attributable_type`/`attributable_id`/`attribute_area_id`
as fillable over Orion, and whether `setRawValueAttribute` requires `type` set before
`raw_value` (it does — order the payload keys / confirm Orion sets them together). If the
resource doesn't accept the morph/area fields on create, a small controller change there
would be needed; otherwise this is a loader-only change.

Files it would touch: `orion_load.py` (new attribute write step + Wave-0b
entity-attribute prerequisite); possibly
`modules/Attribute/Controllers/Api/AttributeValueController.php` (only if the create
payload needs the morph/area fields made fillable). No migration.

### Why it never blocks the acceptance run

Location is **preserved today**, just in the wrong field: the loader writes a readable
section/lot/space string into the property `description` (`orion_load.py:183-192`), so the
acceptance run loses no information and every property still loads. This item upgrades
fidelity (structured, queryable attributes) — it does not unblock the load.

### Risk / auth-sensitivity

Not auth-adjacent. If it stays loader-only (the Orion `attribute-values` resource already
accepts the create payload), there is no Everspot change at all — same token, same
policies. Risk is data-modeling care: get the area/entity-attribute resolution and the
`type`-before-`raw_value` ordering right so values are stored in the form the
`ValueProcessor` expects. Recommend keeping the `description` string as a transitional
fallback until the attribute write path is validated against a sandbox.

---

## (d) Nullable `interment.date` for historical interments (vs. the `1900-01-01` sentinel)

**Status:** ✅ LANDED 2026-06-27 (ck reversed the earlier deferral — "never fabricate a date"). `interments.date` is now nullable (tenant migration `2026_06_27_000000_make_date_nullable_on_interments_table`); the manual-record stage validation (`getManualValidationRules`) was relaxed (`date` → `nullable`) so a manual+completed undated interment stays completed (non-manual app flow still requires a date). The loader composes `interment.date` from **doi/dod only**, else sends `null` — the `1900-01-01` sentinel and the birthday fallback are removed; the contract/overlay no longer carry a `sentinel`. Covered by `IntermentStatusTest` (null-date manual interment stays completed) + the pipeline regression. Blast radius verified: the `IntermentSaved` listeners read `doi`/`dod` (already null-guarded), `PartialDateCast` backs the partial-date columns (not `date`), and cross-module views use null-tolerant `@displayDate`.

### Problem / current behavior

`interments.date` is **NOT NULL** (`$table->date('date')`,
`modules/Interment/Database/Migrations/2024_01_22_145022_create_interments_table.php:17`).
Many historical interments have no usable date in the source. The loader composes the
column from the best available canonical partial date (doi → dod → dob) and, when none
exists, writes a **sentinel `1900-01-01`** and records a warning into the load report
(`orion_load.py:45`, `_required_date()` at `:91-102`, flag at `:206-211`). So the dateless
records load, but with a fake date that pollutes any date sort/filter/report and must be
remembered as "not real."

### Proposed change

Make `interment.date` nullable so dateless historical interments store `NULL` instead of a
sentinel:

- Migration in `modules/Interment/Database/Migrations/` doing
  `$table->date('date')->nullable()->change()`. Per the Laravel-12 rule, the `change()`
  must re-declare every attribute the column already has so nothing is silently dropped.
  This is a tenant migration (run via `php artisan tenants:migrate`).
- Loader: `_required_date()` returns `(None, …)` when no source date exists and omits the
  sentinel; the warning becomes "date unknown — stored NULL" instead of "set to
  1900-01-01."

**Tradeoffs to decide at approval:**

- *NOT NULL is likely load-bearing somewhere.* `interment.date` being guaranteed-present
  may be assumed across the Interment module and its consumers (recognition, certificates,
  reports, ordering/sorting, blade views). Making it nullable is a schema contract change
  with a blast radius beyond the migration — the impact across callers must be assessed
  (use codebase-memory-mcp `detect_changes` on the column / accessor before approving) and
  any null-unsafe consumer hardened. This is the main reason it's a separate, approved
  item rather than a quiet loader tweak.
- *Sentinel is self-contained.* `1900-01-01` keeps the column non-null and needs zero
  Everspot change; its only cost is the fake value, which is already flagged in the load
  report and in `needs_attention.json` so a reviewer sees exactly which records are
  affected.

Files it would touch: a new Interment migration (column change) and any null-unsafe
consumers surfaced by the impact check; loader `orion_load.py` (`_required_date`, the
warning text). No auth.

### Why it never blocks the acceptance run

Dateless interments already load — with the `1900-01-01` sentinel — and every such record
is flagged in the load report (`orion_load.py:206-211`) and surfaces in
`needs_attention.json`. The acceptance run is complete and auditable without this change;
it's a data-quality improvement that trades a flagged fake value for an honest NULL.

### Risk / auth-sensitivity

Not auth-adjacent, but it is the **highest-blast-radius** item here: relaxing a NOT NULL
constraint on a core column can break any consumer that assumes the date is present. Do not
ship without an impact analysis across the Interment module and downstream
(recognition/certificate/report). The sentinel is the safe status quo; nullability is only
worth it if the consumers are confirmed null-safe (or made so).

---

## Optional "Orion 1d" items (from §13.3)

### (i) Validation Request classes — **safe**

**Status:** Proposed — awaiting approval (low-risk).

Add Laravel Form Request validation to the migration-target Orion resources so malformed
payloads fail with clear, field-level 422s instead of surfacing as opaque batch failures
that force the loader's per-record fallback. Orion supports per-action request classes;
these would live alongside the entity Orion controllers
(Customer/Property/PropertyGroup/Interment) following the existing Form Request convention.
Not auth-adjacent — pure input validation. Improves error legibility; does not change what
loads on a clean run (the loader already isolates bad records).

### (ii) Migration-token type lifting the 7-day cap (IP whitelist retained) — **AUTH-ADJACENT, explicit approval required**

**Status:** Proposed — **EXPLICIT APPROVAL REQUIRED. Do not implement without it.**

Today every tenant API token is hard-capped at 7 days:
`AuthenticateTenantApiToken` rejects any token whose expiration is more than 7 days out
(`app/Http/Middleware/AuthenticateTenantApiToken.php:68-73`), so a long migration has to
re-provision tokens mid-flight. The proposal is a distinct **migration-token type** that
lifts the 7-day cap **while keeping the IP whitelist mandatory** (the IP allowlist checks
at `:75-107` stay exactly as they are).

This is explicitly **auth-adjacent**: it changes the token-expiry security policy and would
touch `AuthenticateTenantApiToken` and/or token generation
(`app/Nova/Actions/Tenant/GenerateStaffApiToken.php`,
`app/Nova/Actions/Tenant/RevokeStaffApiToken.php`, `app/Nova/Tenant.php`) — all of which
are under the binding "never touch auth without explicit approval" rule (SPEC §13.1, §18).
It is documented here for visibility only. **No work, design or code, proceeds on this item
until the user explicitly approves it as a separate decision.**

---

## Summary — approval routing

| Item | Change | Approval class |
|------|--------|----------------|
| (a) upsert / `external_id` in create + atomic register | Edits 4 entity Orion controllers; reuses `HasExternalIds`; drops loader prefetch + register round-trip | **Safe** (not auth) — controller approval |
| (b) batch transactions scoped/default-on for migration | Per-controller `transactionsAreEnabled()` override (or pin the global flag) | **Safe** (not auth) |
| (c) Attribute-engine write path (`location-property`) | Loader writes section/lot/space as `attribute-values`; maybe minor `AttributeValueController` fillable | **Safe** (not auth); data-modeling care |
| (d) nullable `interment.date` | Tenant migration relaxing NOT NULL + null-safe consumers | **Safe re: auth**, but highest blast radius — needs impact analysis |
| (i) validation Request classes | Form Requests on the 4 entity Orion resources | **Safe** |
| (ii) migration-token type lifting 7-day cap | Touches `AuthenticateTenantApiToken` / token generation | **AUTH-ADJACENT — explicit approval required** |
