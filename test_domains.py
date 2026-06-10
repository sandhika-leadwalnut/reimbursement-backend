import asyncio
import httpx
import json

async def main():
    with open('tokens.json', 'r') as f:
        tokens = json.load(f)
    token = tokens.get("access_token")
    org_id = "865226191"
    
    domains = ["books.zoho.com", "books.zoho.in", "books.zoho.eu", "books.zoho.com.au"]
    async with httpx.AsyncClient() as client:
        for domain in domains:
            try:
                res = await client.get(
                    f"https://{domain}/api/v3/chartofaccounts?organization_id={org_id}",
                    headers={"Authorization": f"Zoho-oauthtoken {token}"}
                )
                print(f"{domain}: {res.status_code}")
                if res.status_code == 200:
                    print("Found valid domain:", domain)
            except Exception as e:
                pass

if __name__ == "__main__":
    asyncio.run(main())
