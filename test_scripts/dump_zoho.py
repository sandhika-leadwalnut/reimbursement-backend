import asyncio
import json
import httpx
from core.config import settings
from services.zoho import ZohoExpenseService

async def main():
    service = ZohoExpenseService()
    token = await service.get_valid_access_token()
    
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f'https://books.zoho.in/api/v3/chartofaccounts?organization_id={settings.ZOHO_ORGANIZATION_ID}',
            headers={'Authorization': f'Zoho-oauthtoken {token}'}
        )
        data = res.json()
        print(json.dumps(data.get("chartofaccounts", []), indent=2))

if __name__ == '__main__':
    asyncio.run(main())
