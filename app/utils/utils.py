from clerk_backend_api import Clerk, AuthenticateRequestOptions
from fastapi import HTTPException
from app.config.app_config import settings

clerk = Clerk(bearer_auth=settings.clerk_secret_key)

def authenticate_and_get_user_id(request):
    try:
        request_state = clerk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=["http://localhost:5173"],
                jwt_key=settings.jwt_publik_key
            )
        )


        if not request_state.is_signed_in:
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_id = request_state.payload.get("sub")
        return {"user_id": user_id}

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))