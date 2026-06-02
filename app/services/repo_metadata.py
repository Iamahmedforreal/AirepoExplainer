"""
Repository row helpers — single place to read/update pipeline metadata.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repo_models import Repository, RepoStatus


def repo_to_dict(repo: Repository) -> dict:
    status_name = repo.status.name if repo.status else None
    return {
        "id": repo.id,
        "githubUrl": repo.githubUrl,
        "repoOwner": repo.repoOwner,
        "repoName": repo.repoName,
        "defaultBranch": repo.defaultBranch,
        "language": repo.language,
        "description": repo.description,
        "topics": repo.topics or [],
        "isPrivate": repo.isPrivate,
        "status": status_name,
        "clonePath": repo.clonePath,
        "sourceFileCount": repo.sourceFileCount,
        "chunkCount": repo.chunkCount,
        "connectionCount": repo.connectionCount,
        "indexedAt": repo.indexedAt.isoformat() if repo.indexedAt else None,
        "createdAt": repo.createdAt.isoformat() if repo.createdAt else None,
        "updatedAt": repo.updatedAt.isoformat() if repo.updatedAt else None,
    }


async def get_repo(db: AsyncSession, repo_id: str) -> Repository | None:
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    return result.scalars().first()


async def get_repo_for_worker(db: AsyncSession, repo_id: str) -> Repository:
    repo = await get_repo(db, repo_id)
    if repo is None:
        raise ValueError(f"Repository not found: {repo_id}")
    return repo


async def apply_github_metadata(
    db: AsyncSession,
    repo: Repository,
    metadata: dict,
) -> Repository:
    """Refresh GitHub-sourced fields on an existing row."""
    repo.githubUrl = metadata["githubUrl"]
    repo.repoOwner = metadata.get("repoOwner")
    repo.repoName = metadata.get("repoName")
    repo.defaultBranch = metadata.get("defaultBranch")
    repo.isPrivate = metadata.get("isPrivate", False)
    repo.description = metadata.get("description")
    repo.language = metadata.get("language")
    repo.topics = metadata.get("topics") or []
    await db.commit()
    await db.refresh(repo)
    return repo


async def mark_clone_complete(
    db: AsyncSession,
    repo: Repository,
    *,
    clone_path: str,
    source_file_count: int,
) -> None:
    repo.clonePath = clone_path
    repo.sourceFileCount = source_file_count
    repo.statusId = RepoStatus.INDEXING.value
    await db.commit()


async def mark_indexed(
    db: AsyncSession,
    repo: Repository,
    *,
    chunk_count: int,
    connection_count: int,
) -> None:
    repo.chunkCount = chunk_count
    repo.connectionCount = connection_count
    repo.indexedAt = datetime.now(timezone.utc)
    repo.statusId = RepoStatus.INDEXED.value
    await db.commit()


async def mark_failed(db: AsyncSession, repo_id: str) -> None:
    repo = await get_repo_for_worker(db, repo_id)
    repo.statusId = RepoStatus.FAILED.value
    await db.commit()
