"""
Service layer for GitHub repository operations.

Responsibilities:
    - GitHub API communication (repo metadata, file tree)
    - Repository file-tree filtering (non-destructive)
    - Metadata normalization (GitHub response -> DB fields)
    - Repository persistence (save, duplicate check)

All GitHub API calls share a single httpx.AsyncClient instance created
on first use and reused for the lifetime of the process.
"""
import re
import uuid
from urllib.parse import urlparse
import httpx
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.app_config import settings
from app.models.repo_models import RepoStatus, Repository
from pathlib import Path



# Directories skipped entirely (never traversed)
EXCLUDED_DIRECTORIES = {
    # version control / editor
    ".git", ".svn", ".hg",
    ".vscode", ".idea", ".eclipse", ".settings",
    ".github", ".gitlab", ".circleci", ".husky",
    # dependency caches
    "node_modules", "bower_components", "jspm_packages",
    ".yarn", ".pnp",
    # Python caches
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".tox", ".nox", ".eggs", ".ruff_cache",
    "*.egg-info",
    # build output
    "dist", "build", "out", "_build",
    "target", "cmake-build-debug", "cmake-build-release",
    # JVM
    ".gradle", ".mvn",
    # virtual environments
    ".venv", "venv", "env", ".env",
    # coverage / profiling
    "coverage", "htmlcov", ".nyc_output",
    # misc
    "vendor", ".terraform", ".serverless",
    ".next", ".nuxt", ".svelte-kit",
    ".parcel-cache", ".turbo", ".vercel",
    "storybook-static",
}

# Migration directory names — entire folder skipped
MIGRATION_DIRECTORY_PATTERNS = {
    "migrations", "migrate", "alembic",
    "db_migrations", "schema_migrations",
    "prisma", "drizzle",
}

# Migration filenames matched by regex (e.g. 0001_initial.py, 20240312_add_col.sql)
MIGRATION_FILENAME_PATTERNS = [
    r"^\d{4,14}[_\-]",      # timestamp or sequence prefix
    r"^V\d+__",              # Flyway style  V1__create.sql
    r"^R__",                 # Flyway repeatable
]

# Exact filenames to skip (config / noise / CI)
EXCLUDED_FILENAMES = {
    # lock / dependency manifests (not useful for code understanding)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "uv.lock",
    "composer.lock", "Gemfile.lock", "Cargo.lock",
    "go.sum", "flake.lock",
    # build / config noise
    ".DS_Store", "Thumbs.db", "desktop.ini",
    ".editorconfig", ".prettierrc", ".prettierignore",
    ".eslintcache", ".stylelintrc",
    ".browserslistrc", ".babelrc",
    "tsconfig.tsbuildinfo",
    # CI descriptors (not source code)
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "Procfile", "Makefile", "Justfile",
    "Vagrantfile", "Jenkinsfile",
    ".dockerignore", ".gitignore", ".gitattributes",
    ".npmignore", ".slugignore",
}

# File extensions to skip (binary / non-source / noise)
EXCLUDED_EXTENSIONS = {
    # ── images ──
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".tiff", ".tif", ".psd", ".ai", ".eps", ".raw", ".cr2", ".nef",
    ".heic", ".heif", ".avif", ".jxl",
    # ── compiled / object ──
    ".exe", ".dll", ".so", ".dylib", ".obj", ".o", ".a", ".lib",
    ".class", ".pyc", ".pyo", ".pyd",
    ".wasm", ".bc",
    # ── archives ──
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z",
    ".jar", ".war", ".ear",
    ".deb", ".rpm", ".apk", ".dmg", ".iso", ".img",
    # ── media ──
    ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv",
    ".wav", ".flac", ".ogg", ".aac", ".m4a", ".wma",
    ".webm", ".3gp",
    # ── ML / data blobs ──
    ".bin", ".dat", ".pkl", ".pickle",
    ".pt", ".pth", ".ckpt", ".safetensors",
    ".h5", ".hdf5", ".onnx", ".pb", ".tflite",
    ".npy", ".npz", ".parquet", ".feather", ".arrow",
    # ── documents ──
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".odt", ".ods", ".odp",
    ".rtf", ".epub",
    # ── fonts ──
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    # ── lock files ──
    ".lock", ".lck",
    # ── source maps (not useful for understanding) ──
    ".map",
    # ── database files ──
    ".sqlite", ".sqlite3", ".db", ".mdb",
    # ── certificates / keys (sensitive, not code) ──
    ".pem", ".crt", ".key", ".p12", ".pfx", ".jks",
    # ── misc binary ──
    ".swp", ".swo", ".bak", ".tmp", ".log",
    ".min.js", ".min.css",
}
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


# Metadata extraction and normalisation


def _map_metadata_to_db_fields(data: dict, github_url: str) -> dict:
    """
    Normalise a raw GitHub API response into the fields expected by Repository.
    """
  
    owner_info   = data.get("owner") or {}

    return {
        "githubUrl":     github_url,
        "repoName":      data.get("name"),
        "repoOwner":     owner_info.get("login"),
        "defaultBranch": data.get("default_branch"),
        "isPrivate":     data.get("private", False),
        "description":   data.get("description"),
        "language":      data.get("language"),
        "topics":        data.get("topics", [])
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


async def check_existing_repo( user_id: str,github_url: str,db: AsyncSession
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

def collect_clean_repo(repo_path: str) -> dict:
    """
    Walk a locally cloned repo and return both the clean folder
    structure and the accepted source files.
    Returns:
        {
            "folders": ["src", "src/auth", "src/models", ...],
            "files":   [
                {"path": "src/auth/login.py", "abs_path": "..."},
                ...
            ]
        }
    """
    root    = Path(repo_path)
    folders = set()
    files   = []

    for item in root.rglob("*"):
        rel        = item.relative_to(root)
        parts      = rel.parts
        parent_dirs = parts[:-1]

        # skip anything inside an excluded directory
        if any(d in EXCLUDED_DIRECTORIES for d in parts):
            continue

        # skip migration directories
        if any(d in MIGRATION_DIRECTORY_PATTERNS for d in parts):
            continue

        # collect folders
        if item.is_dir():
            folders.add(str(rel).replace("\\", "/"))
            continue

        # from here only files
        filename = parts[-1]

        # skip migration files by pattern
        if any(re.match(p, filename) for p in MIGRATION_FILENAME_PATTERNS):
            continue

        # skip excluded filenames
        if filename in EXCLUDED_FILENAMES:
            continue

        # skip excluded extensions
        if item.suffix.lower() in EXCLUDED_EXTENSIONS:
            continue

        # skip dotfiles
        if filename.startswith("."):
            continue

        # skip empty files
        if item.stat().st_size == 0:
            continue

        # collect the file
        files.append({
            "path":     str(rel).replace("\\", "/"),
            "abs_path": str(item),
        })

        # also register all its parent folders
        for i in range(1, len(parts)):
            folders.add("/".join(parts[:i]))

    return {
        "folders": sorted(folders),   # sorted so tree renders top-down
        "files":   files,
    }


def read_file_contents(accepted_files: list[dict]) -> list[dict]:
    """
    Read content of each accepted file into memory.
    Skips files that cannot be decoded as UTF-8.
    """
    result = []

    for item in accepted_files:
        try:
            content = Path(item["abs_path"]).read_text(encoding="utf-8")
            if not content.strip():
                continue
            result.append({
                "path":    item["path"],
                "content": content,
            })
        except (UnicodeDecodeError, PermissionError):
            continue

    return result
