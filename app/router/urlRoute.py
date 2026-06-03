from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schema.urlSchema import TrustedGitHubRepoLink
from app.utils.utils import authenticate_and_get_user_id
from app.models.db import get_db
from app.models.repo_models import Repository, WorkerTask
from app.models.repo_models import TaskStatus, RepoStatus
from app.services.urlService import extract_repo_info, save_repo, check_existing_repo
from app.services.repo_metadata import repo_to_dict

router = APIRouter(prefix="/api", tags=["repositories"])


@router.post("/repos", status_code=201)
async def submit_repo(
    request: Request,
    payload: TrustedGitHubRepoLink,
    db: AsyncSession = Depends(get_db),
):
    """Create or reuse a repository row, then enqueue clone. Returns repo metadata immediately."""
    user = authenticate_and_get_user_id(request)
    github_url = str(payload.url)

    existing = await check_existing_repo(user["user_id"], github_url, db)
    if existing and existing.statusId == RepoStatus.INDEXED.value:
        return {
            "status": "already_indexed",
            "repo": repo_to_dict(existing),
        }

    if existing:
        metadata, _, _ = await extract_repo_info(github_url)
        existing.githubUrl = metadata["githubUrl"]
        existing.repoOwner = metadata["repoOwner"]
        existing.repoName = metadata["repoName"]
        existing.defaultBranch = metadata.get("defaultBranch")
        existing.isPrivate = metadata.get("isPrivate", False)
        existing.description = metadata.get("description")
        existing.language = metadata.get("language")
        existing.topics = metadata.get("topics") or []
        existing.statusId = RepoStatus.PENDING.value
        existing.clonePath = None
        existing.sourceFileCount = None
        existing.chunkCount = None
        existing.connectionCount = None
        existing.indexedAt = None
        await db.commit()
        await db.refresh(existing)
        repo = existing
    else:
        metadata, _, _ = await extract_repo_info(github_url)
        repo = await save_repo(user["user_id"], metadata, db)

    job = await request.app.state.redis.enqueue_job("clone_repo_task", repo_id=repo.id)

    return {
        "status": "queued",
        "repoId": repo.id,
        "jobId": job.job_id if job else None,
        "repo": repo_to_dict(repo),
    }


@router.get("/repos/{repo_id}")
async def get_repo_metadata(
    repo_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return repository metadata and indexing stats for the dashboard."""
    user = authenticate_and_get_user_id(request)

    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.userId == user["user_id"],
        )
    )
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return repo_to_dict(repo)


@router.get("/tasks/{task_id}")
async def get_task_phase(task_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Poll task progress; includes a summary of repository metadata."""
    _ = authenticate_and_get_user_id(request)

    res = await db.execute(select(WorkerTask).where(WorkerTask.id == task_id))
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    phase = "pending"

    if task.statusId == TaskStatus.PENDING:
        phase = "pending"
    elif task.statusId == TaskStatus.RUNNING:
        tt = getattr(task, "taskType", None)
        ttval = getattr(tt, "name", None) if tt else None
        if ttval == "clone":
            phase = "cloning"
        elif ttval == "parsing":
            phase = "parsing"
        elif ttval == "embed":
            phase = "embedding"
        else:
            phase = "indexing"
    elif task.statusId == TaskStatus.RETRYING:
        phase = "retrying"
    elif task.statusId == TaskStatus.SUCCESS:
        repo_res = await db.execute(select(Repository).where(Repository.id == task.repoId))
        repo = repo_res.scalars().first()
        if repo and repo.statusId == RepoStatus.INDEXED.value:
            phase = "indexed"
        else:
            phase = "completed"
    elif task.statusId == TaskStatus.FAILED:
        phase = "failed"

    repo_res = await db.execute(select(Repository).where(Repository.id == task.repoId))
    repo = repo_res.scalars().first()

    return {
        "taskId": task.id,
        "repoId": task.repoId,
        "phase": phase,
        "startedAt": task.startedAt.isoformat() if task.startedAt else None,
        "completedAt": task.completedAt.isoformat() if task.completedAt else None,
        "attempts": task.attempts,
        "errorType": task.errorType,
        "errorMessage": task.errorMessage,
        "repo": repo_to_dict(repo) if repo else None,
    }
