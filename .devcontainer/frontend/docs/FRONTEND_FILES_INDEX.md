# Frontend files index and quick-purpose map

This index provides a quick map of the frontend source tree (high-level groups) and guidance for where to complete documentation.

How this file was generated
- Header templates were added to all `.ts` / `.tsx` files under `frontend/src` using `scripts/add_frontend_headers.py`.
- The script created backups (`*.bak`) of modified files and wrote the modified file list to `frontend/docs/FRONTEND_DOCS_TODO.md`.

Goal
- Provide a one-stop place for a human reviewer to see the high-level structure and pick files to document.

High-level groups (what to document first)
- `src/pages/` — page-level React components. Document route path(s), required props, and any data fetching behavior.
- `src/components/` — reusable UI components. Document props, visual variants, and accessibility notes.
- `src/layout/` — app layout, headers, sidebars. Document global contexts they depend on.
- `src/context/` — React contexts (theme, sidebar). Document provider usage and values in the context shape.
- `src/hooks/` — custom hooks. Document inputs, outputs, and side-effects.
- `src/services/` & `src/api/` — API clients and stubs. Document endpoints, request/response shapes, and error handling.
- `src/mocks/` — MSW handlers used for dev & tests. Document which endpoints are mocked and how to toggle mocking.
- `src/utils/` — formatters & helpers. Document pure functions and expected input ranges.
- `src/icons/` — SVG icons and index. Document naming convention and how to import icons.

Files list and next steps
- The detailed list of files the header-template script updated is in `frontend/docs/FRONTEND_DOCS_TODO.md`.
- Recommended next tasks (pick from the list):
  1. Fill headers for all `src/services/*` files (api contract, params, return types).
  2. Fill headers for `src/pages/sims/*` pages (these are product-critical for simulation flows).
  3. Add example usage to `src/components/JobForm.tsx`, `JobList.tsx`, and `ResultsViewer.tsx`.

Automation offers
- I can populate the header templates with inferred types for service files by reading TypeScript types in `src/types.ts` and using simple heuristics (safe, non-destructive). Ask and I'll run that pass.

Where the per-file TODO is
- `frontend/docs/FRONTEND_DOCS_TODO.md` — contains a machine-generated list of modified files. Use this as the sprint backlog for documentation work.

If you want me to continue
- I can (A) perform the first safe repo structural move (move a low-risk module into `backend/legacy/` and leave a shim), or (B) auto-fill header content for `src/services/*` and `src/api/*` files, or (C) prepare a PR-ready commit series with linter checks. Tell me which.
