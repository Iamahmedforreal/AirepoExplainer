from app.models.webhook import WebhookEvent
from app.models.db import get_db

# function to save the webhookevent to the database
async def save_webhook_event(db, data :dict , type:str , event_id:str): 
    db_event = WebhookEvent(
        clerk_id = event_id,
        type = type,
        payload = data
    )
    db.add(db_event)
    await db.commit()

#check if the event already exists in the database
async def check_event_exists(db , event_id):
    exist = await db.get(WebhookEvent , event_id)
    return exist is not None