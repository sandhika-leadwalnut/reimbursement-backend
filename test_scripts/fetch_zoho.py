import asyncio
import httpx
import json
import time
from core.config import settings

async def main():
    with open(settings.TOKENS_JSON_PATH, 'r') as f:
        tokens = json.load(f)
    refresh_token = tokens.get("refresh_token", "")
    
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "refresh_token": refresh_token,
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    
    async with httpx.AsyncClient() as client:
        # Refresh token
        response = await client.post(url, data=data)
        if response.status_code != 200:
            print("Token refresh failed:", response.status_code, response.text)
            return
            
        resp_data = response.json()
        token = resp_data.get("access_token")
        print("Got new access token.")
        
        # Save it so the rest of the app can use it
        tokens["access_token"] = token
        if "refresh_token" in resp_data:
            tokens["refresh_token"] = resp_data["refresh_token"]
        tokens["expires_at"] = time.time() + resp_data.get("expires_in", 3600)
        with open(settings.TOKENS_JSON_PATH, 'w') as f:
            json.dump(tokens, f)
        
        # Fetch chart of accounts
        books_url = f"https://books.zoho.com/api/v3/chartofaccounts?organization_id={settings.ZOHO_ORGANIZATION_ID}"
        res = await client.get(
            books_url,
            headers={"Authorization": f"Zoho-oauthtoken {token}"}
        )
        print("API Status (books.zoho.com):", res.status_code)
        if res.status_code == 200:
            accounts = res.json().get("chartofaccounts", [])
            matches = 0
            for acc in accounts:
                name = acc.get('account_name', '').lower()
                target_names = ["travel", "boarding", "office", "staff welfare", "subscription", "miscellaneous"]
                if any(t in name for t in target_names):
                    print(f"{acc.get('account_name')}: {acc.get('account_id')}")
                    matches += 1
            if matches == 0:
                print("No matches found in chart of accounts.")
        else:
            print(res.text)

if __name__ == "__main__":
    asyncio.run(main())
