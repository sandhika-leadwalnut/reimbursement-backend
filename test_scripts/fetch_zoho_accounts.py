import asyncio
import httpx
import json
import os
import time
from core.config import settings

AUTH_CODE = "1000.83f14afb84b98cfb5a8b77d453067511.1f424f27d120824e8502e4ec307f7ebf"

async def main():
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "code": AUTH_CODE,
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "redirect_uri": "http://localhost",
        "grant_type": "authorization_code"
    }
    
    async with httpx.AsyncClient() as client:
        print("Exchanging authorization code...")
        response = await client.post(url, data=data)
        if response.status_code != 200:
            print("Failed to fetch initial tokens:", response.text)
            return
            
        resp_data = response.json()
        if "error" in resp_data:
            print("OAuth Error:", resp_data['error'])
            return
            
        tokens = {
            "access_token": resp_data["access_token"],
            "refresh_token": resp_data["refresh_token"],
            "expires_at": time.time() + resp_data.get("expires_in", 3600)
        }
        
        with open(settings.TOKENS_JSON_PATH, "w") as f:
            json.dump(tokens, f)
        print("Tokens saved successfully.")

        # Now fetch chart of accounts
        print("Fetching Chart of Accounts...")
        books_url = f"https://books.zoho.com/api/v3/chartofaccounts?organization_id={settings.ZOHO_ORGANIZATION_ID}"
        res = await client.get(
            books_url,
            headers={"Authorization": f"Zoho-oauthtoken {tokens['access_token']}"}
        )
        
        if res.status_code == 200:
            accounts = res.json().get("chartofaccounts", [])
            target_names = ["travel", "boarding", "office", "staff welfare", "subscription", "miscellaneous"]
            found = {}
            for acc in accounts:
                name = acc.get('account_name', '')
                if any(t in name.lower() for t in target_names):
                    found[name] = acc.get('account_id')
                    print(f"FOUND: {name} -> {acc.get('account_id')}")
                    
            # Output in a format easy to parse for .env updating
            print("--- MAPPINGS ---")
            for k, v in found.items():
                print(f"{k}|{v}")
        else:
            print("API Error:", res.status_code, res.text)

if __name__ == "__main__":
    asyncio.run(main())
