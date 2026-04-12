from app.models.webhook import webhook
from app.models.db import get_db




async def savedb(db, data :dict):
    db_event = webhook(
        clerkId = data["data"].get("id" , ""),
        type = data["type"],
        playload = data
    )
    db.add(db_event)
    await db.commit()


async def check_event_exists(db , event_id):
    exist = await db.get(webhook , event_id)
    return exist is not None