import asyncio
import httpx
import json
from core.config import settings

async def main():
    try:
        with open('tokens.json', 'r') as f:
            tokens = json.load(f)
        
        refresh_token = tokens.get('refresh_token')
        
        for secret in [settings.ZOHO_CLIENT_SECRET, settings.ZOHO_CLIENT_SECRET[:-1]]:
            for domain in ['accounts.zoho.in', 'accounts.zoho.com']:
                print(f"Trying domain={domain} secret_ends_with={secret[-4:]}")
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        f"https://{domain}/oauth/v2/token",
                        data={
                            "refresh_token": refresh_token,
                            "client_id": settings.ZOHO_CLIENT_ID,
                            "client_secret": secret,
                            "grant_type": "refresh_token"
                        }
                    )
                    data = res.json()
                    if "access_token" in data:
                        print("SUCCESS!", domain)
                        tokens['access_token'] = data['access_token']
                        with open('tokens.json', 'w') as f:
                            json.dump(tokens, f)
                        return
                    else:
                        print("Failed:", data)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
