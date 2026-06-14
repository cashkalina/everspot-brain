---
title: Documentation Models
module: Documentation
last_updated: 2026-06-14
---

# Documentation Models

Models in the Documentation module manage Everspot's built-in knowledge base articles and categories. Both models use the **central** database connection — documentation content is platform-wide, shared across all cemetery tenants.

| Model | Table | Connection | Description |
|-------|-------|------------|-------------|
| [DocArticle](./doc-article.md) | `doc_articles` | central | A single help or documentation article |
| [DocCategory](./doc-category.md) | `doc_categories` | central | A grouping category for documentation articles |
