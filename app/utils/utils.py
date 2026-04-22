from clerk_backend_api import Clerk, AuthenticateRequestOptions
from fastapi import HTTPException, Request
import os

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

async def verify_token(request: Request):
    try:
        request_state = clerk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=["http://localhost:5173"],
                jwt_key=os.getenv("JWT_PUBLIK_KEY")
            )
        )

        if not request_state.is_signed_in:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_id = request_state.payload.get("sub")

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))