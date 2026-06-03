# Project documentation

This folder explains how the codebase works in plain language, so future you (or
another engineer) can quickly remember the architecture and safely change it.

## Recommended reading order

1. **`backend.md`** — start here. High-level FastAPI backend architecture,
   request lifecycle, worker setup, local run notes.
2. **`indexing-pipeline.md`** — the most important system flow: GitHub repo URL
   → clone → filter files → Tree-sitter parse → `code_chunks` +
   `code_connections`.
3. **`database.md`** — schema reference for users, repositories, worker tasks,
   webhooks, conversations, chunks, connections, and lookup tables.
4. **`webhooks.md`** — Clerk/Svix webhook ingestion and local user creation.
5. **`frontend.md`** — React + Vite + Clerk frontend, API client, and next UI
   endpoints to build against.
6. **`comment_director.md`** — guidance for adding useful comments/docstrings.

## One-sentence project summary

The app lets authenticated users submit GitHub repositories, then background
workers clone and parse those repos into a PostgreSQL-backed code graph made of
semantic chunks and import/call connections.

## Key flows

- **User creation**: Clerk → `/webhooks/clerk` → `users` table.
- **Repo submission**: frontend → `POST /api/repos` → `repositories` row →
  ARQ job.
- **Indexing**: `clone_repo_task` → `parse_repo_task` → `code_chunks` +
  `code_connections`.
- **Progress**: frontend polls `GET /api/tasks/{task_id}` and
  `GET /api/repos/{repo_id}`.

## Main source folders

- `app/` — Python backend.
- `app/ARQ/` — Redis/ARQ worker tasks.
- `app/services/` — business logic for GitHub, cloning, parsing, graph building,
  persistence, and webhooks.
- `app/models/` — database models and session setup.
- `clerk-react/` — React frontend.
