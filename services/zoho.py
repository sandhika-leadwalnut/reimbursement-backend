import json
import httpx
from core.config import settings
from schemas.reimbursement import Reimbursement

class ZohoExpenseService:
    def __init__(self):
        self.base_url = "https://www.zohoapis.com/books/v3/expenses"
        self.org_id = settings.ZOHO_ORGANIZATION_ID

    def _load_tokens(self) -> dict:
        try:
            with open(settings.TOKENS_JSON_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    async def get_valid_access_token(self) -> str:
        import time
        tokens = self._load_tokens()
        access_token = tokens.get("access_token", "")
        refresh_token = tokens.get("refresh_token", "")
        expires_at = tokens.get("expires_at", 0)

        if not access_token or not refresh_token:
            raise Exception("Tokens are missing. Please run auth_setup.py")

        # Buffer of 60 seconds
        if time.time() > (expires_at - 60):
            print("Access token is expired or expiring soon. Refreshing...")
            url = "https://accounts.zoho.com/oauth/v2/token"
            data = {
                "refresh_token": refresh_token,
                "client_id": settings.ZOHO_CLIENT_ID,
                "client_secret": settings.ZOHO_CLIENT_SECRET,
                "grant_type": "refresh_token"
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                resp_data = response.json()
                
                if "error" in resp_data:
                    raise Exception(f"OAuth Refresh Error: {resp_data['error']}")
                    
                tokens["access_token"] = resp_data["access_token"]
                if "refresh_token" in resp_data:
                    tokens["refresh_token"] = resp_data["refresh_token"]
                tokens["expires_at"] = time.time() + resp_data.get("expires_in", 3600)
                
                with open(settings.TOKENS_JSON_PATH, 'w') as f:
                    json.dump(tokens, f)
                print("Successfully refreshed access token.")
                return tokens["access_token"]
        
        return access_token

    async def sync_expense(self, reimbursement: Reimbursement) -> dict:
        token = await self.get_valid_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}"
            # Content-Type is set automatically by httpx when using files/data
        }
        
        expense_data = {
            "date": reimbursement.bill_date.isoformat(),
            "account_id": settings.ZOHO_TRAVEL_ACCOUNT_ID,
            "paid_through_account_id": settings.ZOHO_REIMBURSEMENT_ACCOUNT_ID,
            "amount": reimbursement.approved_amount or reimbursement.amount,
            "is_inclusive_tax": False,
            "reference_number": reimbursement.bill_number or "",
            "gst_treatment": settings.ZOHO_DEFAULT_GST_TREATMENT,
            "source_of_supply": settings.ZOHO_DEFAULT_SOURCE_OF_SUPPLY,
            "destination_of_supply": settings.ZOHO_DEFAULT_SOURCE_OF_SUPPLY,
            "description": f"Employee: {reimbursement.employee_name}\nDescription: {reimbursement.brief_description or reimbursement.nature_of_expense}\nAdmin Remarks: {reimbursement.remarks or 'None'}"
        }

        async with httpx.AsyncClient() as client:
            files = {}
            if reimbursement.document_url:
                try:
                    # Fetch document content to upload
                    doc_response = await client.get(reimbursement.document_url)
                    doc_response.raise_for_status()
                    filename = reimbursement.document_url.split("/")[-1]
                    if '?' in filename:
                        filename = filename.split('?')[0]
                    files["receipt"] = (filename, doc_response.content)
                except Exception as e:
                    print(f"Warning: Could not fetch document for Zoho upload: {e}")

            data = {
                "JSONString": json.dumps(expense_data)
            }
            
            response = await client.post(
                f"{self.base_url}?organization_id={self.org_id}",
                data=data,
                files=files if files else None,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
