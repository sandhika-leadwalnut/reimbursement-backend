import asyncio
import httpx
import json
import os
from core.config import settings

async def main():
    try:
        # Check if the token file exists
        if not os.path.exists(settings.TOKENS_JSON_PATH):
            print("❌ tokens.json not found. Please authenticate with Zoho first.")
            return

        with open(settings.TOKENS_JSON_PATH, 'r') as f:
            tokens = json.load(f)
            
        access_token = tokens.get("access_token")
        
        if not access_token:
            print("❌ Access token is empty in tokens.json.")
            return

        print("🔄 Fetching Chart of Accounts from Zoho Books...")
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"https://books.zoho.com/api/v3/chartofaccounts?organization_id={settings.ZOHO_ORGANIZATION_ID}",
                headers={"Authorization": f"Zoho-oauthtoken {access_token}"}
            )
            
            if res.status_code == 401:
                print("❌ Unauthorized! Your token has expired or is invalid.")
                print("Please generate a new refresh token and update tokens.json.")
                return
                
            res.raise_for_status()
            data = res.json()
            accounts = data.get("chartofaccounts", [])
            
            print("\n✅ Found Accounts Matching 'Travel', 'Expense', or 'Reimburse':\n" + "-"*60)
            matches = 0
            for acc in accounts:
                name = acc.get("account_name", "").lower()
                if "travel" in name or "expense" in name or "reimburse" in name:
                    matches += 1
                    print(f"Name: {acc.get('account_name'):<30} | ID: {acc.get('account_id')} | Type: {acc.get('account_type')}")
            
            if matches == 0:
                print("No matching accounts found! You might need to create them in Zoho Books.")
                    
    except Exception as e:
        print(f"❌ Error fetching accounts: {e}")

if __name__ == "__main__":
    asyncio.run(main())
