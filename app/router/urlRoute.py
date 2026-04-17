from fastapi import APIRouter , Depends , HTTPException
from app.schema import TrustedGitHubRepoLink
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from app.services.urlService import extract_repo_info , save_metadata_to_db



route = APIRouter

@route.post("/repos")
async def submitting_url(payload:TrustedGitHubRepoLink ,db:AsyncSession = Depends(get_db)):
    try:
        metadata = await extract_repo_info(payload.url)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    
    await save_metadata_to_db(metadata , db)
    
    return {"message": "Repository indexed successfully"}

        