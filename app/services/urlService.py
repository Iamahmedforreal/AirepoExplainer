"""
Service layer for GitHub repository operations.

Responsibilities:
    - GitHub API communication (repo metadata, file tree)
    - Tree filtering (remove non-source files)
    - Metadata normalization (GitHub response -> DB fields)
    - Repository persistence (save, duplicate check)

All GitHub API calls share a single httpx.AsyncClient instance created
on first use and reused for the lifetime of the process.
"""

import os
import uuid
from datetime import datetime
from urllib.parse import urlparse
import httpx
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.app_config import settings
from app.models.repo_models import RepoStatus, Repository



# HTTP client


_http_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """
    Return the shared GitHub API client, creating it on first call.

    The client is reused across all requests to avoid the overhead of
    establishing a new TCP connection per call. A new client is created
    only if the existing one has been closed.
    """
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"token {settings.github_api_key}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=httpx.Timeout(5.0),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
            ),
        )
    return _http_client



# Tree filtering constants


# File extensions that carry no value for code understanding or embedding.
# Extend these sets as new irrelevant file types are encountered in the wild.
EXCLUDED_EXTENSIONS = {
    # docs
    ".md", ".mdx", ".rst", ".txt", ".pdf", ".doc", ".docx",
    # config / env
    ".env", ".env.example", ".env.local", ".env.sample",
    # images
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    # fonts
    ".ttf", ".woff", ".woff2", ".eot",
    # video / audio
    ".mp4", ".mp3", ".wav", ".avi",
    # archives
    ".zip", ".tar", ".gz", ".rar",
    # compiled / binary — not human-readable, useless for RAG
    ".pyc", ".pyo", ".exe", ".dll", ".so", ".class",
    # lock files — auto-generated, never contains business logic
    ".lock",
}

# Exact filenames that should be dropped regardless of extension.
EXCLUDED_FILENAMES = {
    # project docs
    "README.md", "README", "CHANGELOG.md", "CHANGELOG",
    "CONTRIBUTING.md", "LICENSE", "LICENSE.md", "NOTICE",
    # env templates
    ".env.example", ".env.sample", ".env.template",
    # editor / linter config
    ".editorconfig", ".prettierrc", ".eslintrc",
    # version control config
    ".gitignore", ".gitattributes", ".gitmodules",
    # build orchestration
    "Makefile",
}

# Directory names that indicate generated, vendored, or non-source content.
# Checked against every path segment, not just the top-level directory.
EXCLUDED_DIRECTORIES = {
    # dependency trees
    "node_modules", "venv", ".venv", "env", "__pycache__",
    "site-packages", ".tox", "dist", "build", "eggs",
    # version control internals
    ".git", ".svn", ".hg",
    # IDE state
    ".idea", ".vscode", ".vs",
    # test / type-check caches
    "coverage", ".coverage", ".pytest_cache", ".mypy_cache",
    # frontend build output
    ".next", ".nuxt", "out", ".cache",
}



# GitHub API calls


async def _fetch_repo_from_github(owner: str, repo_name: str) -> dict:
    """
    Fetch repository metadata from the GitHub REST API.

    Returns the raw GitHub response dict on success.
    Raises ValueError for 404 (repo not found).
    Raises RuntimeError for rate limit errors and network failures.
    """
    client = _get_client()

    try:
        response = await client.get(
            f"/repos/{owner}/{repo_name}",
            timeout=10.0
        )

        if response.status_code == 404:
            raise ValueError(f"Repository not found: {owner}/{repo_name}")

        if response.status_code in (403, 429):
            reset = response.headers.get("X-RateLimit-Reset", "unknown")
            raise RuntimeError(f"GitHub rate limit hit. Resets at: {reset}")

        response.raise_for_status()
        return response.json()

    except httpx.TimeoutException:
        raise RuntimeError(f"GitHub timed out fetching {owner}/{repo_name}")

    except httpx.ConnectError:
        raise RuntimeError("Could not connect to GitHub")


async def fetch_repo_tree(owner: str, repo_name: str, branch: str) -> dict:
    """
    Fetch the full recursive file tree for a repository branch.

    Uses the Git Trees API with recursive=1 to retrieve all paths in a
    single request rather than traversing directories individually.

    Returns a normalised dict:
        sha          - tree SHA at time of fetch
        total_count  - total items before any filtering
        tree         - list of {path, type, size, sha} dicts
        truncated    - True if GitHub capped the response (repo > ~100k files)

    Raises ValueError for 404 (repo/branch not found) and 409 (empty repo).
    Raises RuntimeError for rate limit errors and network failures.
    """
    client = _get_client()
    endpoint = f"/repos/{owner}/{repo_name}/git/trees/{branch}"

    try:
        response = await client.get(endpoint, params={"recursive": "1"})

        if response.status_code == 404:
            raise ValueError(
                f"Repository or branch not found: {owner}/{repo_name} @ {branch}"
            )

        if response.status_code == 409:
            raise ValueError(f"Repository is empty: {owner}/{repo_name}")

        if response.status_code in (403, 429):
            raise RuntimeError(
                f"GitHub rate limit reached. "
                f"Resets at: {response.headers.get('X-RateLimit-Reset', 'unknown')}"
            )

        response.raise_for_status()
        data = response.json()
        tree_items = data.get("tree", [])

        return {
            "sha":         data.get("sha"),
            "total_count": len(tree_items),
            "truncated":   data.get("truncated", False),
            "tree": [
                {
                    "path": item.get("path"),
                    "type": item.get("type"),
                    "size": item.get("size"),
                    "sha":  item.get("sha"),
                }
                for item in tree_items
            ],
        }

    except httpx.TimeoutException:
        raise RuntimeError(
            f"GitHub API timed out fetching tree: {owner}/{repo_name} @ {branch}"
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"GitHub API error {e.response.status_code}: {e}")



