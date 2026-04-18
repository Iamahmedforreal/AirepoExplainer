from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from models.db import get_db
from svix.webhooks import Webhook
import os
from dotenv import load_dotenv
from services.webhook import create_new_user

load_dotenv()

router = APIRouter


@router.post("webhooks/clerk")
async def webhookFunction(request:Request , db:AsyncSession = Depends(get_db)):
    webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")

    if not webhook_secret:
        raise HTTPException(status_code=500 , detail="CLERK_WEBHOOK_SECRET is not set") 
    
    payload = await request.body()
    header = dict(request.headers)
    
    try:
        wh=Webhook(webhook_secret)
        event = wh.verify(payload , header)

        if event.get("type") != "user.created":
            return {"status":"ignored"}
        
        await create_new_user(event , db)

        return {"status" , "sucess"}

        
    except Exception as error:
        raise HTTPException(status_code=401 , detail=str(error))