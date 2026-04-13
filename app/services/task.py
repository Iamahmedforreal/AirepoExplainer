from datetime import datetime

from celery import Celery
from sqlalchemy import select 
from app.database import SyncSession
from app.models.webhook import webhook as WebhookEvent
from app.models.users import User

celery = Celery("celery_tasks" , broker="redis://localhost:6379/0")

@celery.task(bind=True, max_retries=3)
def process_webhook_event(self , event_id):
    with SyncSession() as db:
        event = db.get(WebhookEvent , event_id)
        if not event:
            return 
        

        try:
            if event.type == "user.created":
                _handle_user_created(event , db)
            if event.type == "user.updated":
                _handle_user_updated(event , db)
            if event.type == "user.deleted":
                _handle_user_deleted(event , db)
        except Exception as error:
            db.rollback()
            raise self.retry(exc=error , countdown=60)
    


def _handle_user_created(db, data: dict):
    # check if user already exists
    existing = db.execute(
        select(User).where(User.clerk_id == data["id"])
    ).scalar_one_or_none()
    
    if existing:
        return

    user = User(
        clerk_id=data["id"],
        email=data["email_addresses"][0]["email_address"],
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        username=data.get("username"),
    )
    db.add(user)
    db.commit()


def _handle_user_updated(event:list , db):
    exisiting_user = db.execute(
        select(User).where(User.clerk_id == event["id"])
    ).scalar_one_or_none()

    if exisiting_user:
        exisiting_user.email = event["email_addresses"][0]["email_address"]
        exisiting_user.first_name = event.get("first_name")
        exisiting_user.last_name = event.get("last_name")
        exisiting_user.username = event.get("username")
        db.commit()


def _handle_user_deleted(event , db):
    user = db.execute(
        select(User).where(User.clerk_id == event["id"]).scalar_one_or_none()
    )
    if user:
        user.deletedAt = datetime.utcnow()
        db.delete(user)
        db.commit()
