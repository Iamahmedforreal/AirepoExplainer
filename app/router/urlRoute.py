from fastapi import APIRouter, Depends, HTTPException, Request
from app.schema.urlSchema import TrustedGitHubRepoLink
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from app.services.urlService import extract_repo_info, save_repo
from app.utils.utils import authenticate_and_get_user_id

router= APIRouter(prefix="/api", tags=["repositories"])

@router.post("/repos")
async def submitting_url(
    request: Request,
    payload: TrustedGitHubRepoLink,
    db: AsyncSession = Depends(get_db),
):
    try:

        user_id = "b376575f-4e94-4ec8-a3b3-ed3f1bf12e1c"
        metadata = await extract_repo_info(str(payload.url))
        result = await save_repo(user_id, metadata, db)
        return {"message": "Repository indexed successfully", "data": result}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

        