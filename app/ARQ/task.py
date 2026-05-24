"""
ARQ background tasks for repository indexing.
"""
import asyncio
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
from app.services.urlService import extract_repo_info, save_repo
from app.services.clone_service import clone_repo, load_files_from_clone
from app.services.code_store import persist_extraction
from app.services.code_graph.neo4j_client import write_repo_graph


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


async def clone_repo_task(ctx, *, user_id: str, github_url: str) -> dict:
    """Clone repo to disk and queue parsing."""
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
            return {"repo_id": repo_id, "task_id": task_row.id, "status": "already_exists"}

        try:
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(statusId=RepoStatus.INDEXING.value)
            )
            await db.commit()

            clone_result = clone_repo(owner, repo_name, github_url)
            clone_path = clone_result["clone_path"]
            file_count = len(clone_result["files"])

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

            parse_job = await ctx["redis"].enqueue_job(
                "parse_repo_task",
                repo_id=repo_id,
                clone_path=clone_path,
            )

            return {
                "repo_id": repo_id,
                "parse_job_id": parse_job.job_id if parse_job else None,
                "clone_path": clone_path,
                "files_accepted": file_count,
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


async def parse_repo_task(ctx, *, repo_id: str, clone_path: str) -> dict:
    """Read files from disk clone, extract AST symbols, store connections in Postgres + Neo4j."""
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:
        task_row, created = await _insert_task_or_get_existing(
            db,
            repo_id=repo_id,
            task_type=TaskType.PARSING,
            started_at=started_at,
        )
        if not created:
            return {"repo_id": repo_id, "task_id": task_row.id, "status": "already_exists"}

        try:
            files = load_files_from_clone(clone_path)
            summary = await persist_extraction(db, repo_id, files)

            await asyncio.to_thread(
                write_repo_graph,
                repo_id,
                files,
                summary["chunk_payloads"],
                summary["connection_payloads"],
            )

            completed_at = datetime.now(timezone.utc)
            result = {
                "files_extracted": summary["files_extracted"],
                "chunks_created": summary["chunks_created"],
                "connections_created": summary["connections_created"],
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

            return {"repo_id": repo_id, **result}

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
