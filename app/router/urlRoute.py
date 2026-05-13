from fastapi import APIRouter, HTTPException, Request
from app.schema.urlSchema import TrustedGitHubRepoLink
from app.utils.utils import authenticate_and_get_user_id

router = APIRouter(prefix="/api", tags=["repositories"])


@router.post("/repos", status_code=201)
async def submit_repo(request: Request, payload: TrustedGitHubRepoLink):
    """Validate the URL and enqueue an indexing job. Returns 201 immediately.
    """
    user = authenticate_and_get_user_id(request)

    await request.app.state.redis.enqueue_job(
        "index_repo",
        user_id=user["user_id"],
        github_url=str(payload.url),
    )

    return {"status": "queued", "message": "Repository queued for indexing"}