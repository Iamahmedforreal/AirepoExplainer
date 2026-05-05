from datetime import datetime
from urllib.parse import urlparse
import uuid
from cachetools import TTLCache
import httpx
from sqlalchemy import select , and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.models.users import RepoStatus, Repository
from app.config.app_config import settings
from urllib.parse import urlparse
from datetime import datetime


_http_client: httpx.AsyncClient | None = None
_repo_cache: TTLCache = TTLCache(maxsize=500, ttl=300) 



def _get_client() -> httpx.AsyncClient:
    """Return the shared async client, creating it once on first call."""
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


def _parse_github_date(date_str: str | None):
    """Convert GitHub's ISO string → real datetime object."""
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


async def _fetch_repo_from_github(owner: str, repo_name: str) -> dict:

    cache_key = f"{owner}/{repo_name}"

    if cache_key in _repo_cache:
        return _repo_cache[cache_key]

    client = _get_client()

    try:
        response = await client.get(f"/repos/{cache_key}")
        if response.status_code == 404:
            raise ValueError(f"Repository not found: {cache_key}")

        if response.status_code in (403, 429):
            # Rate limited — serve stale cache if we have it
            if cache_key in _repo_cache:
                return _repo_cache[cache_key]
            raise RuntimeError(
                f"GitHub rate limit reached. "
                f"Resets at: {response.headers.get('X-RateLimit-Reset', 'unknown')}"
            )

        response.raise_for_status()
        data = response.json()
        _repo_cache[cache_key] = data
        return data

    except httpx.TimeoutException:
        raise RuntimeError(f"GitHub API timed out after 5s — {cache_key}")
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"GitHub API error {e.response.status_code}: {e}")
    

async def extract_repo_info(github_url: str):
    try:
        owner, repo_name = await get_owner_and_repo(github_url)
        raw= await _fetch_repo_from_github(owner, repo_name)
        metadata =  _map_metadata_to_db_fields(raw, github_url)
        return metadata , owner , repo_name
    except Exception as error:
        raise ValueError(f"Failed to extract repo info: {error}")


async def get_owner_and_repo(github_url: str):
    try:
        parsed = urlparse(github_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError("URL must contain both owner and repository name")
        return path_parts[0], path_parts[1].replace(".git", "")
    except Exception as error:
        raise ValueError(f"Invalid GitHub URL: {error}")




def _parse_github_date(date_str: str | None):
    
    if not date_str:
        return None
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def _map_metadata_to_db_fields(data: dict, github_url: str) -> dict:
    license_info = data.get("license") or {}
    owner_info   = data.get("owner") or {}

    return {
        "githubUrl":      github_url,
        "repoName":       data.get("name"),
        "repoOwner":      owner_info.get("login"),
        "defaultBranch":  data.get("default_branch"),
        "isPrivate":      data.get("private", False),
        "sizeKb":         data.get("size"),
        "description":    data.get("description"),
        "language":       data.get("language"),
        "topics":         data.get("topics", []),
        "stars":          data.get("stargazers_count"),
        "license":        license_info.get("spdx_id"),
        "isArchived":     data.get("archived", False),
        "repoCreatedAt":  _parse_github_date(data.get("created_at")),
        "repoUpdatedAt":  _parse_github_date(data.get("updated_at")),
    }


async def save_repo(user_id: str, metadata: dict, db: AsyncSession) -> Repository:
    try:
        new_repo = Repository(
            id=str(uuid.uuid4()),
            userId=user_id,
            githubUrl=metadata["githubUrl"],
            repoName=metadata.get("repoName"),
            repoOwner=metadata.get("repoOwner"),
            defaultBranch=metadata.get("defaultBranch"),
            isPrivate=metadata.get("isPrivate", False),
            sizeKb=metadata.get("sizeKb"),
            description=metadata.get("description"),
            language=metadata.get("language"),
            topics=metadata.get("topics", []),
            stars=metadata.get("stars"),
            license=metadata.get("license"),
            isArchived=metadata.get("isArchived", False),
            repoCreatedAt=metadata.get("repoCreatedAt"),
            repoUpdatedAt=metadata.get("repoUpdatedAt"),
            status=RepoStatus.PENDING,
        )

        db.add(new_repo)
        await db.commit()
        await db.refresh(new_repo)
        return new_repo

    except KeyError as e:
        raise ValueError(f"Missing required field in metadata: {str(e)}")
    except SQLAlchemyError as e:
        await db.rollback()
        raise Exception(f"Database error while saving repo: {str(e)}")




async def check_existing_repo(user_id: str, github_url: str, db: AsyncSession):
    query = select(Repository).where(
        and_(
            Repository.userId == user_id,
            Repository.githubUrl == github_url,
        )
    )
    result = await db.execute(query)
    return result.scalars().first()
