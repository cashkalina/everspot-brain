---
model: Certificate
module: Certificate
table: certificates
connection: tenant
primary_source: modules/Certificate/Models/Certificate.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Certificate/Observers/CertificateObserver.php
  - modules/Certificate/Providers/CertificateServiceProvider.php
  - modules/Common/Models/Cemetery.php
  - modules/Common/Models/ListOption.php
  - modules/Common/Models/Note.php
  - modules/Common/Models/User.php
  - modules/Certificate/Models/CertificateCustomer.php
  - modules/Certificate/Models/CertificateLine.php
  - modules/Interment/Models/Interment.php
traits:
  - HasApprovals
  - HasAttributes
  - HasByUserFields
  - HasFiles
  - HasModelNumbering
  - HasSearch
  - SoftDeletes
related_models: [Cemetery, CertificateCustomer, CertificateLine, Interment, ListOption, Note, User]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [document, contract, core]
---

# Certificate

## Overview

The Certificate model represents an official cemetery certificate issued to one or more customers, typically documenting rights of interment or property ownership. Certificates are the primary legal instrument Everspot generates for customers, and they go through a defined lifecycle: `pending` → `issued` (or `voided`).

A certificate belongs to a specific cemetery and is typed via a `ListOption` reference. It carries an `issued_to` display string (typically generated from associated customer full names), a `model_no` for user-facing reference, and timestamps for when it was issued and printed. The approval workflow (via `HasApprovals`) controls the transition from `pending` to `issued`: approving an approval request triggers `onApprovalRequestApproval()`, which calls the `IssueCertificate` action.

Certificates are composed of one or more `CertificateLine` records — each line represents a product or property right granted by the certificate — and are associated with one or more customers through `CertificateCustomer` pivot records. They also link to `Interment` records to represent the interment(s) covered by the certificate. Rich property-grouping helpers (`getGroupedPropertyLines()`, `getSimpleGroupedPropertyLines()`, `getPropertyLinesAsText()`) are provided for PDF rendering.

