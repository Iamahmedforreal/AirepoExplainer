# app/utils/utils.py
from clerk_backend_api import Clerk , AuthenticateRequestOptions
from fastapi import HTTPException, Header , Request
import os

clerk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

async def verify_token(request: Request):
    try:
        auth = clerk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=["http://localhost:5173"],
                jwt_key=os.getenv("JWT_PUBLIK_KEY")
            )
        )

        if not auth.is_signed_in:
            raise HTTPException(status_code=401, detail="Unauthorized")

        return auth.session_claims

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))