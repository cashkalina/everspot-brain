---
model: ExternalApprovalFile
module: Approval
table: external_approval_files
connection: tenant
primary_source: modules/Approval/Models/ExternalApprovalFile.php
source_paths:
  - app/Models/BaseModel.php
  - modules/Approval/Models/ExternalApprovalRequest.php
  - modules/Approval/Models/ExternalApprovalAction.php
  - modules/Approval/Models/ExternalApprovalApprover.php
  - modules/Common/Models/PdfTemplate.php
  - modules/Approval/Providers/ApprovalServiceProvider.php
traits:
  - InteractsWithMedia
related_models: [ExternalApprovalAction, ExternalApprovalApprover, ExternalApprovalRequest, PdfTemplate]
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, document, integration]
---

# ExternalApprovalFile

## Overview

`ExternalApprovalFile` represents a single document attached to an [ExternalApprovalRequest](./external-approval-request.md) for external parties to review. Files can be uploaded directly or generated from a [PdfTemplate](../../common/models/pdf-template.md). The model implements Spatie's `HasMedia` interface via the [InteractsWithMedia](../../../system/traits/index.md#interactswithmedia) trait and registers a single `external_approval_files` media collection.

Files can be configured to require viewing (`require_view`) and/or individual approval (`require_individual_approval`) before an approver can submit their overall response on the parent request. The `display_order` column controls the presentation sequence in the portal.

This model is **insert-only** regarding timestamps — it declares `const UPDATED_AT = null` and `$timestamps = ['created_at']`, so no `updated_at` column exists in the database.

Per-file viewer and approval state is tracked via [ExternalApprovalAction](./external-approval-action.md) records (the `actionable` polymorphic side), not by columns on this model.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| external_approval_request_id | bigint | No | - | FK → external_approval_requests: the parent request |
| file_source | enum | No | upload | Source type: `upload` or template-generated |
| pdf_template_id | bigint | Yes | - | FK → pdf_templates: the template used to generate this file (null for direct uploads) |
| source_media_id | bigint | Yes | - | FK to source media if generated from an existing media record |
| message | text | Yes | - | Optional message or description shown to the approver |
| display_order | int | No | 0 | Presentation order in the approval portal |
| require_view | tinyint | No | 1 | Whether the approver must view this file before submitting a response |
| require_individual_approval | tinyint | No | 0 | Whether the approver must individually approve this file |
| created_at | timestamp | Yes | - | Creation timestamp (no updated_at; insert-only) |

**Primary key:** `id`

**Foreign keys:** `external_approval_request_id` → `external_approval_requests.id`; `pdf_template_id` → `pdf_templates.id`

**Indexes:** `external_approval_files_display_order_index` on `display_order`; FK-backing indexes on `external_approval_request_id`, `pdf_template_id`.

**Note:** No `updated_at` column — `const UPDATED_AT = null`.

## Casts

- `display_order` → `integer`
- `require_view` → `boolean`
- `require_individual_approval` → `boolean`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable
**Hidden:** _None._
**Visible:** _None._
**Appends:** _None._
**Defaults (`$attributes`):** _None._

## Accessors & Mutators

_None._

## Traits

- [InteractsWithMedia](../../../system/traits/index.md#interactswithmedia) — Spatie MediaLibrary core; registers a single-file `external_approval_files` media collection; the model implements `HasMedia`

## Relationships

- `externalApprovalRequest()` — belongs to [ExternalApprovalRequest](./external-approval-request.md) (`external_approval_request_id`): the parent approval request this file belongs to
- `pdfTemplate()` — belongs to [PdfTemplate](../../common/models/pdf-template.md) (`pdf_template_id`): the PDF template used to generate this file (null for direct uploads)
- `actions()` — morphMany [ExternalApprovalAction](./external-approval-action.md) (`actionable`): per-file actions (views, approvals, rejections) on this file

## Scopes

- `ordered(Builder $query)` — orders by `display_order` ascending

## Events

_None defined on the model._

## Observers

_None registered._

## Key Methods

- `registerMediaCollections(): void` — registers the `external_approval_files` Spatie media collection (single file)
- `hasBeenViewedBy(ExternalApprovalApprover $approver): bool` — checks if the given approver has a `viewed` action for this file
- `hasBeenApprovedBy(ExternalApprovalApprover $approver): bool` — checks if the given approver has an `approved` action for this file
- `hasBeenRejectedBy(ExternalApprovalApprover $approver): bool` — checks if the given approver has a `rejected` action for this file
- `getApprovalStatusForApprover(ExternalApprovalApprover $approver): ?string` — returns `'approved'`, `'rejected'`, or `null` for the given approver's current response to this file
- `getViewCount(): int` — count of unique approvers who have viewed this file
- `getApprovalCount(): int` — count of unique approvers who have approved this file
- `getRejectionCount(): int` — count of unique approvers who have rejected this file
- `requiresView(): bool` — returns `true` if `require_view` is set
- `requiresApproval(): bool` — returns `true` if `require_individual_approval` is set
- `getFileName(): string` — file name from the attached Spatie media (returns `'Unknown'` if no media)
- `getFileUrl(): string` — direct URL to the attached media (returns `''` if no media)
- `getPublicFileUrl(string $token): string` — external-portal URL for viewing this file given an approver token (route `external-approvals.view-file`)
- `getFileSize(): int` — file size in bytes from attached media (returns `0` if no media)
- `getFileMimeType(): string` — MIME type from attached media (returns `'application/octet-stream'` if no media)

## Common Usage

```php
// Files are created when building an external approval request:
$file = ExternalApprovalFile::create([
    'external_approval_request_id' => $request->id,
    'file_source'                  => 'upload',
    'require_view'                 => true,
    'require_individual_approval'  => false,
    'display_order'                => 1,
    'message'                      => 'Please review the attached contract.',
]);

// Attach the actual file via Spatie:
$file->addMedia($uploadedFile)
     ->toMediaCollection('external_approval_files');

// Retrieve ordered files for a request:
$files = $request->files()->ordered()->get();

// Check per-approver state:
if ($file->hasBeenViewedBy($approver)) {
    echo 'Approver has seen this file.';
}
$status = $file->getApprovalStatusForApprover($approver); // 'approved', 'rejected', or null

// Progress counts:
echo $file->getViewCount();      // 3
echo $file->getApprovalCount();  // 2
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
