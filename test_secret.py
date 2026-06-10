import asyncio
import httpx
from core.config import settings

async def main():
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://accounts.zoho.com/oauth/v2/token",
            data={
                "refresh_token": "dummy",
                "client_id": settings.ZOHO_CLIENT_ID,
                "client_secret": settings.ZOHO_CLIENT_SECRET,
                "grant_type": "refresh_token"
            }
        )
        print("com:", res.json())
        res = await client.post(
            "https://accounts.zoho.eu/oauth/v2/token",
            data={
                "refresh_token": "dummy",
                "client_id": settings.ZOHO_CLIENT_ID,
                "client_secret": settings.ZOHO_CLIENT_SECRET,
                "grant_type": "refresh_token"
            }
        )
        print("eu:", res.json())

if __name__ == "__main__":
    asyncio.run(main())
