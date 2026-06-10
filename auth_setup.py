import asyncio
import urllib.parse
import os
import httpx
import json
import time
from core.config import settings

ZOHO_DOMAIN = "https://accounts.zoho.com"
REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI", "http://localhost")

def get_authorization_url() -> str:
    """Generates the authorization URL for the user to visit."""
    params = {
        "scope": "ZohoBooks.fullaccess.all",
        "client_id": settings.ZOHO_CLIENT_ID,
        "response_type": "code",
        "access_type": "offline",
        "redirect_uri": REDIRECT_URI,
        "prompt": "consent"
    }
    query_string = urllib.parse.urlencode(params)
    return f"{ZOHO_DOMAIN}/oauth/v2/auth?{query_string}"

async def main():
    print("="*60)
    print("ZOHO BOOKS OAUTH2 SETUP")
    print("="*60)
    
    if not settings.ZOHO_CLIENT_ID or not settings.ZOHO_CLIENT_SECRET:
        print("ERROR: Missing configuration.")
        print("Please ensure ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET are set in your .env file.")
        return

    auth_url = get_authorization_url()
    print("\n1. Please visit the following URL to authorize the application:")
    print(auth_url)
    print(f"\n2. After granting access, you will be redirected to {REDIRECT_URI}.")
    print("   Look at the URL in your browser and copy the 'code' parameter.")
    
    auth_code = input("\nEnter the authorization code here: ").strip()
    
    if not auth_code:
        print("Authorization code cannot be empty. Exiting.")
        return

    print("\nFetching initial tokens...")
    try:
        url = f"{ZOHO_DOMAIN}/oauth/v2/token"
        data = {
            "code": auth_code,
            "client_id": settings.ZOHO_CLIENT_ID,
            "client_secret": settings.ZOHO_CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch initial tokens: {response.text}")
                
            resp_data = response.json()
            if "error" in resp_data:
                raise Exception(f"OAuth Error: {resp_data['error']}")
                
            tokens = {
                "access_token": resp_data["access_token"],
                "refresh_token": resp_data["refresh_token"],
                "expires_at": time.time() + resp_data.get("expires_in", 3600)
            }
            
            with open(settings.TOKENS_JSON_PATH, "w") as f:
                json.dump(tokens, f)
                
            print("\nSUCCESS! Tokens have been fetched and saved to 'tokens.json'.")
            print("The service is now ready to run autonomously.")
    except Exception as e:
        print(f"\nERROR: Failed to fetch tokens - {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
