Frontend (clerk-react/) — simple overview

Purpose
- Lightweight React + Vite frontend used to submit repos and show indexing progress.

Key files
- `clerk-react/src/main.tsx` — app entry, mounts React tree.
- `clerk-react/src/App.tsx` — top-level component and routes.
- `clerk-react/src/libs/api.ts` — helper functions for calling backend APIs.
- `clerk-react/index.html` and `vite.config.ts` — build and dev server config.

What to change when updating UI
- Update components under `src/`.
- Use `npm run dev` (or `yarn`) to run locally.
- API base URL should point to the backend host (development: `http://localhost:8000`).

Simple developer steps
1. Install: `npm install` inside `clerk-react/`.
2. Start dev server: `npm run dev`.
3. Build for production: `npm run build`.
