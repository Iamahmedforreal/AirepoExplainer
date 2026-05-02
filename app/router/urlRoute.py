import os
import time
from fastapi import APIRouter, Depends, HTTPException, Request  , BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.app_config import settings
from app.models.db import get_db
from app.schema.urlSchema import TrustedGitHubRepoLink
from app.services.urlService import check_existing_repo, extract_repo_info, save_repo , clone_repository
from app.utils.utils import authenticate_and_get_user_id


router = APIRouter(prefix="/api", tags=["repositories"])


@router.post("/repos")
async def submitting_url(
    request: Request,
    payload: TrustedGitHubRepoLink,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    try:
        t = time.perf_counter()
    
        user_details = authenticate_and_get_user_id(request)
        print(f"Authentication took{(time.perf_counter()-t)*1000:.0f}ms")
        t = time.perf_counter()
        user_id = user_details.get("user_id")

       
        metadata, owner, repo_name = await extract_repo_info(str(payload.url))
        print(f"Metadata extraction took {(time.perf_counter()-t)*1000:.0f}ms")
        t = time.perf_counter()
        
        
        existing_repo = await check_existing_repo(user_id, metadata.get("githubUrl"), db)
        print(f"Existing repo check took {(time.perf_counter()-t)*1000:.0f}ms")
        t = time.perf_counter()
        if existing_repo:
            return {"message": "Repository already indexed"}
        
        await save_repo(user_id, metadata, db)
        
              
        local_path = os.path.join(settings.clone_base_dir, f"{owner}_{repo_name}")
        github_url = metadata.get("githubUrl")
        start = time.time()
        background_tasks.add_task(clone_repository, github_url, local_path)
        print("CELERY DELAY TIME:", (time.time() - start) * 1000, "ms")
       
    

        return {"message": "Repository indexed successfully"}

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))