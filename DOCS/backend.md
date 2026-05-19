Backend (app/) — simple overview

Purpose
- Accepts repository URLs from the frontend and runs an indexing pipeline that:
  1. fetches repo metadata from GitHub
  2. optionally shallow-clones the repo to disk
  3. filters and chunks source files
  4. embeds chunks and stores vectors (not all steps implemented in this repo)

Key directories and files
- `app/app.py` — FastAPI application entry (registers routers and middleware).
- `app/router/urlRoute.py` — endpoints for submitting repos and polling task state.
- `app/router/webhookRouter.py` — webhook ingestion endpoints (see webhooks.md).
- `app/services/` — business logic split into small modules:
  - `urlService.py`: GitHub API calls, repo metadata mapping, repository tree cleaning, file reading.
  - `clone_service.py`: performs local git clone operations.
  - `webhook.py`: webhook handling helpers.
- `app/models/` — DB models and enums (`repo_models.py`) and DB engine config (`db.py`).
- `app/ARQ/` — background worker tasks (`task.py`) and worker settings.

How the main flow works (high level)
1. Frontend POSTs repo URL to `/api/repos`.
2. Router enqueues `index_repo` background job via ARQ (Redis job queue).
3. Worker runs `index_repo` which:
   - extracts repo info using GitHub API (`urlService.extract_repo_info`)
   - saves Repository row (`urlService.save_repo`)
   - performs a shallow clone (`clone_service.clone_repo`)
   - updates WorkerTask and Repository statuses in the DB

Simple run notes
- Environment: configure `CLERK_WEBHOOK_SECRET` and `GITHUB_API_KEY` in `.env` or app config.
- DB migrations managed via Alembic (see `alembic/`).
- Tests live under `test/` and use `pytest`.
