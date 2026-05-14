from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.schema.urlSchema import TrustedGitHubRepoLink
from app.utils.utils import authenticate_and_get_user_id
from app.models.db import get_db
from app.models.repo_models import Repository, WorkerTask
from app.models.repo_models import TaskStatus, RepoStatus

router = APIRouter(prefix="/api", tags=["repositories"])


@router.post("/repos", status_code=201)
async def submit_repo(request: Request, payload: TrustedGitHubRepoLink):
    """Validate the URL and enqueue an indexing job. Returns 201 immediately.
    """
    user = authenticate_and_get_user_id(request)

    await request.app.state.redis.enqueue_job(
        "index_repo",
        user_id=user["user_id"],
        github_url=str(payload.url),
    )

    return {"status": "queued", "message": "Repository queued for indexing"}


"""endpoint for frontend to poll for task progress. Returns the current phase of the background task by its ID."""
@router.get("/tasks/{task_id}")
async def get_task_phase(task_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """return the current phase of a background task by its ID. This is used by the frontend to poll for task progress.

    Phases: `pending`, `fetching`, `indexing`, `completed`, `indexed`, `retrying`, `failed`.
    """
    _ = authenticate_and_get_user_id(request)

    res = await db.execute(select(WorkerTask).where(WorkerTask.id == task_id))
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # default mapping
    phase = "pending"

    if task.status == TaskStatus.PENDING:
        phase = "pending"
    elif task.status == TaskStatus.RUNNING:
        # running tasks: map by taskType to a human-friendly phase
        tt = getattr(task, "taskType", None)
        ttval = getattr(tt, "value", None)
        if ttval == "clone":
            phase = "cloning"
        else:
            phase = "indexing"
    elif task.status == TaskStatus.RETRYING:
        phase = "retrying"
    elif task.status == TaskStatus.SUCCESS:
        # If the repository itself is marked indexed, expose `indexed` otherwise `completed`
        repo_res = await db.execute(select(Repository).where(Repository.id == task.repoId))
        repo = repo_res.scalars().first()
        if repo and getattr(repo, "status", None) == RepoStatus.INDEXED:
            phase = "indexed"
        else:
            phase = "completed"
    elif task.status == TaskStatus.FAILED:
        phase = "failed"

    return {
        "taskId": task.id,
        "repoId": task.repoId,
        "phase": phase,
        "startedAt": task.startedAt.isoformat() if task.startedAt else None,
        "completedAt": task.completedAt.isoformat() if task.completedAt else None,
        "attempts": task.attempts,
        "errorType": task.errorType,
        "errorMessage": task.errorMessage,
    }