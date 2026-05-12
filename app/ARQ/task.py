"""
task.py — ARQ background tasks for the repository indexing pipeline.

Phase 1 (current): fetch_repo_content
    - Fetch the full recursive file tree from the GitHub Trees API
    - Filter out non-source files (clean_tree_data)
    - Store the cleaned tree in WorkerTask.result
    - Mark repo INDEXED

Content fetching and chunking are handled in later phases.
"""

import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import update
from app.models.db import async_session
from app.models.repo_models import (
    RepoStatus,
    Repository,
    TaskStatus,
    TaskType,
    WorkerTask,
)
from app.services.urlService import clean_tree_data, fetch_repo_tree

logger = logging.getLogger(__name__)


async def fetch_repo_content(
    ctx,
    *,
    repo_id: str,
    owner: str,
    repo_name: str,
    branch: str,
) -> dict:
    """Fetch and clean the repository file tree.

    Workflow:
        1. Create WorkerTask audit row
        2. Mark Repository.status → INDEXING
        3. Fetch full recursive tree via GitHub Trees API
        4. Filter out excluded dirs / extensions / dotfiles / empty files
        5. Mark Repository.status → INDEXED
        6. Update WorkerTask.status → SUCCESS, store cleaned tree in result

    Args:
        ctx:       ARQ context (reserved for future shared resources).
        repo_id:   Primary key of the Repository row.
        owner:     GitHub owner login.
        repo_name: Repository name (no .git suffix).
        branch:    Default branch (e.g. "main", "master").

    Returns:
        { "total_items": int, "files_after_filter": int, "tree": [...] }
    """
    task_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:

        # ── 1. Create WorkerTask audit row ────────────────────────────────────
        task_row = WorkerTask(
            id=task_id,
            repoId=repo_id,
            taskType=TaskType.FETCH_TREE,
            status=TaskStatus.RUNNING,
            startedAt=started_at,
            attempts=1,
        )
        db.add(task_row)

        # ── 2. Mark repository as INDEXING ────────────────────────────────────
        await db.execute(
            update(Repository)
            .where(Repository.id == repo_id)
            .values(status=RepoStatus.INDEXING)
        )
        await db.commit()

        logger.info(
            "[%s] fetch_repo_content started — repo=%s (%s/%s @ %s)",
            task_id, repo_id, owner, repo_name, branch,
        )

        try:
            # ── 3. Fetch full recursive file tree ─────────────────────────────
            tree_data = await fetch_repo_tree(owner, repo_name, branch)
            total_items = tree_data["total_count"]
            logger.info(
                "[%s] Tree fetched — %d total items (truncated=%s)",
                task_id, total_items, tree_data.get("truncated"),
            )

            # ── 4. Filter to source files only ────────────────────────────────
            cleaned_tree = await clean_tree_data(tree_data["tree"])
            files_after_filter = len(cleaned_tree)
            logger.info(
                "[%s] Tree cleaned — %d files remaining after filtering",
                task_id, files_after_filter,
            )

            # ── 5. Mark repository as INDEXED ─────────────────────────────────
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(status=RepoStatus.INDEXED)
            )

            # ── 6. Record success + store cleaned tree ────────────────────────
            completed_at = datetime.now(timezone.utc)
            result_summary = {
                "total_items":       total_items,
                "files_after_filter": files_after_filter,
                "tree":              cleaned_tree,
            }
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_id)
                .values(
                    status=TaskStatus.SUCCESS,
                    completedAt=completed_at,
                    result=result_summary,
                )
            )
            await db.commit()

            logger.info(
                "[%s] fetch_repo_content SUCCESS — %d/%d files kept",
                task_id, files_after_filter, total_items,
            )
            return result_summary

        except Exception as exc:
            # ── Failure path ──────────────────────────────────────────────────
            logger.error(
                "[%s] fetch_repo_content FAILED — repo=%s: %s",
                task_id, repo_id, exc, exc_info=True,
            )
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
            raise  # re-raise so ARQ marks the job as failed in Redis
