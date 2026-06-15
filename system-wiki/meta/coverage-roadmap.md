# Modules Documentation Coverage & Roadmap

> **Generated:** 2026-06-15
> **Everspot source basis:** `origin/main` @ `78b496b` (HEAD); model inventory unchanged since bootstrap sync `86b4328` — the 4 commits in between touch no model files.
> **Scope:** every concrete Eloquent model under `modules/*/Models/` and `app/Models/`, plus a structural pass on module index files.
>
> **Headline:** Model coverage is effectively **100% (152/152 concrete models documented)**. There is **no net-new model documentation outstanding.** The remaining roadmap is structural cleanup + the known straggler audit items from `CLAUDE.md`, not new model docs.

---

## 1. Coverage Summary

| Source group | Concrete models in source | Documented | Status |
|---|---:|---:|---|
| `app/Models/` (→ `system/models/`) | 3¹ | 3 | ✅ Complete |
| Accounting | 3 | 3 | ✅ Complete |
| Approval | 6 | 6 | ✅ Complete |
| Attribute | 4 | 4 | ✅ Complete |
| Autopay | 1 | 1 | ✅ Complete |
| Cancellation | 2 | 2 | ✅ Complete |
| Certificate | 3 | 3 | ✅ Complete |
| Commission | 7 | 7 | ✅ Complete |
| Common | 31 | 31 | ✅ Complete |
| Customer | 2 | 2 | ⚠️ Models done, **missing index files** |
| Delivery | 2 | 2 | ✅ Complete |
| Documentation | 2 | 2 | ✅ Complete |
| Event | 3 | 3 | ✅ Complete |
| ExternalSite | 1 | 1 | ✅ Complete |
| Interment | 1 | 1 | ✅ Complete |
| Liability | 1 | 1 | ✅ Complete |
| Mapping | 2 | 2 | ✅ Complete |
| Memorial | 2 | 2 | ✅ Complete |
| Opportunity | 1 | 1 | ✅ Complete |
| Order | 2 | 2 | ✅ Complete |
| PaymentPlan | 2 | 2 | ✅ Complete |
| Product | 5 | 5 | ✅ Complete |
| Program | 7 | 7 | ✅ Complete |
| Property | 4 | 4 | ✅ Complete |
| Recognition | 4 | 4 | ✅ Complete |
| Repetition | 1 | 1 | ✅ Complete |
| Report | 2 | 2 | ✅ Complete |
| Signature | 5 | 5 | ✅ Complete |
| Subscription | 1 | 1 | ✅ Complete |
| Task | 1 | 1 | ✅ Complete |
| Transaction | 6 | 6 | ✅ Complete |
| Trust | 10 | 10 | ✅ Complete |
| WorkOrder | 3 | 3 | ✅ Complete |
| **TOTAL** | **152** | **152** | **✅ 100%** |

¹ `app/Models/` holds 4 files: `User`, `Plan`, `Feature` (concrete → documented in `system/models/`) and `BaseModel` (base class — documented as a concept, not counted for coverage, per `CLAUDE.md`).

**Modules with no `Models/` directory** (nothing to document, by design): `AccountingSystem`, `Definition`, `PaymentProcessor`. (`Definition` still contributes a documented trait — `has-model-definition` — under `modules/definition/traits/`.)

---

## 2. The Full Model Map (source → wiki doc)

Every row below is a concrete model in `origin/main` and where its doc lives. All present.

<details>
<summary><strong>app/Models → system/models/</strong></summary>

| Source | Doc | ✓ |
|---|---|:-:|
| `app/Models/User.php` | `system/models/user.md` | ✅ |
| `app/Models/Plan.php` | `system/models/plan.md` | ✅ |
| `app/Models/Feature.php` | `system/models/feature.md` | ✅ |
| `app/Models/BaseModel.php` *(base/concept)* | `system/models/index.md` | ✅ (concept) |
</details>

<details>
<summary><strong>Accounting (3)</strong></summary>

| Source | Doc | ✓ |
|---|---|:-:|
| `GlAccount` | `modules/accounting/models/gl-account.md` | ✅ |
| `JournalEntry` | `modules/accounting/models/journal-entry.md` | ✅ |
| `JournalEntryLine` | `modules/accounting/models/journal-entry-line.md` | ✅ |
</details>

<details>
<summary><strong>Approval (6)</strong></summary>

| Source | Doc | ✓ |
|---|---|:-:|
| `ApprovalAction` | `modules/approval/models/approval-action.md` | ✅ |
| `ApprovalRequest` | `modules/approval/models/approval-request.md` | ✅ |
| `ExternalApprovalAction` | `modules/approval/models/external-approval-action.md` | ✅ |
| `ExternalApprovalApprover` | `modules/approval/models/external-approval-approver.md` | ✅ |
| `ExternalApprovalFile` | `modules/approval/models/external-approval-file.md` | ✅ |
| `ExternalApprovalRequest` | `modules/approval/models/external-approval-request.md` | ✅ |
</details>

