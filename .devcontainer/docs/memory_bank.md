```markdown
# Memory Bank — Developer Architectural Notes (docs/memory_bank.md)

Purpose:
- Maintain a short, persistent, human-readable record of architectural decisions, trade-offs, and important TODOs for AI assistants and new contributors.

Guidelines:
- Keep entries short (1-3 paragraphs).
- Date each entry and link to source code paths and PRs when possible.
- Mark status with: UNDER ACTIVE DEVELOPMENT / PROTOTYPE / DEPRECATED.

Example entry:

- 2025-10-31 — Hybrid pipeline location
  - Decision: Consolidate orchestration into `backend/orchestrator/` and keep research demos in `src/hybrid_pipeline/` (duplicate until interface stabilizes).
  - Rationale: Keeps production orchestration separate from exploratory research notebooks.
  - Status: UNDER ACTIVE DEVELOPMENT

- 2025-10-31 — Merge strategy for external frontend template and secondary repo
  - Decision: Perform a conservative, staged merge of the `free-react-tailwind-admin-dashboard-main` repository into this monorepo. The merge will be driven by a safe, repeatable script `scripts/merge_and_cleanup.py` which defaults to a dry-run and produces a `merge_report` describing planned operations.
  - Strategy details:
    1. Dry-run first: run the script with `--source <path>` (no `--apply`) to preview which files will be copied. Review `scripts/merge_reports/merge_report_<origin>_*.json` for the proposed file list.
    2. Preserve frontend templates: the script will copy candidate frontend files (`src`, `public`, `package.json`, `index.html`) into `frontend/template_sources/<origin>/...` instead of overwriting `frontend/` directly. This keeps the original template upstream for later manual integration.
    3. Selective copying: only recommended top-level directories (ai, backend, frontend, docs, notebooks, scripts) and important manifests (package.json, requirements.txt, README*) are copied by default. Large runtime and build directories (`node_modules`, `.git`, `dist`, `build`) are skipped.
    4. Manual review: maintainers should manually inspect `frontend/template_sources/<origin>` and selectively migrate components (feature-by-feature, tests, and styles) into `frontend/` using a feature-branch workflow.
  - Rationale: The template contains useful UI scaffolding, styles, and components the frontend team can re-use. Automatic overwrite risks losing hand-tuned state and creates merge conflicts. A staged approach preserves provenance and makes review manageable for a two-founder team.
  - Status: UNDER ACTIVE DEVELOPMENT

Please update this file whenever you make a cross-cutting design change that impacts other contributors.

```
