# Database schema

All tables, enums, and relationships live in `app/models/repo_models.py`.
The async engine + session factory are in `app/models/db.py`
(SQLAlchemy 2.0 async + asyncpg). Schema changes are versioned with Alembic.

## Entity map

```
users ─┬─< repositories ─┬─< worker_tasks
       │                  ├─< code_chunks ──< code_connections
       │                  ├─< conversations ──< messages
       │                  └─< webhook_events (repoId nullable)
       └─< conversations

(lookup tables: repo_statuses, task_types, task_statuses, message_roles)
```

`<` means one-to-many. A `User` owns repositories and conversations; a
`Repository` owns its worker tasks, code chunks, connections, and conversations.

## The star-schema / lookup-table pattern

Status-like fields are stored as **integer foreign keys into small lookup
tables** rather than as raw enums in each row. There are two halves:

1. **Python enums** (`RepoStatus`, `TaskType`, `TaskStatus`, `MessageRole`) used
   in application code for readability, e.g. `RepoStatus.INDEXED.value`.
2. **Lookup tables** (`repo_statuses`, `task_types`, `task_statuses`,
   `message_roles`) holding `id → name`. These are **seeded automatically** on
   startup by `create_db_and_tables()` using `INSERT ... ON CONFLICT DO NOTHING`,
   so they stay in sync with the enums and seeding is idempotent.

This keeps fact tables compact, lets you join to human-readable names in
reporting, and centralizes the valid values.

## Tables

### `users`
Platform accounts. Created by the Clerk webhook (`webhooks.md`), not by API
signup. PK `id` is the Clerk user id (a string). Has `createdAt`/`updatedAt`.

### `repositories`
A GitHub repo a user submitted for indexing. Two groups of fields:

- **GitHub metadata** (set at submit / refreshed by clone): `githubUrl`,
  `repoOwner`, `repoName`, `defaultBranch`, `language`, `description`,
  `topics` (string array), `isPrivate`.
- **Pipeline metadata** (filled in by the workers): `clonePath`,
  `sourceFileCount`, `chunkCount`, `connectionCount`, `indexedAt`, and
  `statusId` → `repo_statuses`.

Constraints/indexes worth knowing:
- `UNIQUE(userId, githubUrl)` — a user can't submit the same repo twice.
- Indexes on `userId` (dashboard), `statusId` (worker polling), `language`.

### `worker_tasks`
Tracks **one pipeline stage for one repo** (e.g. CLONE, PARSING). Key fields:
`repoId`, `taskTypeId`, `statusId`, `startedAt`/`completedAt`, `attempts`/
`maxAttempts`, `errorType`, `errorMessage`, and a JSON `result` summary.

- `UNIQUE(repoId, taskTypeId)` — at most one row per stage per repo. The worker
  relies on this for **idempotency** (insert, let Postgres reject duplicates).
- `errorType` stores the exception class name so failures can be grouped without
  parsing `errorMessage`.

### `webhook_events`
Raw audit log of every incoming Clerk webhook, written **before** processing so
events can be replayed. PK `id` is the Svix message id (idempotency key).
`status`: `pending → processed | failed`. `repoId` is nullable. Stores the full
`payload` as JSON. See `webhooks.md`.

### `conversations` & `messages`
Chat scaffolding (schema exists; chat endpoint not yet implemented).

- `conversations` — one chat session linking a `User` and a `Repository`.
- `messages` — one turn each: `roleId` → `message_roles` (`user`/`assistant`),
  `content`, and `sourcePaths` (string array of file paths retrieved for an
  assistant answer, for source attribution; null on user turns).
  Indexed by `conversationId`.

### `code_chunks`  ← produced by the parse stage
A node in the repo's symbol tree. One per module (whole file) and one per
class/function/method.

| Column           | Meaning                                                        |
| ---------------- | ------------------------------------------------------------- |
| `repoId`         | owning repo (FK, `ON DELETE CASCADE`)                         |
| `path`           | relative file path, e.g. `app/services/urlService.py`        |
| `type`           | `module` / `class` / `method` / `function` / `interface` / `type` |
| `name`           | short name, e.g. `save_repo`                                  |
| `fullName`       | fully-qualified, e.g. `app.services.urlService.save_repo`     |
| `startLine`/`endLine` | location in the file                                    |
| `content`        | the source text of the chunk                                  |
| `metadata` (JSON)| signature, docstring, decorators, visibility, imports/exports, lineCount, contentHash, unresolvedCalls, etc. |
| `parentChunkId`  | self-FK → parent chunk (module → class → method tree)        |

Indexed on `repoId`, `path`, `type`, `name`. Re-indexing a repo deletes and
recreates these rows (clean replace).

### `code_connections`  ← produced by the parse stage
A directed edge between chunks — an **import** or a **call**.

| Column           | Meaning                                                        |
| ---------------- | ------------------------------------------------------------- |
| `repoId`         | owning repo (FK, cascade)                                     |
| `sourceChunkId`  | the chunk that imports/calls (FK → code_chunks)              |
| `targetSymbol`   | raw text of what was referenced                              |
| `targetChunkId`  | resolved target chunk, or null if unresolved (FK)           |
| `connectionType` | `import` or `call`                                            |
| `sourceLine`     | line of the reference                                         |
| `targetPath`     | resolved file path of the target, if known                  |
| `confidence`     | `resolved` / `partial` / `unresolved`                        |
| `metadata` (JSON)| kind, module, names, caller/callee text, source path        |

Indexed on `repoId`, `sourceChunkId`, `targetChunkId`. See
`indexing-pipeline.md` for how confidence is determined.

## Enums (and what the values mean)

```
RepoStatus    PENDING(1)  INDEXING(2)  INDEXED(3)  FAILED(4)  OUTDATED(5)
TaskType      FULL_PIPELINE(1)  CLONE(2)  CHUNK(3)  EMBED(4)  PARSING(5)
TaskStatus    PENDING(1)  RUNNING(2)  RETRYING(3)  SUCCESS(4)  FAILED(5)
MessageRole   USER(1)  ASSISTANT(2)
```

Only `CLONE` and `PARSING` task types are actually used today; the others
(`FULL_PIPELINE`, `CHUNK`, `EMBED`) are reserved for future partial re-runs.

## Notes for changing the schema

- Add/modify a model in `repo_models.py`, then generate a migration with Alembic
  (`alembic revision --autogenerate -m "..."`), review it, and `alembic upgrade head`.
- If you add a new enum value, the startup seeder will insert the new lookup row
  automatically (existing rows are left untouched thanks to `ON CONFLICT DO NOTHING`).
- `db.echo=True` is on in `db.py`, so SQL is logged — handy in dev, noisy in prod.
