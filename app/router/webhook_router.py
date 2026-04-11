import os
from fastapi import APIRouter, Depends, Request, HTTPException , AssyncSession
from dotenv import load_dotenv
from svix.webhooks import Webhook , WebhookVerificationError
from app.models.db import get_db
from services.clerk_webhook import savedb
from services.task import process_webhook_event


load_dotenv()

router = APIRouter()

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

@router.post("/clerk-webhook")
async def handle_clerk_webhook(request: Request , db: AssyncSession = Depends(get_db)):
    #extract header and playload
    playload = await request.body()
    header  = dict(request.headers)

    #check if the webhook is from clerk
    try:
        wh = Webhook(CLERK_SECRET_KEY)
        event = wh.verify(playload, header)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    

    clerk_event_id = event["id"]
    exist = await db.get(Webhook , clerk_event_id)
    if exist:
        raise HTTPException(status_code=400, detail="Event already exists")
    
    #save the event to the database
    saved_db = await savedb(db , event)
    if not saved_db:
        raise HTTPException(status_code=500, detail="Failed to save event to database")
    
    #process the event asynchronously  using celery
    process_webhook_event.delay(clerk_event_id)



    return{"status":"queued"}
    

