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


import uuid
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
