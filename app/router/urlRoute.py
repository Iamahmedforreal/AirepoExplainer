from fastapi import APIRouter, Depends, HTTPException, Request
from app.schema.urlSchema import TrustedGitHubRepoLink
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from app.services.urlService import extract_repo_info, save_repo
from app.utils.utils import verify_token

router= APIRouter(prefix="/api", tags=["repositories"])

@router.post("/repos")
async def submitting_url(
    request: Request,
    payload: TrustedGitHubRepoLink,
    db: AsyncSession = Depends(get_db),
    token_payload = Depends(verify_token)
):
    try:

        user_id = token_payload.get("user_id")
        metadata = await extract_repo_info(payload.url)
        result = await save_repo(user_id, metadata, db)
        return {"message": "Repository indexed successfully", "data": result}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

        