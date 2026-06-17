import httpx
import time
from datetime import datetime, timezone
from fastapi import HTTPException
from core.config import settings
from repositories.oauth import oauth_repository
from schemas.oauth import OAuthTokenCreate

class OAuthService:
    def __init__(self, provider: str = "zoho"):
        self.provider = provider
        self.repo = oauth_repository

    def get_credentials(self):
        """Loads credentials from Supabase"""
        credentials = self.repo.get_by_provider(self.provider)
        if not credentials:
            raise HTTPException(status_code=401, detail=f"No OAuth credentials found for provider: {self.provider}")
        return credentials

    def is_token_expired(self, credentials) -> bool:
        """Checks whether the access token is expired"""
        # Buffer of 60 seconds
        now = datetime.now(timezone.utc)
        return now >= credentials.expiry

    async def refresh_access_token(self, refresh_token: str):
        """Automatically refreshes the token when necessary"""
        url = "https://accounts.zoho.com/oauth/v2/token"
        data = {
            "refresh_token": refresh_token,
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "grant_type": "refresh_token"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            resp_data = response.json()
            
            if "error" in resp_data:
                raise HTTPException(status_code=401, detail=f"OAuth Refresh Error: {resp_data['error']}")
                
            return resp_data

    def save_credentials(self, access_token: str, refresh_token: str, expires_in: int):
        """Updates Supabase with the new access token and expiry"""
        expiry_time = datetime.fromtimestamp(time.time() + expires_in, timezone.utc)
        
        token_data = OAuthTokenCreate(
            provider=self.provider,
            access_token=access_token,
            refresh_token=refresh_token,
            expiry=expiry_time
        )
        return self.repo.upsert(token_data)

    async def get_valid_access_token(self) -> str:
        """Returns a valid access token to callers, refreshing if needed"""
        try:
            credentials = self.get_credentials()
        except HTTPException:
            # If no credentials found, we can't refresh
            raise Exception(f"Tokens are missing for provider '{self.provider}'. Please re-authenticate.")

        if not credentials.access_token or not credentials.refresh_token:
            raise Exception("Tokens are missing or invalid.")

        if self.is_token_expired(credentials):
            print("Access token is expired or expiring soon. Refreshing...")
            new_tokens = await self.refresh_access_token(credentials.refresh_token)
            
            new_access_token = new_tokens["access_token"]
            new_refresh_token = new_tokens.get("refresh_token", credentials.refresh_token)
            expires_in = new_tokens.get("expires_in", 3600)
            
            self.save_credentials(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
                expires_in=expires_in
            )
            return new_access_token
            
        return credentials.access_token

oauth_service = OAuthService("zoho")
