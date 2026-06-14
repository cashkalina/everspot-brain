---
model: EmailTemplate
module: Common
table: email_templates
connection: tenant
primary_source: modules/Common/Models/EmailTemplate.php
source_paths:
  - app/Models/BaseModel.php
traits:
  - SoftDeletes
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, integration]
---

# EmailTemplate

## Overview

The EmailTemplate model stores customizable email templates used by the Everspot notification and email system. Templates are typed via the `EmailTemplateType` enum — either `NOTIFICATION` (mapped to a notification class) or `MODEL_EMAIL` (mapped to a model class for direct model-triggered emails).

Each template carries a name, subject, optional to/cc/bcc overrides (as text), HTML content, optional attachment metadata, and flags for active status (`is_active`) and advanced mode (`is_advanced`). Active templates matching a notification or model class are resolved at send time. Soft deletes allow templates to be deactivated without loss.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| type | varchar | No | notification | Template type (`notification` or `model_email`) |
| class | varchar | No | - | Notification or model class this template applies to |
| name | varchar | No | - | Template name |
| subject | varchar | No | - | Email subject line |
| to | text | Yes | - | Override recipient(s) |
| cc | text | Yes | - | Override CC recipient(s) |
| bcc | text | Yes | - | Override BCC recipient(s) |
| content | text | No | - | HTML email body |
| attachment_data | json | Yes | - | Attachment configuration |
| is_active | tinyint | No | 1 | Whether the template is active |
| is_advanced | tinyint | No | 0 | Whether advanced editing mode is enabled |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |
| deleted_at | timestamp | Yes | - | Soft-delete timestamp (via [SoftDeletes](../../../system/traits/index.md#softdeletes) — see trait doc) |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

- `is_active` → `boolean`
- `is_advanced` → `boolean`
- `type` → `EmailTemplateType::class` (enum)
- `attachment_data` → `array`

<!-- trait-contributed casts are documented in the respective trait docs, not here -->

## Attributes

**Guarded:** `[]` — all fields are mass-assignable

## Accessors & Mutators

_None._

## Traits

- [SoftDeletes](../../../system/traits/index.md#softdeletes) — templates are soft-deleted, never hard-deleted

## Relationships

_None._

## Scopes

- `active($query): Builder` — filters to `is_active = true`
- `forNotificationClass($query, $notificationClass): Builder` — active templates of type `NOTIFICATION` matching the given class
- `forModelClass($query, string $modelClass): Builder` — active templates of type `MODEL_EMAIL` matching the given class

## Events

_None._

## Observers

_None registered._

## Key Methods

- `isAdvanced(): bool` — returns `true` when `is_advanced` is set
- `hasAttachments(): bool` — returns `true` when `attachment_data` is non-empty

## Common Usage

```php
// Find the template for a specific notification class
$template = EmailTemplate::forNotificationClass(OrderConfirmationNotification::class)->first();

// Find templates for a specific model class
$templates = EmailTemplate::forModelClass(Order::class)->get();

// Check if a template uses advanced editing
if ($template->isAdvanced()) {
    // render with advanced editor
}
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
