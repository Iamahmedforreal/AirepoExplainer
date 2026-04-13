import json
import os
from fastapi import APIRouter, Depends, Request, HTTPException 
from dotenv import load_dotenv
from svix.webhooks import Webhook , WebhookVerificationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from app.models.webhook import webhook as WebhookEvent
from app.services.clerk_webhook import save_webhook_event 
from app.services.task import process_webhook_event
from app.services.clerk_webhook import check_event_exists


load_dotenv()

router = APIRouter()



@router.post("/clerk-webhook")
async def handle_clerk_webhook(request: Request , db: AsyncSession = Depends(get_db)):
    #extract header and playload

    
    body = await request.body()
    payload = body.decode("utf-8")
    header  = dict(request.headers)
    CLERK_SECRET_KEY = os.getenv("CLERK_WEBHOOK_SECRET")
    if not CLERK_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Clerk webhook secret not configured")
    
    print(event)

    
    #check if the webhook is from clerk
    try:
        wh = Webhook(CLERK_SECRET_KEY)
        event = wh.verify(payload, header)
        data = json.loads(payload)        
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    
    
    Clerk_event_id = data.get("id") or header["svix-id"]
    event_type = data.get("type")
   
    if await check_event_exists(db , Clerk_event_id):
        raise HTTPException(status_code=400, detail="Event already processed")
    
    #save the event to the database
    await save_webhook_event(db , Clerk_event_id ,event_type ,  data)
    
    #process the event asynchronously  using celery
    process_webhook_event.delay(Clerk_event_id)

    return{"status":"queued"}


