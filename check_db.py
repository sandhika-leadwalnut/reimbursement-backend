import asyncio
from core.config import settings
from repositories.impl import ReimbursementRepository
from supabase import create_client

async def main():
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    repo = ReimbursementRepository(client)
    records = repo.get_active()
    for r in records[-5:]:
        print(f"ID: {r.id}, Doc URL: {r.document_url}")

if __name__ == "__main__":
    asyncio.run(main())
