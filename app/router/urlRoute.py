
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from app.schema.urlSchema import TrustedGitHubRepoLink
from app.services.urlService import (
    check_existing_repo,
    extract_repo_info,
    fetch_repo_tree,
    save_repo,
)
from app.utils.utils import authenticate_and_get_user_id


router = APIRouter(prefix="/api", tags=["repositories"])


@router.post("/repos")
async def submitting_url(
    request: Request,
    payload: TrustedGitHubRepoLink,
    db: AsyncSession = Depends(get_db),
):
    try:
        user_details = authenticate_and_get_user_id(request)
        user_id = user_details.get("user_id")

        metadata, owner, repo_name = await extract_repo_info(str(payload.url))

        existing_repo = await check_existing_repo(user_id, metadata.get("githubUrl"), db)
        if existing_repo:
            return {"message": "Repository already indexed"}

        await save_repo(user_id, metadata, db)

        # Fetch the full file tree via GitHub Trees API (no cloning)
        branch = metadata.get("defaultBranch", "main")
        tree_data = await fetch_repo_tree(owner, repo_name, branch)

        return {
            "message": "Repository indexed successfully",
            "tree": tree_data,
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))