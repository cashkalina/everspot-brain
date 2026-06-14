---
title: ExternalSite Module
purpose: Overview of the ExternalSite module and its documentation
last_updated: 2026-06-14
---

# ExternalSite Module

The ExternalSite module manages configured external-facing website integrations — for example, public memorial portals or obituary sites — that cemeteries set up through Everspot. Each site has a type, a human-readable name, a unique URL slug, a public-visibility flag, and arbitrary JSON configuration data resolved by a type-specific `SiteConfig` strategy.

## Models

- [ExternalSite](./models/external-site.md) — a single configured external site integration, route-bound by its `slug`.

## Module-owned traits

_None._

## Related modules

_None._ ExternalSite is a standalone configuration module with no direct Eloquent relationships to other domain modules.
