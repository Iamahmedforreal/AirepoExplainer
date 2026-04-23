from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import get_db
from svix.webhooks import Webhook
import os
import logging
from dotenv import load_dotenv
from app.services.webhook import create_new_user,is_duplicate_webhook , save_webhook_events
load_dotenv()

logger = logging.getLogger(__name__)

router_webhook = APIRouter()  


@router_webhook.post("/webhooks/clerk") 
async def webhook_function(request: Request, db: AsyncSession = Depends(get_db)):
    logger.info("Received incoming Clerk webhook request")
    try:
        # check secret exists
        webhook_secret = os.getenv("CLERK_WEBHOOK_SECRET")
        if not webhook_secret:
            logger.error("CLERK_WEBHOOK_SECRET is not set")
            raise HTTPException(
                status_code=500,
                detail="CLERK_WEBHOOK_SECRET is not set"
            )

        payload = await request.body()
        headers = dict(request.headers)

        # verify the webhook signature
        try:
            logger.debug("Attempting to verify webhook signature")
            wh = Webhook(webhook_secret)
            event = wh.verify(payload, headers)
            logger.debug("Webhook signature verified successfully")
        except Exception as error:
            logger.error("Webhook verification failed: %s", error, exc_info=True)
            raise HTTPException(status_code=401, detail=f"Webhook verification failed: {str(error)}")
        
        svix_id = request.headers.get("svix-id")
        if not svix_id:
            raise HTTPException(status_code=400 , details="Missing svix-id header")
        if await is_duplicate_webhook(svix_id , db):
            return {"status":"duplicate ignored"}
        
        # ignore events that are not user.created
        if event.get("type") != "user.created":
            logger.info("Ignoring webhook event type: %s", event.get("type"))
            return {"status": "ignored"}
       # get clerk user id

        user_id = event.get("data", {}).get("id")

        if not user_id:
            logger.error("Could not extract user id from webhook event payload: %s", event)
            raise HTTPException(
                status_code=400,
                detail="Could not extract user id from webhook event"
            )
        
        await save_webhook_events(svix_id , event , db)
        await create_new_user(user_id, db)
        return {"status": "success"}

    except HTTPException:
        raise  

    except ValueError as error:
        logger.warning("ValueError processing webhook: %s", error)
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        logger.error("Internal server error processing webhook: %s", error, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(error)}")