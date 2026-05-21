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
        "clone_repo_task",
        user_id=user["user_id"],
        github_url=str(payload.url),
    )

    return {"status": "queued", "message": "Repository queued for cloning"}


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

    if task.statusId == TaskStatus.PENDING:
        phase = "pending"
    elif task.statusId == TaskStatus.RUNNING:
        # running tasks: map by taskType relationship name to a human-friendly phase
        tt = getattr(task, "taskType", None)
        ttval = getattr(tt, "name", None) if tt else None
        if ttval == "clone":
            phase = "cloning"
        elif ttval == "parse":
            phase = "parsing"
        else:
            phase = "indexing"
    elif task.statusId == TaskStatus.RETRYING:
        phase = "retrying"
    elif task.statusId == TaskStatus.SUCCESS:
        # If the repository itself is marked indexed, expose `indexed` otherwise `completed`
        repo_res = await db.execute(select(Repository).where(Repository.id == task.repoId))
        repo = repo_res.scalars().first()
        if repo and getattr(repo, "statusId", None) == RepoStatus.INDEXED:
            phase = "indexed"
        else:
            phase = "completed"
    elif task.statusId == TaskStatus.FAILED:
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
