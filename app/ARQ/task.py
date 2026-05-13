"""
task.py — ARQ background tasks.

index_repo pipeline:
    Priority 1 (sequential):
        - Fetch repo metadata from GitHub API
        - Duplicate check (reject if user already submitted this URL)
        - Save Repository row to DB (status = INDEXING)

    Priority 2 (runs after save, parallel-friendly across workers):
        - Fetch full recursive file tree from GitHub Trees API
        - Clean / filter the tree

Each task is fully self-contained so multiple ARQ workers can run
index_repo for different repos in parallel without sharing any state.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_, update

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
    fetch_repo_tree,
    clean_tree_data,
)

logger = logging.getLogger(__name__)


async def index_repo(ctx, *, user_id: str, github_url: str) -> dict:
    """Full indexing pipeline for one repository.

    Priority 1 — metadata + save (must complete before anything else):
        1. Fetch repo metadata from GitHub
        2. Reject duplicate submissions
        3. Save Repository row (status = INDEXING)

    Priority 2 — tree (runs after repo is saved):
        4. Fetch full recursive file tree
        5. Clean / filter tree

    Args:
        ctx:        ARQ context (reserved for future shared resources).
        user_id:    Clerk user ID from the JWT.
        github_url: Validated GitHub repository URL.

    Returns:
        { "repo_id", "total_items", "files_after_filter" }
    """
    task_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:

        # ── PRIORITY 1: metadata + save ───────────────────────────────────────

        logger.info("[%s] index_repo started — user=%s url=%s", task_id, user_id, github_url)

        # 1. Fetch metadata from GitHub
        metadata, owner, repo_name = await extract_repo_info(github_url)

        # 2. Duplicate check — skip silently if already submitted
        existing = await check_existing_repo(user_id, metadata["githubUrl"], db)
        if existing:
            logger.info(
                "[%s] Duplicate submission — repo %s already exists for user %s",
                task_id, github_url, user_id,
            )
            return {"status": "duplicate", "repo_id": existing.id}

        # 3. Save repo row (status = INDEXING from the start)
        repo = await save_repo(user_id, metadata, db)
        repo_id = repo.id

        # Attach a WorkerTask audit row now that we have a repo_id
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

        logger.info(
            "[%s] Repo saved — id=%s (%s/%s @ %s)",
            task_id, repo_id, owner, repo_name, metadata.get("defaultBranch"),
        )

        # ── PRIORITY 2: tree fetch + clean ────────────────────────────────────
        # Runs after the repo row exists. Multiple workers handle different
        # repos here in parallel — no shared state between tasks.

        try:
            # 4. Fetch full recursive tree
            branch = metadata.get("defaultBranch", "main")
            tree_data = await fetch_repo_tree(owner, repo_name, branch)
            total_items = tree_data["total_count"]
            logger.info("[%s] Tree fetched — %d items", task_id, total_items)

            # 5. Filter to source files only
            cleaned_tree = await clean_tree_data(tree_data["tree"])
            files_after_filter = len(cleaned_tree)
            logger.info("[%s] Tree cleaned — %d files kept", task_id, files_after_filter)

            # Mark repo indexed + record result
            completed_at = datetime.now(timezone.utc)
            result = {
                "total_items":        total_items,
                "files_after_filter": files_after_filter,
                "tree":               cleaned_tree,
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

            logger.info(
                "[%s] index_repo SUCCESS — %d/%d files kept",
                task_id, files_after_filter, total_items,
            )
            return {"repo_id": repo_id, "total_items": total_items, "files_after_filter": files_after_filter}

        except Exception as exc:
            logger.error("[%s] index_repo FAILED — %s", task_id, exc, exc_info=True)
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
