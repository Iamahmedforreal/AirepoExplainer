import logging

from clerk_backend_api import Clerk, AuthenticateRequestOptions, ClerkBaseError
from fastapi import HTTPException
from app.config.app_config import settings

logger = logging.getLogger(__name__)
clerk = Clerk(bearer_auth=settings.clerk_secret_key)

def authenticate_and_get_user_id(request):
    try:
        request_state = clerk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                authorized_parties=settings.authorized_parties,
                jwt_key=settings.jwt_publik_key
            )
        )


        if not request_state.is_signed_in:
            logger.info("Auth failed: not signed in. reason=%s", request_state.reason)
            raise HTTPException(status_code=401, detail="Unauthorized")

        user_id = request_state.payload.get("sub")
        if not user_id:
            logger.info("Auth failed: user_id not found in payload")
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        return {"user_id": user_id}


    except HTTPException:
        raise
 
    except ClerkBaseError as e:
        logger.error("Clerk auth error: %s", e.message, exc_info=True)
        raise HTTPException(status_code=401, detail="Unauthorized")
 
    except Exception:
        logger.exception("Unexpected error during authentication")
        raise HTTPException(status_code=500, detail="Internal server error")
 