# Architecture Decisions & Memory (work-in-progress)

This document records key architectural choices, rationale, and current work-in-progress notes. It is a living document and intentionally marked **UNDER ACTIVE DEVELOPMENT**.

## High-level goals
- Two-founder startup: clean separation between AI/ML and backend/orchestration responsibilities.
- Monorepo structure to support fast iteration and shared types/contracts.

## Decisions (initial)

1) Monorepo layout
   - Keep language-specific code near its toolchain: Python code in `src/` and `backend/` for services; TypeScript frontend in `frontend/`.
   - Shared documentation and contracts in `docs/` to minimize drift.

2) API contract policy
   - Maintain a canonical `docs/api_contract.md` describing unstable contracts.
   - Use versioned endpoints when a contract stabilizes.

3) LLM integration
   - Use an adapter pattern (backend/ai) to allow swapping providers and rotating keys.
   - Keep model orchestration separate from domain logic — adapter provides a small, stable interface.

4) Data persistence and memory bank
   - `backend/db/` holds metadata, summaries, and persistent 'memory bank' artifacts used by AI assistants.
   - Summaries and architectural memory are explicitly stored and curated; they are not authoritative but aid development.

## Current WIP notes (memory bank)
- Using lightweight JSON stores for prototypes (e.g., `backend/db/summaries.json`).
- Consider migrating to SQLite or Redis for concurrency as the team grows.

## Open questions
- CI/CD guardrails: how strict should the pre-merge checks be for experimental branches?
- Model provider strategy: rotating keys vs. paid plan tradeoffs.

---
Status: UNDER ACTIVE DEVELOPMENT
