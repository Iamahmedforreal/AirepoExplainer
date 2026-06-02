"""
ARQ background tasks for repository indexing.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.models.db import async_session
from app.models.repo_models import (
    TaskStatus,
    TaskType,
    WorkerTask,
)
from app.services.urlService import extract_repo_info
from app.services.clone_service import clone_repo, load_files_from_clone
from app.services.code_store import persist_extraction
from app.services.repo_metadata import (
    get_repo_for_worker,
    apply_github_metadata,
    mark_clone_complete,
    mark_indexed,
    mark_failed,
)


async def _get_existing_task(db, *, repo_id: str, task_type: TaskType) -> WorkerTask | None:
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


async def clone_repo_task(ctx, *, repo_id: str) -> dict:
    """Clone repo to disk using metadata on the Repository row; queue parsing."""
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:
        repo = await get_repo_for_worker(db, repo_id)

        task_row, created = await _insert_task_or_get_existing(
            db,
            repo_id=repo_id,
            task_type=TaskType.CLONE,
            started_at=started_at,
        )
        if not created:
            return {"repo_id": repo_id, "task_id": task_row.id, "status": "already_exists"}

        try:
            metadata, _, _ = await extract_repo_info(repo.githubUrl)
            await apply_github_metadata(db, repo, metadata)

            clone_result = clone_repo(repo.repoOwner, repo.repoName, repo.githubUrl)
            clone_path = clone_result["clone_path"]
            file_count = len(clone_result["files"])

            await mark_clone_complete(
                db,
                repo,
                clone_path=clone_path,
                source_file_count=file_count,
            )

            completed_at = datetime.now(timezone.utc)
            result = {
                "clone_path": clone_path,
                "folders": len(clone_result["folders"]),
                "files_accepted": file_count,
            }

            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_row.id)
                .values(statusId=TaskStatus.SUCCESS.value, completedAt=completed_at, result=result)
            )
            await db.commit()

            parse_job = await ctx["redis"].enqueue_job("parse_repo_task", repo_id=repo_id)

            return {
                "repo_id": repo_id,
                "task_id": task_row.id,
                "parse_job_id": parse_job.job_id if parse_job else None,
                "files_accepted": file_count,
            }

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            await mark_failed(db, repo_id)
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


async def parse_repo_task(ctx, *, repo_id: str) -> dict:
    """Read clone from Repository.clonePath; extract symbols; store chunks + connections in Postgres."""
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:
        repo = await get_repo_for_worker(db, repo_id)

        task_row, created = await _insert_task_or_get_existing(
            db,
            repo_id=repo_id,
            task_type=TaskType.PARSING,
            started_at=started_at,
        )
        if not created:
            return {"repo_id": repo_id, "task_id": task_row.id, "status": "already_exists"}

        if not repo.clonePath:
            raise ValueError(f"Repository {repo_id} has no clonePath — run clone first")

        try:
            files = load_files_from_clone(repo.clonePath)
            summary = await persist_extraction(db, repo_id, files)

            await mark_indexed(
                db,
                repo,
                chunk_count=summary["chunks_created"],
                connection_count=summary["connections_created"],
            )

            completed_at = datetime.now(timezone.utc)
            result = {
                "files_extracted": summary["files_extracted"],
                "chunks_created": summary["chunks_created"],
                "connections_created": summary["connections_created"],
            }

            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_row.id)
                .values(statusId=TaskStatus.SUCCESS.value, completedAt=completed_at, result=result)
            )
            await db.commit()

            return {"repo_id": repo_id, **result}

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            await mark_failed(db, repo_id)
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
