from os import sync

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.models.db import get_db
from app.services.webhook import (
    create_new_user,
    is_duplicate_webhook,
    save_webhook_event,
    mark_webhook_processed,
    verify_webhook_signature,
    fail_safely
)

logger = logging.getLogger(__name__)

router_webhook = APIRouter()
EVENT_HANDLERS= {
    "user.created": create_new_user,
}

@router_webhook.post("/webhooks/clerk")
async def webhook_function(request: Request, db: AsyncSession = Depends(get_db)):
    """Ingestion endpoint for Clerk user lifecycle webhooks (e.g. user.created)."""
 
    event = await verify_webhook_signature(request)
 
    svix_id = request.headers.get("svix-id")
    if not svix_id:
        raise HTTPException(status_code=400, detail="Missing svix-id header")
 
    if await is_duplicate_webhook(svix_id, db):
        logger.info("Duplicate webhook ignored: %s", svix_id)
        return {"status": "duplicate ignored"}
 
    event_type = event.get("type")
    await save_webhook_event(svix_id, event_type, event, db)
 
    handler = EVENT_HANDLERS.get(event_type)
    if handler is None:
        logger.info("Ignoring unhandled webhook event type: %s", event_type)
        await mark_webhook_processed(svix_id, repo_id=None, db=db)
        return {"status": "ignored"}
 
    user_id = event.get("data", {}).get("id")
    if not user_id:
        error_msg = "Could not extract user id from webhook event payload"
        logger.error("%s: %s", error_msg, event)
        await fail_safely(svix_id, error_msg, db)
        raise HTTPException(status_code=400, detail=error_msg)
 
    try:
        await handler(user_id, db)
    except Exception as e:
        logger.exception("Handler failed for event %s (user %s)", event_type, user_id)
        await fail_safely(svix_id, str(e), db)
        raise HTTPException(status_code=500, detail="Internal server error")
 
    await mark_webhook_processed(svix_id, repo_id=None, db=db)
    logger.info("Event %s processed successfully for user %s", event_type, user_id)
    return {"status": "success"}