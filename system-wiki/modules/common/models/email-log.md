---
model: EmailLog
module: Common
table: email_logs
connection: tenant
primary_source: modules/Common/Models/EmailLog.php
source_paths: []
traits: []
related_models: []
built_at: 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0
last_updated: 2026-06-14
completeness: complete
deprecated: false
tags: [admin, integration]
---

# EmailLog

## Overview

The EmailLog model records every outgoing email sent from the system, providing an audit trail and a debugging surface for email delivery issues. It stores the full message envelope — to, cc, bcc, from, reply-to, subject, body, and any attachments — along with delivery status, timestamp, and error information.

Unlike most Common models, `EmailLog` extends Laravel's base `Illuminate\Database\Eloquent\Model` directly (not `BaseModel`), so it does not participate in activity logging or other BaseModel-contributed behavior. It has no relationships, traits, or observers. The model's primary purpose is append-only logging; queries are performed through the provided scopes.

## Schema

<!-- rendered from schema/tenant.json (snapshot_commit 86b4328c28e8f0f8b1f0a0a84210b51ba08816d0); validated before commit -->

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | bigint | No | - | Primary key |
| to | json | No | - | Recipient email address(es) as array |
| cc | json | Yes | - | CC email address(es) as array |
| bcc | json | Yes | - | BCC email address(es) as array |
| from | varchar | No | - | Sender email address |
| reply_to | varchar | Yes | - | Reply-to email address |
| subject | varchar | No | - | Email subject line |
| body | longtext | Yes | - | Email body (HTML) |
| attachments | json | Yes | - | Attachment metadata as array |
| status | varchar | No | sent | Delivery status (`sent`, `failed`, etc.) |
| sent_at | timestamp | Yes | - | Timestamp when the email was sent |
| error_message | text | Yes | - | Error details if delivery failed |
| metadata | json | Yes | - | Additional metadata |
| created_at | timestamp | Yes | - | Creation timestamp |
| updated_at | timestamp | Yes | - | Last update timestamp |

**Primary key:** `id`

**Foreign keys:** None

**Indexes:** None beyond primary key.

## Casts

- `to` → `array`
- `cc` → `array`
- `bcc` → `array`
- `attachments` → `array`
- `metadata` → `array`
- `sent_at` → `TimezonedDateTime::class` (timezone-aware datetime; see `modules/Common/Support/Timezone/Casts/TimezonedDateTime.php`)

## Attributes

**Fillable:** `['to', 'cc', 'bcc', 'from', 'reply_to', 'subject', 'body', 'attachments', 'status', 'sent_at', 'error_message', 'metadata']`

## Accessors & Mutators

- `getToStringAttribute(): string` — recipient addresses joined as comma-separated string
- `getCcStringAttribute(): string` — CC addresses joined as comma-separated string
- `getBccStringAttribute(): string` — BCC addresses joined as comma-separated string

## Traits

_None._

## Relationships

_None._

## Scopes

- `recent(Builder $query): Builder` — orders by `sent_at` descending
- `olderThan(Builder $query, int $days): Builder` — filters to records where `sent_at < now() - $days days`
- `byStatus(Builder $query, string $status): Builder` — filters by `status`
- `search(Builder $query, string $term): Builder` — searches `subject`, `from`, and JSON `to` field by `$term` (LIKE)

## Events

_None._

## Observers

_None registered._

## Key Methods

_None beyond scopes and accessors._

## Common Usage

```php
// Log a sent email
EmailLog::create([
    'to'      => ['recipient@example.com'],
    'from'    => 'noreply@cemetery.com',
    'subject' => 'Your order confirmation',
    'body'    => $htmlBody,
    'status'  => 'sent',
    'sent_at' => now(),
]);

// Retrieve recent emails
$recent = EmailLog::recent()->limit(50)->get();

// Search for emails with a subject keyword
$results = EmailLog::search('order confirmation')->get();

// Find failed deliveries
$failures = EmailLog::byStatus('failed')->get();

// Clean up old logs
EmailLog::olderThan(90)->delete();
```

<!-- human:begin -->
## Business Logic Notes

<!-- human:end -->
