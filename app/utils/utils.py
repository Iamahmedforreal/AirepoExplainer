import os
from dotenv import load_dotenv
from clerk_backend_api import Clerk , AuthenticateRequestOptions
from fastapi import HTTPException


load_dotenv()
clerk_sdk = Clerk(bearer_auth=os.getenv("CLERK_SECRET_KEY"))

def authenticate_and_get_user_details(request):
    try:
        request_state = clerk_sdk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=["http://localhost:8000"],
                jwt_key=os.getenv("JWT_PUBLIK_KEY")
            )
        )
        if not request_state.is_signed_in:
            raise HTTPException(status_code=401 , detail="invalid token")

        user_id = request_state.get("sub")
        return user_id
        
    except  HTTPException as error:
        raise HTTPException(status_code=500 , detail="invalid crendetionl")