Soft delete is enabled; certificates are archived, not destroyed.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| date | date | No | - | Certificate date |
| cemetery_id | bigint | No | - | FK → cemeteries: issuing cemetery |
| type_id | bigint | No | - | FK → list_options: certificate type |
| status | varchar | No | - | Lifecycle status (`pending`, `issued`, `voided`) |
| model_no | varchar | Yes | - | User-facing certificate number (via [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — see trait doc); unique |
| issued_to | varchar | Yes | - | Display name(s) of customer(s) the certificate is issued to |
| is_replacement | tinyint | No | 0 | Whether this is a replacement for a previously issued certificate |
| issued_by | bigint | Yes | - | FK → users: user who issued the certificate |
| issued_at | datetime | Yes | - | Timestamp when the certificate was issued |
| printed_at | datetime | Yes | - | Timestamp when the certificate was printed |
| created_by | bigint | Yes | - | User who created the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| updated_by | bigint | Yes | - | User who last updated the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| deleted_by | bigint | Yes | - | User who soft-deleted the record (via [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — see trait doc) |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Unique indexes:** `model_no`

**Foreign keys:** `cemetery_id` → `cemeteries.id`; `type_id` → `list_options.id`; `issued_by`, `created_by`, `updated_by`, `deleted_by` → `users.id`

**Indexes:** single-column indexes on `cemetery_id`, `issued_by`, `issued_to`, `status`, `type_id`, `created_by`, `updated_by`, `deleted_by`

## Casts

- `date` → `date`
- `issued_at` → `TimezonedDateTime::class` — timezone-aware datetime (see `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)
- `printed_at` → `TimezonedDateTime::class` — timezone-aware datetime

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

**Constants / static config:**
```php
const STATUSES = [
    'pending' => ['label' => 'Pending', 'color' => 'warning'],
    'issued'  => ['label' => 'Issued',  'color' => 'success'],
    'voided'  => ['label' => 'Voided',  'color' => 'danger'],
];
```

Status-check methods (`isIssued()`, `isPending()`, `isVoided()`) and status-scopes (`issued()`, `pending()`, `voided()`) are auto-generated by `BaseModel` from `STATUSES` entries.

## Accessors & Mutators

- `getFormattedTypeAttribute(): ?string` — returns `typeOption->name` for the certificate type
- `getIsPrintedStyledTextAttribute(): string` — HTML `<span>` styled bold green "Yes" or red "No" indicating print status

## Traits

- [HasApprovals](../../../system/traits/index.md#hasapprovals) — internal approval workflow controlling the `pending` → `issued` transition; `onApprovalRequestApproval()` triggers `IssueCertificate`
- [HasAttributes](../../../system/traits/index.md#hasattributes) — EAV custom attributes for storing dynamic per-certificate fields
- [HasByUserFields](../../../system/traits/index.md#hasbyuserfields) — `createdBy()` / `updatedBy()` / `deletedBy()` audit stamps
- [HasFiles](../../../system/traits/index.md#hasfiles) — Spatie MediaLibrary attachments for certificate file storage
- [HasModelNumbering](../../../system/traits/index.md#hasmodelnumbering) — generates the user-facing `model_no`
- [HasSearch](../../../system/traits/index.md#hassearch) — search indexing; `addToSearchData()` adds `issued_to` to the searchable payload
- [SoftDeletes](../../../system/traits/index.md#softdeletes) — certificates are soft-deleted, never hard-deleted

## Relationships

- `cemetery()` — belongs to [Cemetery](../../common/models/cemetery.md): the issuing cemetery
- `typeOption()` — belongs to [ListOption](../../common/models/list-option.md) (`type_id`): the certificate type
- `issuedBy()` — belongs to [User](../../common/models/user.md) (`issued_by`): the user who issued the certificate
- `customers()` — has many [CertificateCustomer](./certificate-customer.md): pivot records linking customers to this certificate
- `lines()` — has many [CertificateLine](./certificate-line.md): the line items (products/properties) included in this certificate
- `notes()` — morphMany [Note](../../common/models/note.md) (`notable`): notes attached to the certificate
- `interments()` — has many [Interment](../../interment/models/interment.md): interments covered by this certificate

## Scopes

Status-based query scopes are auto-generated by `BaseModel` from `STATUSES`:
- `pending(Builder $query)` — filters to `status = 'pending'`
- `issued(Builder $query)` — filters to `status = 'issued'`
- `voided(Builder $query)` — filters to `status = 'voided'`

## Events

_None defined on the model._ Lifecycle behavior is handled by `CertificateObserver` (see Observers).

## Observers

- `CertificateObserver` — registered in `CertificateServiceProvider::registerObservers()` (`Certificate::observe(CertificateObserver::class)`). Handles:
  - `created` — fires `analytics()->track('Certificate Created')`
  - `deleting` — wraps deletion in a DB transaction via `PreDeleteCertificate` action

## Key Methods

- `generateIssueTo($customers): ?string` *(static)* — maps a collection of customers to their `full_name` and joins them with ` & `; used to populate the `issued_to` column
- `isPrinted(): bool` — returns `true` if `printed_at` is set
- `setPrinted(): void` — sets `printed_at` to `now()` and saves the record
- `canBeSetPrinted(): bool` — `true` when the certificate is issued and not yet printed
- `canBeSetNotPrinted(): bool` — `true` when the certificate has been printed (allows un-printing)
- `onApprovalRequestApproval(): void` — approval hook: executes `IssueCertificate` action to transition status to `issued`
- `getQuickApproveActionName(): string` — returns `'Issue Certificate'` for the approval UI label
- `addToSearchData(): array` — extends the search payload with `issued_to`
- `propertyLines(): HasMany` — returns lines that have a `property_id` or `property_type_id` set
- `numberOfPropertyLines(): int` — count of property lines
- `getGroupedPropertyLines(): array` — hierarchically groups property lines by location attributes (section, lot, space, etc.) via `GroupCertificateLinesByLocation`; useful for detailed PDF layouts
- `getSimpleGroupedPropertyLines(): Collection` — flat grouping by location (all levels except last) via `GroupCertificateLinesByLocation`; designed for PDF templates
- `getPropertyLinesAsText(string $groupSeparator, string $spaceSeparator, bool $useColonFormat): string` — property lines as a single formatted text string (e.g., `"Area: E | Lot: 6A | Spaces: E, F"`)
- `getPropertyLinesAsTextArray(string $spaceSeparator): array` — property lines as an array of per-group text strings

## Factory & Seeders

- Factory: `modules/Certificate/Database/Factories/CertificateFactory.php`

## Common Usage

```php
// Create a pending certificate
$certificate = Certificate::create([
    'date'        => today(),
    'cemetery_id' => $cemetery->id,
    'type_id'     => $typeOption->id,
    'status'      => 'pending',
    'issued_to'   => Certificate::generateIssueTo($customers),
]);

// Add a customer link
$certificate->customers()->create([
    'customer_id'   => $customer->id,
    'customer_name' => $customer->full_name,
]);

// Attach lines
$certificate->lines()->create([
    'product_name'      => 'Right of Interment',
    'liability_line_id' => $liabilityLine->id,
]);

// Check status
if ($certificate->isPending()) {
    // submit for approval
}

// Print handling
if ($certificate->canBeSetPrinted()) {
    $certificate->setPrinted();
}

// Scope queries
$issuedCerts = Certificate::issued()->get();

// Render property lines for a PDF
$text = $certificate->getPropertyLinesAsText();  // "Area: E | Lot: 6A | Spaces: E, F"
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