# Tree filtering


async def clean_tree_data(tree: list[dict]) -> list[dict]:
    """
    Remove non-source files from a raw GitHub tree response.

    Filters out:
        - directories (type != blob)
        - files inside excluded directories (e.g. node_modules, venv)
        - files with excluded names (e.g. README.md, Makefile)
        - files with excluded extensions (e.g. .png, .lock)
        - hidden files (dotfiles like .DS_Store, .eslintrc)
        - empty files (size == 0, nothing to embed)
    """
    cleaned = []

    for item in tree:
        # directories have no content 
        if item["type"] != "blob":
            continue

        path: str = item.get("path", "")
        parts = path.split("/")
        filename = parts[-1]
        parent_dirs = parts[:-1]

        # drop anything nested inside an excluded directory
        if any(d in EXCLUDED_DIRECTORIES for d in parent_dirs):
            continue

        # drop files whose name is on the exclusion list
        if filename in EXCLUDED_FILENAMES:
            continue

        # drop files whose extension is on the exclusion list
        _, ext = os.path.splitext(filename)
        if ext.lower() in EXCLUDED_EXTENSIONS:
            continue

        # drop dotfiles — editor config, tool config, OS metadata
        if filename.startswith("."):
            continue

        # drop empty files — nothing to embed
        if item.get("size", 0) == 0:
            continue

        cleaned.append(item)

    return cleaned


# Metadata extraction and normalisation

def _parse_github_date(date_str: str | None) -> datetime | None:
    """
    Convert a GitHub ISO 8601 timestamp string to a timezone-aware datetime.
    Returns None if the input is missing or empty.
    """
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def _map_metadata_to_db_fields(data: dict, github_url: str) -> dict:
    """
    Normalise a raw GitHub API response into the fields expected by Repository.
    """
    license_info = data.get("license") or {}
    owner_info   = data.get("owner") or {}

    return {
        "githubUrl":     github_url,
        "repoName":      data.get("name"),
        "repoOwner":     owner_info.get("login"),
        "defaultBranch": data.get("default_branch"),
        "isPrivate":     data.get("private", False),
        "description":   data.get("description"),
        "language":      data.get("language"),
        "topics":        data.get("topics", []),
    }


async def get_owner_and_repo(github_url: str) -> tuple[str, str]:
    """
    Parse owner and repository name from a GitHub URL.

    Handles both HTTPS and .git-suffixed URLs.
    Raises ValueError if the URL does not contain a valid owner/repo path.
    """
    try:
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("URL must contain both owner and repository name")
        return path_parts[0], path_parts[1].replace(".git", "")
    except Exception as error:
        raise ValueError(f"Invalid GitHub URL: {error}")


async def extract_repo_info(github_url: str) -> tuple[dict, str, str]:
    """
    Fetch and normalise all information needed to create a Repository record.

    Returns:
        metadata   - normalised dict ready for save_repo()
        owner      - GitHub owner login
        repo_name  - repository name

    Raises ValueError on any failure so the caller gets a single,
    consistent error type regardless of what went wrong internally.
    """
    try:
        owner, repo_name = await get_owner_and_repo(github_url)
        raw = await _fetch_repo_from_github(owner, repo_name)
        metadata = _map_metadata_to_db_fields(raw, github_url)
        return metadata, owner, repo_name
    except Exception as error:
        raise ValueError(f"Failed to extract repo info: {error}")


# Database operations

async def save_repo(user_id: str, metadata: dict, db: AsyncSession) -> Repository:
    """
    Persist a new Repository record to the database.

    Expects metadata in the shape returned by _map_metadata_to_db_fields().
    Status is always set to PENDING on creation — the worker updates it
    as the indexing pipeline progresses.

    Raises ValueError if a required metadata field is missing.
    Raises Exception (wrapping SQLAlchemyError) on database failure,
    rolling back the transaction before re-raising.
    """
    try:
        new_repo = Repository(
            id=str(uuid.uuid4()),
            userId=user_id,
            githubUrl=metadata["githubUrl"],
            repoName=metadata.get("repoName"),
            repoOwner=metadata.get("repoOwner"),
            defaultBranch=metadata.get("defaultBranch"),
            isPrivate=metadata.get("isPrivate", False),
            description=metadata.get("description"),
            language=metadata.get("language"),
            topics=metadata.get("topics", []),
            status=RepoStatus.PENDING,
        )

        db.add(new_repo)
        await db.commit()
        await db.refresh(new_repo)
        return new_repo

    except KeyError as e:
        raise ValueError(f"Missing required field in metadata: {e}")
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error while saving repo: {e}")


async def check_existing_repo(
    user_id: str,
    github_url: str,
    db: AsyncSession
) -> Repository | None:
    """
    Return the existing Repository record if this user has already submitted
    this URL, otherwise return None.

    Used by the router to short-circuit duplicate submissions before
    any GitHub API calls are made.
    """
    query = select(Repository).where(
        and_(
            Repository.userId == user_id,
            Repository.githubUrl == github_url,
        )
    )
    result = await db.execute(query)
    return result.scalars().first()