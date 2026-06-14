---
title: Common Module — Models Index
last_updated: 2026-06-14
---

# Common Module — Models

The Common module provides foundational models used system-wide across Everspot. These models cover addresses, reference data, dashboards, integrations, file management, notes, settings, users, tenancy, and more.

## Models (31)

| Model | Table | Connection | Description |
|-------|-------|-----------|-------------|
| [Address](./address.md) | `addresses` | tenant | Polymorphic address records attached to any addressable entity |
| [Cemetery](./cemetery.md) | `cemeteries` | tenant | Physical cemetery location; foundational org unit in the system |
| [Country](./country.md) | `countries` | tenant | ISO country reference data (pre-seeded) |
| [Dashboard](./dashboard.md) | `dashboards` | tenant | Configurable dashboard pages assignable to users |
| [DashboardElement](./dashboard-element.md) | `dashboard_elements` | tenant | Individual widget component within a dashboard |
| [DeliveryPreference](./delivery-preference.md) | `delivery_preferences` | tenant | Lookup table for delivery preference options |
| [Domain](./domain.md) | `domains` | **central** | Tenant domain/subdomain routing records (Stancl Tenancy) |
| [EmailLog](./email-log.md) | `email_logs` | tenant | Audit log of all outgoing emails sent by the system |
| [EmailTemplate](./email-template.md) | `email_templates` | tenant | Customizable email templates for notifications and model emails |
| [Entity](./entity.md) | `entities` | tenant | External companies/individuals (manufacturers, installers, dealers) |
| [EntityTypePivot](./entity-type-pivot.md) | `entity_types` | tenant | Per-entity type assignments (MANUFACTURER, INSTALLER, DEALER) |
| [ExternalId](./external-id.md) | `external_ids` | tenant | Polymorphic store mapping Everspot records to external system IDs |
| [Integration](./integration.md) | `integrations` | tenant | External system integrations (QuickBooks, Stripe, etc.) |
| [ListOption](./list-option.md) | `list_options` | tenant | System-wide controlled vocabulary (titles, types, branches, etc.) |
| [ListOptionType](./list-option-type.md) | `list_option_types` | tenant | Dynamic type definitions for list option categories |
| [Media](./media.md) | `media` | tenant | Extended Spatie MediaLibrary media records with tags and external IDs |
| [Metadata](./metadata.md) | `metadata` | tenant | Polymorphic contextual annotations (e.g. report last-run tracking) |
| [ModelNumberConfiguration](./model-number-configuration.md) | `model_number_configurations` | tenant | Per-model-class number generation configuration |
| [Note](./note.md) | `notes` | tenant | Free-text notes attached to any notable entity; supports alert mode |
| [OwnerFile](./owner-file.md) | `owner_files` | tenant | Central record linking customers to owned properties |
| [OwnerFileLine](./owner-file-line.md) | `owner_file_lines` | tenant | Individual property line item within an owner file |
| [PdfTemplate](./pdf-template.md) | `pdf_templates` | tenant | Configurable PDF template definitions for printable documents |
| [Setting](./setting.md) | `settings` | tenant | Polymorphic key-value settings for any entity (cemetery, user, tenant) |
| [Share](./share.md) | `shares` | tenant | Permission-level sharing grants for shareable models |
| [State](./state.md) | `states` | tenant | State/province reference data keyed to countries (pre-seeded) |
| [Syncable](./syncable.md) | `syncables` | tenant | Per-record sync state between Everspot records and external systems |
| [Tenant](./tenant.md) | `tenants` | **central** | Cemetery organization (client) in the multi-tenant platform |
| [TenantIntegration](./tenant-integration.md) | `tenant_integrations` | **central** | Central cross-tenant integration audit table |
| [TenantUser](./tenant-user.md) | `tenant_users` | **central** | Central mapping of users to tenants |
| [Token](./token.md) | `tokens` | tenant | Polymorphic OAuth/API token storage for integrations |
| [User](./user.md) | `users` | tenant | Tenant-side authenticated user (staff/employee) |
