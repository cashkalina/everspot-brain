---
title: Signature Module — Models
module: Signature
last_updated: 2026-06-14
---

# Signature Module: Models

This directory contains documentation for all Eloquent models in the `modules/Signature/` module.

The Signature module provides e-signature workflow infrastructure for Everspot. Documents are generated from templates, grouped into envelopes, and routed to signers via signature requests. All five models use the tenant database connection.

## Model Index

| Model | Table | Description |
|-------|-------|-------------|
| [Document](./document.md) | `documents` | A single document within a signing envelope, generated from a template. |
| [DocumentEnvelope](./document-envelope.md) | `document_envelopes` | The top-level record that groups one or more documents into a single signing event. |
| [DocumentTemplate](./document-template.md) | `document_templates` | Reusable template (content + config) from which documents are generated. |
| [SignatureRequest](./signature-request.md) | `signature_requests` | A signing request sent to a specific user, tracking the full delivery-and-signing lifecycle. |
| [Signer](./signer.md) | `signers` | An individual (optionally linked to a Customer) required to sign an envelope. |

## Relationships at a glance

```
DocumentTemplate
    └── has many → Document

DocumentEnvelope
    ├── belongs to → User (creator)
    ├── has many → Document
    ├── has many → Signer
    └── has many → SignatureRequest

Document
    ├── belongs to → DocumentEnvelope
    └── belongs to → DocumentTemplate

SignatureRequest
    ├── belongs to → DocumentEnvelope
    └── belongs to → User (signer)

Signer
    ├── belongs to → DocumentEnvelope
    └── belongs to (optional) → Customer
```
