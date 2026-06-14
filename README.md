# Everspot Brain

AI-maintained knowledge for **Everspot**, a Laravel-based cemetery management system. This repository is the container; the work lives in `system-wiki/`.

## Layout

- **`system-wiki/`** — the Everspot System Wiki: an AI-optimized, searchable documentation repository for Everspot's data model, maintained by Claude Code. Start at [`system-wiki/CLAUDE.md`](system-wiki/CLAUDE.md) (operating instructions) and [`system-wiki/meta/foundation.md`](system-wiki/meta/foundation.md) (authoritative spec).
- **`temp/`** — scratch space; not part of the wiki.

## Related repository

The **Everspot** codebase that the wiki documents is a **separate** git repository (not nested here). Its location is configured in `system-wiki/wiki.config.json` (machine-local). The wiki only ever reads Everspot source via git; it never modifies it.
