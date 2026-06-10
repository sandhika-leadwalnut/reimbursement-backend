import asyncio
import httpx
import json
import os
from core.config import settings

async def main():
    with open(settings.TOKENS_JSON_PATH, 'r') as f:
        tokens = json.load(f)
    access_token = tokens.get("access_token")
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"https://www.zohoapis.com/books/v3/expenses/5589375000003235001?organization_id={settings.ZOHO_ORGANIZATION_ID}",
            headers={"Authorization": f"Zoho-oauthtoken {access_token}"}
        )
        data = res.json()
        print(data.get("expense", {}).get("account_id"))
        print(data.get("expense", {}).get("paid_through_account_id"))

if __name__ == "__main__":
    asyncio.run(main())
