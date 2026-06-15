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
            f"https://www.zohoapis.com/books/v3/chartofaccounts?organization_id={settings.ZOHO_ORGANIZATION_ID}",
            headers={"Authorization": f"Zoho-oauthtoken {token}"}
        )
        if res.status_code == 200:
            data = res.json()
            accounts = data.get("chartofaccounts", [])
            
            target_ledgers = [
                "Travel Expenses", "Travelling Expenses", "Boarding and lodging", "Boarding & Lodging Expenses",
                "Office Expenses", "Staff welfare", "Staff Welfare Expenses",
                "Subscription Cost", "Subscriptions", "Miscellaneous Expenses", "Miscellaneous"
            ]
            
            for acc in accounts:
                name = acc.get("account_name")
                for t in target_ledgers:
                    if t.lower() in name.lower():
                        print(f"{name}: {acc.get('account_id')}")
        else:
            print("Error:", res.status_code, res.text)

if __name__ == "__main__":
    asyncio.run(main())
