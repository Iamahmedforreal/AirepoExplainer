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
    CodeChunk,
)
from app.services.urlService import (
    extract_repo_info,
    check_existing_repo,
    save_repo,
    collect_clean_repo,
    read_file_contents,
)
from app.services.clone_service import clone_repo
from app.services.tree_sitter_parser import detect_language
from app.services.chunk import chunk_source_code


async def clone_repo_task(ctx, *, user_id: str, github_url: str) -> dict:
    """
    ARQ Background Task: Phase 1 - Repository Cloning.
    """
    task_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:
        # 1. Fetch metadata from GitHub
        metadata, owner, repo_name = await extract_repo_info(github_url)

        # 2. Duplicate check
        existing = await check_existing_repo(user_id, metadata["githubUrl"], db)
        if existing:
            raise HTTPException(status_code=400, detail="Repository already exists")

        # 3. Save repo row (starts in PENDING)
        repo = await save_repo(user_id, metadata, db)
        repo_id = repo.id

        # Audit row
        task_row = WorkerTask(
            id=task_id,
            repoId=repo_id,
            taskTypeId=TaskType.CLONE,
            statusId=TaskStatus.RUNNING,
            startedAt=started_at,
            attempts=1,
        )
        db.add(task_row)
        
        # Set repository status to INDEXING while we clone
        await db.execute(
            update(Repository)
            .where(Repository.id == repo_id)
            .values(statusId=RepoStatus.INDEXING)
        )
        await db.commit()

        try:
            clone_result = clone_repo(owner, repo_name, github_url)
            clone_path = clone_result["clone_path"]
            file_count = len(clone_result["files"])

            extracted_languages = extract_languages_from_clean_files(clone_result["files"])

            completed_at = datetime.now(timezone.utc)
            result = {
                "clone_path": clone_path,
                "folders": len(clone_result["folders"]),
                "extracted_languages": extracted_languages,
            }
            
            # Mark CLONE task as SUCCESS
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_id)
                .values(statusId=TaskStatus.SUCCESS, completedAt=completed_at, result=result)
            )
            await db.commit()

            # Enqueue Phase 2: parse_repo_task
            await ctx["redis"].enqueue_job(
                "parse_repo_task",
                repo_id=repo_id,
                clone_path=clone_path,
            )

            return {
                "repo_id": repo_id,
                "clone_path": clone_path,
                "files_accepted": file_count,
                "languages": extracted_languages,
                "status": "cloned_and_parsing_queued"
            }

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(statusId=RepoStatus.FAILED)
            )
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_id)
                .values(
                    statusId=TaskStatus.FAILED,
                    completedAt=completed_at,
                    errorType=type(exc).__name__,
                    errorMessage=str(exc),
                )
            )
            await db.commit()
            raise


async def parse_repo_task(ctx, *, repo_id: str, clone_path: str) -> dict:
    """
    ARQ Background Task: Phase 2 - AST Structural Parsing.
    """
    task_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    async with async_session() as db:
        # Create WorkerTask row for PARSING
        task_row = WorkerTask(
            id=task_id,
            repoId=repo_id,
            taskTypeId=TaskType.PARSING,
            statusId=TaskStatus.RUNNING,
            startedAt=started_at,
            attempts=1,
        )
        db.add(task_row)
        await db.commit()

        try:
            # 1. Read cloned files
            clean = collect_clean_repo(clone_path)
            file_contents = read_file_contents(clean["files"])

            # 2. Parse each file into AST chunks
            all_chunks = []
            for file_item in file_contents:
                lang = detect_language(file_item["path"])
                if lang:
                    file_chunks = chunk_source_code(file_item["content"], file_item["path"], lang)
                    all_chunks.extend(file_chunks)

            # 3. Resolve parent relationships in memory
            for c in all_chunks:
                if "id" not in c:
                    c["id"] = str(uuid.uuid4())
                
                # Check enclosing class
                if c.get("parent") and c["type"] in ("method", "function", "class"):
                    parent_id = None
                    for other in all_chunks:
                        if other["path"] == c["path"] and other["type"] == "class" and other["name"] == c["parent"]:
                            if "id" not in other:
                                other["id"] = str(uuid.uuid4())
                            parent_id = other["id"]
                            break
                    c["parentChunkId"] = parent_id
                else:
                    c["parentChunkId"] = None

            # 4. Save chunks to the database
            db_chunks = []
            for c in all_chunks:
                # Resolve fullName
                path = c["path"].replace("\\", "/")
                name = c["name"]
                if c["type"] == "module":
                    full_name = path
                elif c["parent"]:
                    full_name = f"{path}::{c['parent']}.{name}"
                else:
                    full_name = f"{path}::{name}"

                db_chunks.append(
                    CodeChunk(
                        id=c["id"],
                        repoId=repo_id,
                        path=path,
                        type=c["type"],
                        name=name,
                        fullName=full_name,
                        startLine=c["start_line"],
                        endLine=c["end_line"],
                        content=c["content"],
                        parentChunkId=c["parentChunkId"]
                    )
                )

            db.add_all(db_chunks)
            await db.flush()

            # Mark SUCCESS
            completed_at = datetime.now(timezone.utc)
            result = {
                "chunks_count": len(db_chunks)
            }
            
            # Set repository status to INDEXED
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(statusId=RepoStatus.INDEXED)
            )
            # Set task status to SUCCESS
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_id)
                .values(statusId=TaskStatus.SUCCESS, completedAt=completed_at, result=result)
            )
            await db.commit()

            return {
                "repo_id": repo_id,
                "status": "indexed",
                "chunks_created": len(db_chunks)
            }

        except Exception as exc:
            completed_at = datetime.now(timezone.utc)
            await db.execute(
                update(Repository)
                .where(Repository.id == repo_id)
                .values(statusId=RepoStatus.FAILED)
            )
            await db.execute(
                update(WorkerTask)
                .where(WorkerTask.id == task_id)
                .values(
                    statusId=TaskStatus.FAILED,
                    completedAt=completed_at,
                    errorType=type(exc).__name__,
                    errorMessage=str(exc),
                )
            )
            await db.commit()
            raise
