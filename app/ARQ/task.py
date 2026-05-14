"""
background task file for ARQ workers. Each function here is designed to be run as a background task.
"""
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import update
from app.models.db import async_session
from app.models.repo_models import (
    Repository,
    RepoStatus,
    TaskStatus,
    TaskType,
    WorkerTask,
)
from app.services.urlService import (
    extract_repo_info,
    check_existing_repo,
    save_repo,
)
from app.services.clone_service import clone_repo



async def index_repo(ctx, *, user_id: str, github_url: str) -> dict:
    """
    This function is designed to be run as a background task in ARQ.
    """
    task_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:

        # ── PRIORITY 1: metadata + save ───────────────────────────────────────

       

        # 1. Fetch metadata from GitHub
        metadata, owner, repo_name = await extract_repo_info(github_url)

        # 2. Duplicate check
        existing = await check_existing_repo(user_id, metadata["githubUrl"], db)
        if existing:
            
            raise HTTPException(status_code=400, detail="Repository already exists")

        # 3. Save repo row
        repo = await save_repo(user_id, metadata, db)
        repo_id = repo.id

        # Audit row
        task_row = WorkerTask(
            id=task_id,
            repoId=repo_id,
            taskType=TaskType.FETCH_TREE,
            status=TaskStatus.RUNNING,
            startedAt=started_at,
            attempts=1,
        )
        db.add(task_row)
        await db.commit()

        
        # ── PRIORITY 2: shallow clone ─────────────────────────────────────────

        try:
            clone_result = clone_repo(owner, repo_name, github_url)
            clone_path = clone_result["clone_path"]
            file_count = len(clone_result["files"])

            # Mark success
            completed_at = datetime.now(timezone.utc)
            result = {
                "clone_path": clone_path,
                "folders": len(clone_result["folders"])
            }
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(status=RepoStatus.INDEXED)
            )
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_id)
                .values(status=TaskStatus.SUCCESS, completedAt=completed_at, result=result)
            )
            await db.commit()

            
            return {"repo_id": repo_id, "clone_path": clone_path, "files_accepted": file_count}

        except Exception as exc:
           
            completed_at = datetime.now(timezone.utc)
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(status=RepoStatus.FAILED)
            )
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_id)
                .values(
                    status=TaskStatus.FAILED,
                    completedAt=completed_at,
                    errorType=type(exc).__name__,
                    errorMessage=str(exc),
                )
            )
            await db.commit()
            raise
