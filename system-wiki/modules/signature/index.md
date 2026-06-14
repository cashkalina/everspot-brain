---
title: Signature Module
module: Signature
last_updated: 2026-06-14
---

# Signature Module

The Signature module provides electronic-signature workflow infrastructure for Everspot. It enables documents to be generated from templates, bundled into envelopes, delivered to signers for review and signing, and tracked with a full forensic audit trail.

## Sections

- [Models](./models/index.md) — 5 Eloquent models documenting the full e-signature domain

## Overview

The module is organized around a core signing workflow:

1. **[DocumentTemplate](./models/document-template.md)** — staff create reusable templates containing document markup and configuration (signing zone placement, field definitions, rendering options).
2. **[DocumentEnvelope](./models/document-envelope.md)** — a signing event is initiated by creating an envelope, which bundles one or more documents and tracks overall status.
3. **[Document](./models/document.md)** — each document inside an envelope is generated from a template and stores both unsigned and signed storage paths.
4. **[Signer](./models/signer.md)** — the individuals required to sign are listed on the envelope; each signer may optionally be linked to an Everspot [Customer](../customer/models/customer.md).
5. **[SignatureRequest](./models/signature-request.md)** — a request is sent to each user-account signer, driving delivery (email/SMS), tracking views and signatures, and capturing forensic signing metadata (device, OS, browser, IP).

## Source location

`modules/Signature/` in the Everspot repository.
