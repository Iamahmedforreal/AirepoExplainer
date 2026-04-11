import os
from fastapi import APIRouter, Depends, Request, HTTPException , AssyncSession
from dotenv import load_dotenv

from app.models.db import get_db


load_dotenv()

router = APIRouter()

@router.post("/clerk-webhook")
async def handle_clerk_webhook(request: Request , db: AssyncSession = Depends(get_db)):
    pass