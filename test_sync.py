import asyncio
import httpx
import json
import os
from core.config import settings

async def main():
    with open(settings.TOKENS_JSON_PATH, 'r') as f:
        tokens = json.load(f)
    access_token = tokens.get("access_token")
    
    url = "https://npgripymbwxeutfccikm.supabase.co/storage/v1/object/public/reimbursement-documents/2a60927b-1691-4d6d-a3d0-b88616716efe.pdf"
    
    async with httpx.AsyncClient() as client:
        doc_res = await client.get(url)
        
        expense_data = {
            "date": "2026-06-10",
            "account_id": settings.ZOHO_TRAVEL_ACCOUNT_ID,
            "paid_through_account_id": settings.ZOHO_REIMBURSEMENT_ACCOUNT_ID,
            "amount": 500.0,
            "is_inclusive_tax": False,
            "reference_number": "12345",
            "gst_treatment": settings.ZOHO_DEFAULT_GST_TREATMENT,
            "source_of_supply": settings.ZOHO_DEFAULT_SOURCE_OF_SUPPLY,
            "destination_of_supply": settings.ZOHO_DEFAULT_SOURCE_OF_SUPPLY,
            "description": "Test",
            "custom_fields": [
                {"label": "Employee Name", "value": "Test"},
                {"label": "Business Category", "value": "Test"}
            ]
        }
        
        data = {"JSONString": json.dumps(expense_data)}
        files = {"receipt": ("doc.pdf", doc_res.content)}
        res = await client.post(
            f"https://www.zohoapis.com/books/v3/expenses?organization_id={settings.ZOHO_ORGANIZATION_ID}",
            data=data,
            files=files,
            headers={"Authorization": f"Zoho-oauthtoken {access_token}"}
        )
        print("Status:", res.status_code)
        print("Response:", res.text)

if __name__ == "__main__":
    asyncio.run(main())
