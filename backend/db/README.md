# Backend DB / Memory Bank (backend/db/) — UNDER ACTIVE DEVELOPMENT

Purpose:
- Store metadata about simulation jobs, small summaries used by AI assistants, and a curated "memory bank" of architecture decisions.

Recommended files & conventions:
- `backend/db/summaries.json` — lightweight curated summaries for large files or modules (keep small)
- `backend/db/migrations/` — database migrations (if using SQLite/Postgres)
- `backend/db/README.md` — this file

Memory bank guidance:
- Keep entries short (1-3 paragraph), dated, and linked to the source code path.
- This memory is *developer-facing* (not authoritative) and supports AI assistants in giving context-aware suggestions.

Persistence options (incremental):
1. Start with small JSON files for rapid iteration.
2. If concurrency becomes a need, migrate to SQLite or Redis with an adapter layer.

Status: UNDER ACTIVE DEVELOPMENT
