# Indexing pipeline — clone → parse → chunks → connections

This is the core of the backend: how a submitted GitHub repo becomes a queryable
map of code. It runs as **two background ARQ tasks** that hand off to each other
via Redis. Both live in `app/ARQ/task.py`.

```
POST /api/repos ──enqueue──▶ clone_repo_task ──enqueue──▶ parse_repo_task
                                   │                            │
                              git clone +                  Tree-sitter parse +
                              file filtering               chunk/connection build
                                   │                            │
                          status = INDEXING              status = INDEXED
```

Each task also writes a `WorkerTask` row so progress and failures are tracked in
the DB (see `database.md` for that table).

---

## Stage 1 — `clone_repo_task`

Goal: get a clean copy of the repo on disk and record its metadata.

1. **Load the repo row** — `get_repo_for_worker(db, repo_id)` (raises if missing).
2. **Claim the work** — `_insert_task_or_get_existing(...)` inserts a `WorkerTask`
   of type `CLONE` in status `RUNNING`. A unique constraint on
   `(repoId, taskTypeId)` means if a row already exists the task short-circuits
   and returns `{"status": "already_exists"}` — this makes the task **idempotent**
   so a retried/duplicate job can't clone twice.
3. **Refresh GitHub metadata** — `extract_repo_info(githubUrl)` calls the GitHub
   API; `apply_github_metadata(...)` writes owner, name, default branch,
   language, description, topics, visibility onto the row.
