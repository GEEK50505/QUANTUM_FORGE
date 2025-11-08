# Frontend Developer Guide

Purpose
-------
This document explains the frontend layout, how to run the app locally, lists the important folders and files, and provides a per-file documentation checklist so we can rapidly add inline docs for every frontend file.

Run & dev workflow
------------------
- Install dependencies (project root `frontend`):
  - npm install (or `pnpm install` / `yarn` depending on your preference and repo policy).
- Start dev server:
  - `npm run dev` (via Vite)
- Build for production:
  - `npm run build`
- Run tests:
  - `npm test` or `npm run test` (check script configured in `package.json`)

Top-level files (summary)
- `index.html` — app bootstrap page.
- `package.json` — scripts and dependency manifest.
- `vite.config.ts` — Vite dev server & build config.
- `tailwind.config.js` & `postcss.config.js` — styling pipeline.

src/ layout and responsibilities
--------------------------------
- `src/main.tsx` — main entry, mounts React app and providers.
- `src/App.tsx` — top-level routing and page layout wiring.
- `src/index.css` — global styles and Tailwind entry.

Key directories
- `components/` — small, reusable UI components (buttons, form controls, etc.).
- `layout/` — layout components shared across pages (headers, footers, sidebars).
- `pages/` — page-level components rendered by the router (one component per route).
- `context/` — React contexts (ThemeContext, SidebarContext) used app-wide.
- `hooks/` — custom hooks (e.g., `useMockApi`, `useGoBack`). Keep them pure and small.
- `services/` & `api/` — API client wrappers and stubs (e.g., `client.ts`, `qpuStub.ts`). Keep HTTP logic here.
- `utils/` — formatting helpers, constants, and error handling.
- `mocks/` — MSW handlers and mock server for local dev/testing.
- `icons/` — svg icons and `index.ts` to import them as React-friendly components.

Per-folder documentation checklist (apply to every folder/file)
- For each component file (.tsx/.ts) add a short header block near the top with:
  - One-line purpose.
  - Inputs (props) shape (brief with types) and default values.
  - Outputs/effects (events emitted, context mutations, side effects).
  - Example usage snippet (1-2 lines) if the component is reused.
- For hooks: document inputs, return shape, and whether the hook is stateful or pure.
- For services: document exported functions and expected parameter shapes and error modes.
- For pages: document the route path(s) that map to the page and any required route params.

Example file header (TSX / TS)
```ts
// Purpose: Small one-line description
// Props: { items: Item[], onSelect?: (item: Item) => void }
// Returns: JSX.Element
// Notes: Pure / no side-effects except calling onSelect
```

Suggested initial documentation tasks (low-effort, high value)
1. Add header blocks to all files in `src/pages/` (one-liners + route info).
2. Add headers to `src/services/*` describing network calls and mock behavior.
3. Add headers to `src/hooks/*` with input/outputs.
4. Populate `src/components/` README.md with component conventions (naming, props-first, presentational vs container components).

Testing and mocks
-----------------
- `src/mocks/` contains MSW handlers. Document which endpoints are mocked and how to toggle mocks on/off in dev.
- Keep API client logic centralized in `src/api/client.ts` so changing endpoints requires minimal changes.

Coding conventions and style
--------------------------
- Files: TypeScript + React + Tailwind.
- Types: prefer explicit interfaces for public props and return types on exported functions.
- Styling: Tailwind utility classes in component markup. For complex or repeated patterns, create small reusable style classes in `index.css`.

Documentation roll-up tasks
- Create `frontend/docs` files for: architecture overview, component conventions, testing & mocks, and contribution guidelines.
- Add a `FRONTEND_DOCS_TODO.md` that lists all files that lack headers so contributors can pick tasks.

How I can help next
- I can run an automated pass that inserts the header template into every `.ts`/`.tsx` file in `frontend/src` as a starting point (no content auto-filled beyond types where available). Approve and I'll execute a non-destructive commit that adds these templates and a `frontend/docs/FRONTEND_DOCS_TODO.md` listing files to be filled in with real prose.