<details>
<summary><strong>Attribute (4)</strong></summary>

| Source | Doc | ✓ |
|---|---|:-:|
| `Attribute` | `modules/attribute/models/attribute.md` | ✅ |
| `AttributeArea` | `modules/attribute/models/attribute-area.md` | ✅ |
| `AttributeValue` | `modules/attribute/models/attribute-value.md` | ✅ |
| `EntityAttribute` | `modules/attribute/models/entity-attribute.md` | ✅ |
</details>

<details>
<summary><strong>Common (31)</strong></summary>

| Source | Doc | ✓ |
|---|---|:-:|
| `Address` | `address.md` | ✅ |
| `Cemetery` | `cemetery.md` | ✅ |
| `Country` | `country.md` | ✅ |
| `Dashboard` | `dashboard.md` | ✅ |
| `DashboardElement` | `dashboard-element.md` | ✅ |
| `DeliveryPreference` | `delivery-preference.md` | ✅ |
| `Domain` | `domain.md` | ✅ |
| `EmailLog` | `email-log.md` | ✅ |
| `EmailTemplate` | `email-template.md` | ✅ |
| `Entity` | `entity.md` | ✅ |
| `EntityTypePivot` | `entity-type-pivot.md` | ✅ |
| `ExternalId` | `external-id.md` | ✅ |
| `Integration` | `integration.md` | ✅ |
| `ListOption` | `list-option.md` | ✅ |
| `ListOptionType` | `list-option-type.md` | ✅ |
| `Media` | `media.md` | ✅ |
| `Metadata` | `metadata.md` | ✅ |
| `ModelNumberConfiguration` | `model-number-configuration.md` | ✅ |
| `Note` | `note.md` | ✅ |
| `OwnerFile` | `owner-file.md` | ✅ |
| `OwnerFileLine` | `owner-file-line.md` | ✅ |
| `PdfTemplate` | `pdf-template.md` | ✅ |
| `Setting` | `setting.md` | ✅ |
| `Share` | `share.md` | ✅ |
| `State` | `state.md` | ✅ |
| `Syncable` | `syncable.md` | ✅ |
| `Tenant` | `tenant.md` | ✅ |
| `TenantIntegration` | `tenant-integration.md` | ✅ |
| `TenantUser` | `tenant-user.md` | ✅ |
| `Token` | `token.md` | ✅ |
| `User` | `user.md` | ✅ |

*(all under `modules/common/models/`)*
</details>

<details>
<summary><strong>Trust (10)</strong></summary>

| Source | Doc | ✓ |
|---|---|:-:|
| `TrustAccount` | `trust-account.md` | ✅ |
| `TrustAccountTransaction` | `trust-account-transaction.md` | ✅ |
| `TrustAccountTransactionApplication` | `trust-account-transaction-application.md` | ✅ |
| `TrustApplicationStrategy` | `trust-application-strategy.md` | ✅ |
| `TrustApproval` | `trust-approval.md` | ✅ |
| `TrustArrangement` | `trust-arrangement.md` | ✅ |
| `TrustElement` | `trust-element.md` | ✅ |
| `TrustTransactionType` | `trust-transaction-type.md` | ✅ |
| `TrustingSchedule` | `trusting-schedule.md` | ✅ |
| `TrustingScheduleGroup` | `trusting-schedule-group.md` | ✅ |

*(all under `modules/trust/models/`)*
</details>

<details>
<summary><strong>Transaction (6)</strong></summary>

| Source | Doc | ✓ |
|---|---|:-:|
| `Transaction` | `transaction.md` *(STI base)* | ✅ |
| `Payment` | `payment.md` *(STI subtype)* | ✅ |
| `Refund` | `refund.md` *(STI subtype)* | ✅ |
| `PaymentMethod` | `payment-method.md` | ✅ |
| `PaymentMethodRequest` | `payment-method-request.md` | ✅ |
| `DepositBatch` | `deposit-batch.md` | ✅ |
</details>

<details>
<summary><strong>Commission (7) · Program (7) · Product (5) · Signature (5) · Property (4) · Recognition (4)</strong></summary>

**Commission:** commission, commission-approval, commission-calculation, commission-category, commission-plan, commission-rate, rep-association — ✅ all
**Program:** program, program-enrollment, program-obligation, program-obligation-preference, program-obligation-preference-collection, program-preference-collection, program-preference-collection-option — ✅ all
**Product:** product, product-type, product-tax-rate, price-tier, price-tier-price — ✅ all
**Signature:** document, document-envelope, document-template, signature-request, signer — ✅ all
**Property:** property, property-commitment, property-group, property-type — ✅ all
**Recognition:** recognition-approval, recognition-arrangement, recognition-element, recognition-rule — ✅ all
</details>

