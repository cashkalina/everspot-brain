---
title: Documentation Module
module: Documentation
last_updated: 2026-06-14
---

# Documentation Module

The Documentation module provides Everspot's built-in knowledge base — a set of help articles organized into categories that staff can browse directly within the application. Content is authored and managed by Everspot administrators and is shared globally across all cemetery tenants via the **central** database connection.

## Contents

- [Models](./models/index.md)
  - [DocCategory](./models/doc-category.md) — grouping container for articles
  - [DocArticle](./models/doc-article.md) — individual help article

## Key Concepts

- Both models live on the **central** connection (not tenant-specific).
- Both use `slug` as the route key for human-readable URLs.
- `DocArticle.published_at` controls visibility: `null` = draft; a past or present datetime = published.
- `DocCategory.publishedArticles()` is the primary consumer-facing relationship — pre-filtered and ordered.
- Both models support soft deletes.
