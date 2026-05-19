Comment Director — where and how to add comprehensive comments

Goal
- Provide a short guide for engineers to add clear, consistent inline comments and file-level headers.

Recommended conventions
- File header: 3–5 lines at top explaining purpose and public API of the module.
- Function docstrings: use short `"""One-line summary."""` then one blank line and a short paragraph if needed.
- Complex logic: add inline comments above blocks explaining intent, not implementation details.
- TODOs: use `# TODO: reason` with owner initials.

Where to add comments in this repo
- `app/services/urlService.py`: describe the cleaning rules, why particular directories/extensions are skipped, and the expected return shapes of `collect_clean_repo` and `read_file_contents`.
- `app/ARQ/task.py`: document task phases, retry policy, and how `WorkerTask` rows are used to track attempts.
- `app/models/repo_models.py`: add a short comment for each Enum describing valid transitions and their meanings.
- `clerk-react/src/libs/api.ts`: document each function's request/response shape and error handling expectations.
- `app/router/webhookRouter.py`: explain signature verification and mapping to `webhook_events` table.

Example comment snippets
- Module header:
  """
  `urlService` — GitHub API helpers and repo tree cleaning.

  Public functions:
    - `extract_repo_info(url) -> (metadata, owner, repo)`
    - `collect_clean_repo(path) -> {folders, files}`
  """

- Function docstring:
  def get_owner_and_repo(url: str) -> tuple[str, str]:
      """Return `(owner, repo)` parsed from a GitHub URL.

      Raises `ValueError` if parsing fails.
      """

Next steps
- If you want, I can apply these recommended comments directly into key files (`urlService.py`, `repo_models.py`, and `webhookRouter.py`). Say which files to update.
