import asyncio
import httpx
import json
from core.config import settings

async def main():
    with open(settings.TOKENS_JSON_PATH, 'r') as f:
        tokens = json.load(f)
    token = tokens.get("access_token")
    
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://www.zohoapis.com/books/v3/settings/expensecategories?organization_id={settings.ZOHO_ORGANIZATION_ID}",
            headers={"Authorization": f"Zoho-oauthtoken {token}"}
        )
        print("API Status:", res.status_code)
        print(res.text)

if __name__ == "__main__":
    asyncio.run(main())
