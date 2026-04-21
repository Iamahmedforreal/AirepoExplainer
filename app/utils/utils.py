# app/utils/utils.py
from clerk_backend_api import Clerk
from clerk_backend_api.models import ClerkErrors
from fastapi import HTTPException, Header
import os

# initialize Clerk once with your secret key
clerk = Clerk(bearer_auth=os.getenv("CLEERK_SCERET_KEY"))

async def verify_token(authorization: str = Header(...)) -> dict:
    # Step 1: check header exists and has correct format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization scheme. Use 'Bearer <token>'"
        )

    # Step 2: extract raw token
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")

    try:
        # Step 3: send token to Clerk for verification
        # Clerk checks: signature, expiry, revocation — everything
        payload = clerk.sessions.verify_token(token)
        return payload  # contains sub (user_id), email, etc.

    except ClerkErrors as e:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")