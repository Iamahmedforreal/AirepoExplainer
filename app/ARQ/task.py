"""
ARQ background tasks for repository indexing.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
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
    save_repo,
)
from app.services.clone_service import clone_repo
from app.services.tree_sitter_parser import parse_repo


async def _get_existing_task(db, *, repo_id: str, task_type: TaskType) -> WorkerTask | None:
    """
    This function is intentionally used only after an IntegrityError. It is not
    a pre-insert duplicate check.
    """
    result = await db.execute(
        select(WorkerTask)
        .where(
            WorkerTask.repoId == repo_id,
            WorkerTask.taskTypeId == task_type.value,
        )
        .order_by(WorkerTask.createdAt.desc())
        .limit(1)
    )
    return result.scalars().first()


async def _insert_task_or_get_existing(
    db,
    *,
    repo_id: str,
    task_type: TaskType,
    started_at: datetime,
) -> tuple[WorkerTask, bool]:
    """
    Atomically create a WorkerTask.

    Returns (task, created).
    - created=True means this worker owns the work and should execute it.
    - created=False means the task already exists and this worker must exit.
    """
    task = WorkerTask(
        id=str(uuid.uuid4()),
        repoId=repo_id,
        taskTypeId=task_type.value,
        statusId=TaskStatus.RUNNING.value,
        startedAt=started_at,
        attempts=1,
    )
    db.add(task)

    try:
        await db.commit()
        await db.refresh(task)
        return task, True
    except IntegrityError:
        await db.rollback()
        existing_task = await _get_existing_task(db, repo_id=repo_id, task_type=task_type)
        if existing_task is None:
            raise
        return existing_task, False


async def clone_repo_task(ctx, *, user_id: str, github_url: str) -> dict:
    """
    Clone a repository and queue parsing.

    Idempotency rule:
    the clone task row is inserted before cloning starts. If the row already
    exists, PostgreSQL raises IntegrityError and this worker returns the
    existing task instead of cloning again.
    """
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:
        metadata, owner, repo_name = await extract_repo_info(github_url)

        repo = await save_repo(user_id, metadata, db)
        repo_id = repo.id

        task_row, created = await _insert_task_or_get_existing(
            db,
            repo_id=repo_id,
            task_type=TaskType.CLONE,
            started_at=started_at,
        )
        if not created:
            return {
                "repo_id": repo_id,
                "task_id": task_row.id,
                "status": "already_exists",
            }

        try:
            clone_result = clone_repo(owner, repo_name, github_url)
            clone_path = clone_result["clone_path"]
            file_count = len(clone_result["files"])
            files = clone_result["files"]


            completed_at = datetime.now(timezone.utc)
            result = {
                "clone_path": clone_path,
                "folders": len(clone_result["folders"])
            }
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(statusId=RepoStatus.INDEXED.value)
            )
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_row.id)
                .values(statusId=TaskStatus.SUCCESS.value, completedAt=completed_at, result=result)
            )
            await db.commit()

            parse_job = await ctx["redis"].enqueue_job(
                "parse_repo_task",
                repo_id=repo_id,
                files=files,
            )

            return {
                "repo_id": repo_id,
                "parse_job_id": parse_job.job_id if parse_job else None,
                "clone_path": clone_path,
                "files_accepted": file_count,
                "files": files
            }

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(statusId=RepoStatus.FAILED.value)
            )
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_row.id)
                .values(
                    statusId=TaskStatus.FAILED.value,
                    completedAt=completed_at,
                    errorType=type(exc).__name__,
                    errorMessage=str(exc),
                )
            )
            await db.commit()
            raise



async def parse_repo_task(ctx, *, repo_id: str, files: list[dict]) -> dict:
    """
    Parse cloned repository files.
    """
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:
        task_row, created = await _insert_task_or_get_existing(
            db,
            repo_id=repo_id,
            task_type=TaskType.PARSING,
            started_at=started_at,
        )
        if not created:
            return {
                "repo_id": repo_id,
                "task_id": task_row.id,
                "status": "already_exists",
            }

        try:
            ast_tree = parse_repo(files)
            completed_at = datetime.now(timezone.utc)
            result = {
                "files_parsed": len(ast_tree),
            }
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_row.id)
                .values(statusId=TaskStatus.SUCCESS.value, completedAt=completed_at, result=result)
            )
            await db.commit()

            return {
                "repo_id": repo_id,
                "files_parsed": len(ast_tree),
                "ast_tree": ast_tree,
            }
        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_row.id)
                .values(
                    statusId=TaskStatus.FAILED.value,
                    completedAt=completed_at,
                    errorType=type(exc).__name__,
                    errorMessage=str(exc),
                )
            )
            await db.commit()
            raise

        

        
    

    
