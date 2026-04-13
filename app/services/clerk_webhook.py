from app.models.webhook import webhook
from app.models.db import get_db

# function to save the webhookevent to the database
async def save_webhook_event(db, data :dict , type:str , event_id:str): 
    db_event = webhook(
        clerkId = event_id,
        type = type,
        playload = data
    )
    db.add(db_event)
    await db.commit()

#check if the event already exists in the database
async def check_event_exists(db , event_id):
    exist = await db.get(webhook , event_id)
    return exist is not None