4. **Clone** — `clone_repo(owner, repo_name, github_url)` (`clone_service.py`):
   - destination is `clone_base_dir/<owner>/<repo_name>` (wiped first if present),
   - **shallow** clone (`depth=1` — history isn't needed for parsing),
   - then `collect_clean_repo()` filters the tree and `read_file_contents()`
     loads the accepted files into memory.
5. **Record results** — `mark_clone_complete(...)` sets `clonePath`,
   `sourceFileCount`, and moves the repo to status `INDEXING`. The `WorkerTask`
   is marked `SUCCESS` with a JSON `result` summary.
6. **Hand off** — enqueue `parse_repo_task` for the same `repo_id`.

On any exception: `mark_failed(...)` flips the repo to `FAILED`, the `WorkerTask`
records `errorType` + `errorMessage`, and the error re-raises so ARQ can retry.

### What counts as a "source file"? (filtering rules)

`collect_clean_repo()` in `app/services/urlService.py` walks the clone and keeps
only files worth understanding. It skips:

- **Excluded directories** — `.git`, `node_modules`, `__pycache__`, `.venv`,
  `dist`/`build`, etc. (full set: `EXCLUDED_DIRECTORIES`).
- **Migration folders & files** — `migrations/`, `alembic/`, `prisma/`, and
  timestamp/Flyway-style filenames (`MIGRATION_*` patterns). These are noise for
  code understanding.
- **Excluded filenames** — lockfiles, `Dockerfile`, `Makefile`, CI descriptors,
  editor configs (`EXCLUDED_FILENAMES`).
- **Excluded extensions** — images, binaries, archives, media, ML blobs,
  documents, fonts, minified assets (`EXCLUDED_EXTENSIONS`).
- **Dotfiles** and **empty files**.

`read_file_contents()` then reads each kept file as UTF-8, silently skipping
anything that can't be decoded or is blank. The output shape is a list of
`{"path": "relative/path.py", "content": "..."}`.

---

## Stage 2 — `parse_repo_task`

Goal: turn source text into structured `code_chunks` + `code_connections`.

1. **Load + claim** — same pattern as stage 1, but `WorkerTask` type `PARSING`.
   Fails fast if `repo.clonePath` is missing (clone must have run first).
2. **Re-read files** — `load_files_from_clone(clonePath)` re-applies the same
   filtering and reads file contents from disk.
3. **Extract + persist** — `persist_extraction(db, repo_id, files)` does the real
   work (below).
4. **Record results** — `mark_indexed(...)` sets `chunkCount`, `connectionCount`,
   `indexedAt`, and moves the repo to status `INDEXED`. `WorkerTask` → `SUCCESS`.

Failure handling mirrors stage 1.

---

## Inside the parser: text → symbols → chunks → connections

This is the most important part to understand. Four modules cooperate:

```
files ─▶ tree_sitter_parser ─▶ ast_extractor ─▶ connection_builder ─▶ code_store ─▶ DB
        (text → AST)          (AST → symbols)  (symbols → edges)    (rows → Postgres)
```

### 1. `tree_sitter_parser.py` — text → AST

- `detect_language(path)` maps a file extension to a grammar
  (`.py`→python, `.js`/`.jsx`→javascript, `.ts`→typescript, `.tsx`→tsx).
- `parse_file(content, language)` lazily loads the right Tree-sitter grammar
  (cached with `lru_cache`) and returns the root AST node. Source is encoded as
  UTF-8 so byte offsets line up with the text.

### 2. `ast_extractor.py` — AST → `FileExtraction`

Walks the AST (separate walkers for Python vs JS/TS) and produces, per file, a
`FileExtraction` containing:

- **`symbols`** — every module/class/function/method as a `Symbol` with:
  - `name`, `kind`, `full_name` (e.g. `app.services.urlService.save_repo`),
  - `start_line`/`end_line`, `parent_full_name` (nesting),
  - `signature`, `docstring` (Python), `decorators`, `visibility`
    (`_name`/`#name` → private), `body_start_line`.
- **`imports`** — `ImportRef`s (module, imported names, line, `import` vs
  `from_import`). JS/TS named/default/namespace imports are parsed too.
- **`calls`** — `CallSite`s: which function called what callee text, on which
  line. Only calls made *inside* a tracked function are recorded.
- **`exports`** — JS/TS `export`ed symbol full-names.

`extract_repo(files)` runs this over all files, skipping unsupported languages.

> Note: `full_name` is derived from the file path via `path_to_module()`
> (`a/b/c.py` → `a.b.c`), which is what lets the connection builder later match
> an import target back to a real module chunk.

### 3. `connection_builder.py` — symbols → edges

`build_connections(...)` turns imports and calls into `ConnectionRecord`s
(future rows in `code_connections`). Two kinds:

- **import edges** — source is the *module* chunk; the target is resolved to a
  real file via `_resolve_import_path()`. This handles both absolute
  (`a.b.c` → `a/b/c.py`) and relative (`.`, `..`) imports, trying multiple
  extensions and `__init__.py`. Resolved → linked to the target module chunk.
- **call edges** — source is the calling function chunk. `_resolve_call_target()`
  tries, in order: a same-file symbol of that name, any known symbol whose
  full-name ends with the callee, then an imported name resolved to a target
  module + symbol.

Each record carries a **`confidence`**:
- `resolved` — target chunk found in this repo,
- `partial` — target file resolved but exact symbol not found,
- `unresolved` — couldn't link it (e.g. a third-party/stdlib call).

This confidence is the honest signal of how complete the graph is.

### 4. `code_store.py` — build rows + persist

`build_extraction_payload(repo_id, files)` materializes the DB rows:

- **One `module` chunk per file** (the whole file's content + module metadata:
  language, imports, exports, line count, content hash, child count).
- **One chunk per symbol** (class/function/method), with `parentChunkId` wired
  up so the tree (module → class → method) is navigable, and rich `metadata`
  (signature, docstring, decorators, visibility, unresolved calls, etc.).
- Then `build_connections(...)` produces the connection rows. As a nicety, when
  a call becomes `resolved`, the matching entry is removed from the source
  symbol's `unresolvedCalls` metadata so that list stays accurate.

`persist_extraction(db, repo_id, files)` writes it transactionally:

1. **Delete** existing `code_connections` then `code_chunks` for this repo — so
   re-indexing a repo is a clean replace, not a duplicate.
2. `add_all(chunk_rows)` + `add_all(connection_rows)`, then `flush()`.
3. Return a summary `{ files_extracted, chunks_created, connections_created, ... }`
   which the task uses to update repo counts.

---

## Status & error model (quick reference)

- **Repository status** (`RepoStatus`): `PENDING → INDEXING → INDEXED`, or
  `FAILED` on any error. `OUTDATED` exists for future re-index triggers.
- **WorkerTask** tracks each stage independently (`CLONE`, `PARSING`) with its
  own status, timings, attempts, and `result`/`error*` fields.
- **Idempotency**: the `(repoId, taskTypeId)` unique constraint plus the
  "already_exists" short-circuit prevents duplicate work from retries.
- **Worker limits** (`app/ARQ/worker.py`): up to 10 concurrent jobs,
  `job_timeout = 600s` (covers clone + parse).

## Common gotchas

- The pipeline only links calls/imports **within the same repo**. External
  libraries always show up as `unresolved` connections — that's expected.
- Only Python/JS/TS/TSX files produce symbols; everything else is filtered out
  or yields no extraction.
- If the ARQ worker isn't running, jobs never execute and repos never leave
  `PENDING`/`INDEXING`.
