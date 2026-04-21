import os
from dotenv import load_dotenv
from clerk_backend_api import Clerk, AuthenticateRequestOptions
from fastapi import HTTPException, Request , Header
import asyncio



load_dotenv()
clerk_sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))


def authenticate_and_get_user_details(request: Request):
    request_state = clerk_sdk.authenticate_request(
        request,
        AuthenticateRequestOptions(
            authorized_parties=["http://localhost:5173", "http://localhost:3000"],
            jwt_key=os.getenv("JWT_PUBLIK_KEY")
        )
    )

    if not request_state.is_signed_in:
        raise HTTPException(status_code=401, detail="Invalid token")

    return request_state.payload.get("sub")

async def verify_token(authorization:str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException( status_code=401 , detail="invalid token")
    
    token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(status_code=401 , detail="token missing")
    
    return token


async def get_clerk_user_id(request: Request) -> str:
    """Extract and verify Clerk user ID from request."""
    loop = asyncio.get_event_loop()
    try:
        user_id = await loop.run_in_executor(
            None,
            authenticate_and_get_user_details,
            request
        )
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        return user_id
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=401, detail=str(error))


