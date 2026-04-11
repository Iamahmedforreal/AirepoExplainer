from models import webhook
from models import users
from app.models.db import get_db




async def savedb(db, data :dict):
    db_event = webhook(
        id = data["id"],
        clerkId = data["data"].get("id" , ""),
        type = data["type"],
        playload = data
    )
    db.add(db_event)
    await db.commit()
    