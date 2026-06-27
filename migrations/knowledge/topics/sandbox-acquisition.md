# topics/sandbox-acquisition.md

> **triggers:** `sandbox`, `acquire-target` · stages: acquire-sandbox

Loaded for stage 0 (acquire the load target). The pipeline loads into a **dev sandbox
pulled from production — never the live client tenant.**

## Pull

`pullFromProduction()` calls the production central-domain export API
(`GET /api/sandbox/tenants`, `POST /api/sandbox/exports {tenant_id}`,
`GET /api/sandbox/exports/{id}`), polls until ready, downloads the zip, imports it via
the existing manifest/zip path, **stamps provenance** (`source=production`,
`source_tenant_id`, `pulled_at`), and **scrubs secrets** post-import (Stripe/QBO/mail
nulled). No prod DB creds in dev.

## Deterministic domain

Local domain = `<prod-prefix>-sb.<DEFAULT_ROOT_URL>` (the prod tenant's leftmost label +
`-sb`), with `-1`/`-2` collision uniquify. Because **refresh deletes first**, a re-pull
lands on the **same** domain — only the internal tenant id changes. **Target by domain,
never repoint.**

## Refresh is cache-first

`refreshFromProduction()` defaults to `source=cache`: rebuild from the last cached
artifact (`sandbox_files` import row on the non-suffixed `sandbox_artifacts` disk) →
delete sandbox + re-import from the local zip — **offline, prod never contacted**. On
cache miss / missing file it falls back to a fresh production pull (only the production
branch asserts prod availability, so cache rebuilds work even if prod is down).

So a migration can re-baseline the sandbox between iterations **without losing the
ledger** — the ledger lives in the project dir, not the tenant.

## Typical loop

Pull a fresh sandbox of the client's current production tenant → run the migration into
it → reconcile → iterate the ledger until clean → run the same ledger against the real
target. `sandbox:prune-files` (weekly) keeps N-per-source + an age cap.

## Note

A freshly-pulled prod tenant may be a near-empty shell (few/zero cemeteries, a small set
of seeded list_options). That's normal — Wave-0 introspects what's there and Wave-0b
creates what's missing (see `value-set-resolution`).
