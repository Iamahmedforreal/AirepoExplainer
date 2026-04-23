import logging

from requests import session
import uuid
from sqlalchemy.exc import SQLAlchemyError 
from app.models.users import User
from sqlalchemy import  exists, select 
from sqlalchemy.dialects.postgresql import insert
from app.models.users import WebhookEvent


logger = logging.getLogger(__name__)

async def create_new_user(user_id: str, db) -> None:
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

async def save_webhook_events(svix_id , event , db):
    try:
        db.add(WebhookEvent(id=svix_id , payload=event))
        await db.commit()
     
    except SQLAlchemyError as e:
       await db.rollback()
       logger.error("[save_webhook_events] Failed to save webhook event: %s", e, exc_info=True)
       raise  
        
  

   
