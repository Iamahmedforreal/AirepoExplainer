# Backend (`app/`) — overview

## What this project is

A **codebase intelligence platform**. A signed-in user submits a public GitHub
repository URL; the backend clones it, parses every source file into a structured
map of *symbols* (modules, classes, functions/methods) and the *connections*
between them (imports and calls), and stores that map in PostgreSQL. The schema
also has `conversations` / `messages` tables so a user can later chat about an
indexed repo (the chat endpoint itself is not implemented yet).

The heavy work (clone + parse) runs **out of the request/response cycle** in
background workers, so the API responds instantly and the frontend polls for
progress.

## The big picture

```
React frontend (Clerk auth)
        │  POST /api/repos   (Bearer JWT + GitHub URL)
        ▼
FastAPI router (app/router/urlRoute.py)
        │  - authenticates the user (Clerk)
        │  - saves a Repository row  (status = PENDING)
        │  - enqueues a job on Redis
        ▼
Redis  ◀────────────────────────────────┐
        │ ARQ worker picks up the job    │ enqueues next stage
        ▼                                │
clone_repo_task  ──────────────────────┘
        │  shallow git clone + file filtering   (status = INDEXING)
        ▼
parse_repo_task
        │  Tree-sitter AST → code_chunks + code_connections  (status = INDEXED)
        ▼
PostgreSQL  ◀── frontend polls GET /api/tasks/{id} and GET /api/repos/{id}
```

Separately, **Clerk webhooks** hit `/webhooks/clerk` to create user rows when
people sign up (see `webhooks.md`).

## Tech stack

| Concern            | Tool                                             |
| ------------------ | ------------------------------------------------ |
| Web framework      | FastAPI + Uvicorn                                |
| Background jobs    | ARQ (async Redis task queue)                     |
| Database           | PostgreSQL via SQLAlchemy 2.0 async + asyncpg    |
| Migrations         | Alembic                                          |
| Auth               | Clerk (`clerk-backend-api`) — JWT bearer tokens  |
| Webhook signatures | Svix                                             |
| Code parsing       | Tree-sitter (Python, JavaScript, TypeScript, TSX)|
| Git                | GitPython (shallow clone)                        |
| Config             | pydantic-settings (`.env`)                       |

## Directory map

```
app/
├── app.py                  FastAPI entry: lifespan, CORS, middleware, routers
├── config/app_config.py    Settings loaded from .env (DB URL, API keys, paths)
├── router/
│   ├── urlRoute.py         /api/repos + /api/tasks  (submit & poll)
│   └── webhookRouter.py    /webhooks/clerk          (user lifecycle)
├── schema/urlSchema.py     Request validation (GitHub-URL-only Pydantic model)
├── utils/utils.py          Clerk auth helper -> user_id
├── ARQ/
│   ├── task.py             clone_repo_task, parse_repo_task (the pipeline)
│   └── worker.py           ARQ WorkerSettings (registers tasks, Redis, limits)
├── services/
│   ├── urlService.py       GitHub API + file-tree filtering rules
│   ├── clone_service.py    git clone + read accepted files
│   ├── repo_metadata.py    read/update Repository row + status transitions
│   ├── tree_sitter_parser.py  grammar loading + parse to AST
│   ├── ast_extractor.py    walk the AST -> symbols, imports, call sites
│   ├── connection_builder.py  resolve imports/calls -> connection records
│   ├── code_store.py       build + persist code_chunks & code_connections
│   └── webhook.py          webhook persistence + user creation helpers
└── models/
    ├── repo_models.py      all tables, enums, lookup-table seeding
    └── db.py               async engine + session factory
```

## Request lifecycle: submitting a repo

Endpoint: `POST /api/repos` (`app/router/urlRoute.py`)

1. **Authenticate** — `authenticate_and_get_user_id(request)` validates the Clerk
   JWT and returns `user_id`. Unauthenticated requests get `401`.
2. **Validate URL** — `TrustedGitHubRepoLink` rejects anything whose host is not
   `github.com`.
3. **Dedupe** — `check_existing_repo(user_id, url)`:
   - already `INDEXED` → return it immediately, nothing re-runs.
   - exists but not indexed → refresh GitHub metadata, reset pipeline fields,
     set status back to `PENDING`.
   - brand new → `save_repo(...)` creates the row at status `PENDING`.
4. **Enqueue** — `redis.enqueue_job("clone_repo_task", repo_id=...)`.
5. **Respond** instantly with `{ status: "queued", repoId, jobId, repo }`.

The actual cloning/parsing then happens in the worker. See
`indexing-pipeline.md` for the full two-stage worker flow and how status moves
`PENDING → INDEXING → INDEXED` (or `FAILED`).

## Polling endpoints

- `GET /api/repos/{repo_id}` — repository metadata + index stats
  (`sourceFileCount`, `chunkCount`, `connectionCount`, `indexedAt`, `status`).
  Scoped to the authenticated user.
- `GET /api/tasks/{task_id}` — maps the task's internal status to a friendly
  `phase`: `pending → cloning → parsing → indexed` (or `retrying` / `failed`),
  plus timing, attempt count, and the error type/message if it failed.

## App startup (`app/app.py`)

On startup the `lifespan` context:
- creates all tables (`create_db_and_tables`) and **seeds the lookup tables**
  (see `database.md`), and
- opens a shared Redis pool stored on `app.state.redis` (used by the router to
  enqueue jobs).

There is also CORS (allowing the Vite dev server on `:5173` and `:3000`) and an
HTTP middleware that times every request and logs a warning for anything slower
than 500 ms.

## Running locally

1. **Env** — create `.env` with at least:
   `DATABASE_URL`, `GITHUB_API_KEY`, `CLERK_WEBHOOK_SECRET`, `JWT_PUBLIK_KEY`,
   `CLEERK_SCERET_KEY` (note: the env var name for the Clerk secret key is
   spelled `CLEERK_SCERET_KEY`; `clone_base_dir` defaults to
   `cloned_repos/` under the project root).
2. **Dependencies** — managed in `pyproject.toml` (Python ≥ 3.12). Install with
   `uv sync` (or `pip install -e .`).
3. **Infra** — a PostgreSQL database and a Redis server must be reachable
   (worker + app both expect Redis at `localhost:6379`).
4. **Migrations** — `alembic upgrade head`.
5. **Run the API** — `uvicorn app.app:app --reload`.
6. **Run the worker** (separate process, required for indexing to happen) —
   `arq app.ARQ.worker.WorkerSettings`.

> Without the ARQ worker running, repos stay stuck at `PENDING`/`INDEXING`
> because nothing consumes the queue.

## Where to read next

- `indexing-pipeline.md` — the clone → parse → chunk → connection flow in detail.
- `database.md` — every table, enum, and the star-schema lookup pattern.
- `webhooks.md` — Clerk webhook ingestion.
- `frontend.md` — the React client.
