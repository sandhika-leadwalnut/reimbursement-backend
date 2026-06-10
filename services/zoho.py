import json
import httpx
from core.config import settings
from schemas.reimbursement import Reimbursement

class ZohoExpenseService:
    def __init__(self):
        self.base_url = "https://books.zoho.in/api/v3/expenses"
        self.org_id = settings.ZOHO_ORGANIZATION_ID
        self.token = self._get_access_token()

    def _get_access_token(self) -> str:
        try:
            with open(settings.TOKENS_JSON_PATH, 'r') as f:
                tokens = json.load(f)
                return tokens.get("access_token", "")
        except Exception:
            return ""

    async def sync_expense(self, reimbursement: Reimbursement) -> dict:
        headers = {
            "Authorization": f"Zoho-oauthtoken {self.token}"
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
            "description": f"Employee: {reimbursement.employee_name}\nDescription: {reimbursement.brief_description or reimbursement.nature_of_expense}\nAdmin Remarks: {reimbursement.remarks or 'None'}",
            "custom_fields": [
                {"label": "Employee Name", "value": reimbursement.employee_name},
                {"label": "Business Category", "value": reimbursement.business_category}
            ]
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
