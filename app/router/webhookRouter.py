from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from models.db import get_db
from svix.webhooks import Webhook
import os
from dotenv import load_dotenv
from services.webhook import create_new_user

load_dotenv()

router = APIRouter()  


@router.post("/webhooks/clerk")  # fix 2 — added leading slash
async def webhook_function(request: Request, db: AsyncSession = Depends(get_db)):
    
    # check secret exists
    webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="CLERK_WEBHOOK_SECRET is not set"
        )

  
    payload = await request.body()
    headers = dict(request.headers)

    # verify the webhook signature
    try:
        wh = Webhook(webhook_secret)
        event = wh.verify(payload, headers)
    except Exception as error:
        raise HTTPException(status_code=401, detail=str(error))

    # ignore events that are not user.created
    if event.get("type") != "user.created":
        return {"status": "ignored"}  # fix 3 — colon not comma

    user_id = event.get("data", {}).get("id")

    
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract user id from webhook event"
        )

    await create_new_user(user_id, db)
    return {"status": "success"}  