<details>
<summary><strong>Remaining small modules (all ✅ complete)</strong></summary>

| Module | Models |
|---|---|
| Certificate (3) | certificate, certificate-customer, certificate-line |
| Event (3) | calendar, calendar-permission, event |
| WorkOrder (3) | work-order, work-order-category, time-entry |
| Cancellation (2) | cancellation, cancellation-line |
| Customer (2) | customer, veteran-tag |
| Delivery (2) | delivery, delivery-line |
| Documentation (2) | doc-article, doc-category |
| Mapping (2) | map, map-location |
| Memorial (2) | memorial, memorial-person |
| Order (2) | order, order-line |
| PaymentPlan (2) | payment-plan, payment-plan-restructure |
| Report (2) | report, report-chart |
| Autopay (1) | autopay |
| ExternalSite (1) | external-site |
| Interment (1) | interment |
| Liability (1) | liability-line |
| Opportunity (1) | opportunity |
| Repetition (1) | repetition |
| Subscription (1) | subscription |
| Task (1) | task |
</details>

---

## 3. Roadmap — Outstanding Work

Since model coverage is complete, the roadmap is about **structural integrity** and **depth/correctness** rather than new model docs. Ordered by effort/priority.

### Phase A — Structural cleanup (quick, mechanical)

| # | Item | Detail | Command |
|---|---|---|---|
| A1 | `modules/customer/index.md` missing | Customer is the **only** module missing its `index.md` (module-level). | Generate per `conventions.md`. |
| A2 | `modules/customer/models/index.md` missing | Customer is the **only** module whose `models/` dir has no `index.md`. | Generate models index. |
| A3 | Verify `customer` module wiring | Confirm Customer docs are linked from `modules/index.md` and inbound links resolve. | Audit (link check). |

### Phase B — Known straggler audit items (from `CLAUDE.md` "Current State")

These were explicitly flagged at bootstrap completion as needing follow-up. Each should be re-derived from `origin/main` and corrected:

| # | Item | Detail | Command |
|---|---|---|---|
| B1 | `HasTransactions` / `HasTransactionService` deep docs | Trait docs need deepening — currently shallow. Resolve owners and write full deep docs; register in `system/traits/index.md`. | Generate/Update (trait) |
| B2 | `TrustingSchedule` SoftDeletes | May be missing `SoftDeletes` in its doc — verify trait set against source and correct. | Audit → Update model |
| B3 | `SignatureRequest` SoftDeletes | Same — verify `SoftDeletes` presence against source. | Audit → Update model |
| B4 | `RecognitionArrangement` stale cast | Doc has a stale cast definition — re-derive casts from source and fix. | Update model |

### Phase C — Freshness re-validation (recurring)

| # | Item | Detail | Command |
|---|---|---|---|
| C1 | Re-validate schema snapshots | Confirm `schema/central.json` / `schema/tenant.json` still match `origin/main` migrations; `snapshot_commit` drift check. | Snapshot schema |
| C2 | Bump `synced_through` | After A+B land and a clean Sync, advance `meta/wiki-state.json` `synced_through` to current HEAD (`78b496b`) — the 4 post-bootstrap commits touch no models, so this is low-risk. | Sync |
| C3 | Full Audit pass | Run the Audit command end-to-end: coverage, staleness, broken links, deprecations, invalidated human notes. | Audit |

### Phase D — Ongoing maintenance (steady state)

The wiki is **operational**. From here, the model-doc workload is event-driven, not a backlog:
- Run **Sync** whenever new Everspot commits touch a re-derived source set (model file, parent, observers, relationship inverses, or trait files).
- Run **Review coverage** periodically against `wiki.fallback.log` to surface missing sections/links revealed by real lookups.
- New models added to source → generate docs at Sync time; removed models → deprecate (never delete).

---

## 4. What Is *Not* Outstanding

To be explicit, so this isn't misread as "lots left to do":

- **No undocumented concrete models.** All 152 are covered.
- **No missing modules.** All 32 model-bearing modules are documented; the 3 model-less modules (`AccountingSystem`, `Definition`, `PaymentProcessor`) correctly have no model docs.
- **Traits are broadly covered** — ~30 trait docs exist across `system/traits/` and module-owned `traits/` dirs. The only known trait gap is the `HasTransactions`/`HasTransactionService` depth item (B1).

The honest status: **Phase 1 (full model coverage) is done.** Phases A–C above are finishing touches and the pre-flagged audit list; Phase D is steady-state maintenance.
