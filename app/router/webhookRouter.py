from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook
import logging

from app.config.app_config import settings
from app.models.db import get_db
from app.services.webhook import (
    create_new_user,
    is_duplicate_webhook,
    save_webhook_event,
    mark_webhook_processed,
    mark_webhook_failed,
)

logger = logging.getLogger(__name__)

router_webhook = APIRouter()


@router_webhook.post("/webhooks/clerk")
async def webhook_function(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Ingestion endpoint for Clerk user lifecycle webhooks.
    This endpoint is designed to receive webhooks from Clerk related to user lifecycle events (e.g., user.created).
    """

    webhook_secret = settings.clerk_webhook_secret
    if not webhook_secret:
        logger.error("CLERK_WEBHOOK_SECRET is not configured")
        raise HTTPException(status_code=500, detail="CLERK_WEBHOOK_SECRET is not set")

    # verify signature
    try:
        payload = await request.body()
        headers = dict(request.headers)
        wh      = Webhook(webhook_secret)
        event   = wh.verify(payload, headers)
        logger.debug("Webhook signature verified successfully")
    except Exception as error:
        logger.error("Webhook verification failed: %s", error, exc_info=True)
        raise HTTPException(status_code=401, detail=f"Webhook verification failed: {error}")

    # svix-id is required — used as idempotency key and DB primary key
    svix_id = request.headers.get("svix-id")
    if not svix_id:
        raise HTTPException(status_code=400, detail="Missing svix-id header")

    # deduplicate — Svix may deliver the same event more than once
    if await is_duplicate_webhook(svix_id, db):
        logger.info("Duplicate webhook ignored: %s", svix_id)
        return {"status": "duplicate ignored"}

    event_type = event.get("type")

    
    await save_webhook_event(svix_id, event_type, event, db)

    # only user.created is handled — all other types are acknowledged and ignored
    if event_type != "user.created":
        logger.info("Ignoring webhook event type: %s", event_type)
        await mark_webhook_processed(svix_id, repo_id=None, db=db)
        return {"status": "ignored"}

    # extract the Clerk user id from the event payload
    user_id = event.get("data", {}).get("id")
    if not user_id:
        error_msg = "Could not extract user id from webhook event payload"
        logger.error("%s: %s", error_msg, event)
        await mark_webhook_failed(svix_id, error_msg, db)
        raise HTTPException(status_code=400, detail=error_msg)

    # create the user record
    try:
        await create_new_user(user_id, db)
        await mark_webhook_processed(svix_id, repo_id=None, db=db)
        logger.info("User created successfully: %s", user_id)
        return {"status": "success"}

    except ValueError as error:
        logger.warning("ValueError creating user %s: %s", user_id, error)
        await mark_webhook_failed(svix_id, str(error), db)
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        logger.error("Failed to create user %s: %s", user_id, error, exc_info=True)
        await mark_webhook_failed(svix_id, str(error), db)
        raise HTTPException(status_code=500, detail=f"Internal server error: {error}")