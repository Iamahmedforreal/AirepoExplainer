from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import get_db
from app.schema.urlSchema import TrustedGitHubRepoLink
from app.services.urlService import check_existing_repo, extract_repo_info, save_repo
from app.utils.utils import authenticate_and_get_user_id

router = APIRouter(prefix="/api", tags=["repositories"])


@router.post("/repos", status_code=201)
async def submitting_url(
    request: Request,
    payload: TrustedGitHubRepoLink,
    db: AsyncSession = Depends(get_db),
):
    """Submit a GitHub repository URL for background indexing.

    Saves the repository record and immediately returns 201.
    Tree fetching, filtering, and content downloading all run in
    the ARQ background worker — nothing slow happens in this request.
    """
    try:
        user_details = authenticate_and_get_user_id(request)
        user_id = user_details.get("user_id")

        # Single GitHub API call to pull repo metadata 
        metadata, owner, repo_name = await extract_repo_info(str(payload.url))

        # Reject duplicates before writing anything
        existing = await check_existing_repo(user_id, metadata.get("githubUrl"), db)
        if existing:
            raise HTTPException(status_code=400, detail="Repository already indexed")

        # Persist the repo row — status starts as PENDING
        repo = await save_repo(user_id, metadata, db)

        # Hand off everything else to the background worker
        await request.app.state.redis.enqueue_job(
            "fetch_repo_content",
            repo_id=repo.id,
            owner=owner,
            repo_name=repo_name,
            branch=metadata.get("defaultBranch", "main"),
        )

        # Return immediately — worker handles tree + clean + content fetch
        return {
            "repo_id": repo.id,
            "status":  "PENDING",
            "message": "Repository queued for indexing",
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))