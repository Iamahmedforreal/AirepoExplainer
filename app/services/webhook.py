import logging
from sqlalchemy.exc import SQLAlchemyError 
from app.models.repo_models import User
from sqlalchemy import  select 
from sqlalchemy.dialects.postgresql import insert
from app.models.repo_models import WebhookEvent
from datetime import datetime, timezone


logger = logging.getLogger(__name__)

async def create_new_user(user_id: str, db) -> None:
    """this function creates a new user in the database if they don't already exist."""
    try:
        stmt = insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=["id"])
        await db.execute(stmt)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[create_new_user] Failed to create user: %s", e, exc_info=True)
        raise

#function for checking webhook duplicate
async def is_duplicate_webhook(svix_id: str, db) -> bool:
    result = await db.execute(
        select(WebhookEvent).where(WebhookEvent.id == svix_id)
    )
    return result.scalar_one_or_none() is not None

async def save_webhook_event(svix_id: str,event_type: str,payload: dict,db) -> WebhookEvent:
    """
    saving incoming webhook events to the database with status "pending".
    """
    try:
        event = WebhookEvent(
            id=svix_id,
            eventType=event_type,
            status="pending",       
            payload=payload,
            repoId=None,           
            processedAt=None,      
            errorMessage=None,     
        )

        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(
            "[save_webhook_event] Failed to persist event %s: %s",
            svix_id, e,
            exc_info=True
        )
        raise
async def mark_webhook_processed( svix_id: str,   repo_id: str | None,db) -> None:
    """
    Mark a webhook event as successfully processed.
    Sets repoId so the event is linked to the repository it affected.
    """
    

    try:
        result = await db.execute(
            select(WebhookEvent).where(WebhookEvent.id == svix_id)
        )
        event = result.scalars().first()
        if not event:
            return

        event.status      = "processed"
        event.repoId      = repo_id
        event.processedAt = datetime.now(timezone.utc)

        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(
            "[mark_webhook_processed] Failed to update event %s: %s",
            svix_id, e,
            exc_info=True
        )
        raise


async def mark_webhook_failed(svix_id: str,error: str,db) -> None:
    """
    Mark a webhook event as failed and store the error reason.
    Allows failed events to be identified and replayed later.
    """
    

    try:
        result = await db.execute(
            select(WebhookEvent).where(WebhookEvent.id == svix_id)
        )
        event = result.scalars().first()
        if not event:
            return

        event.status       = "failed"
        event.errorMessage = error
        event.processedAt  = datetime.now(timezone.utc)

        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(
            "[mark_webhook_failed] Failed to update event %s: %s",
            svix_id, e,
            exc_info=True
        )
        raise
  

   
