import json
import os
import logging
from fastapi import APIRouter, Depends, Request, HTTPException 
from dotenv import load_dotenv
from svix.webhooks import Webhook , WebhookVerificationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from app.services.clerk_webhook import save_webhook_event 
from app.services.task import process_webhook_event
from app.services.clerk_webhook import check_event_exists


logger = logging.getLogger(__name__)
load_dotenv()

router = APIRouter()

CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")

@router.post("/webhooks/clerk")
async def handle_clerk_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    header = dict(request.headers)

  
    if not CLERK_WEBHOOK_SECRET:
        raise RuntimeError("CLERK_WEBHOOK_SECRET is not set")

    try:
        wh = Webhook(CLERK_WEBHOOK_SECRET)
        event = wh.verify(payload, header)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    
    event_id = header.get("svix-id")
    event_type = event.get("type")
    event_data = event.get("data" , {})
    
    if await check_event_exists(db, event_id):
        return {"status": "duplicate"}
    
    await save_webhook_event(db, event_data, event_type, event_id)

    # Enqueue the task to process the webhook event asynchronously
    process_webhook_event.delay(event_id)
       
    return {"status": "success"}
