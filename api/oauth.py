from fastapi import APIRouter, Depends, HTTPException
from schemas.oauth import OAuthToken
from services.oauth import oauth_service

router = APIRouter()

@router.get("/status", response_model=dict)
async def get_oauth_status():
    """
    Check the status of the OAuth integration.
    """
    try:
        token = await oauth_service.get_valid_access_token()
        # If we successfully got a valid access token, the integration is working
        return {
            "status": "connected",
            "provider": oauth_service.provider,
            "message": "OAuth integration is active and credentials are valid."
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "provider": oauth_service.provider,
            "error": str(e)
        }

@router.post("/refresh", response_model=dict)
async def force_refresh_token():
    """
    Force a manual refresh of the OAuth access token.
    """
    try:
        credentials = oauth_service.get_credentials()
        new_tokens = await oauth_service.refresh_access_token(credentials.refresh_token)
        
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens.get("refresh_token", credentials.refresh_token)
        expires_in = new_tokens.get("expires_in", 3600)
        
        oauth_service.save_credentials(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in
        )
        return {"status": "success", "message": "Token successfully refreshed."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
