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
            "Authorization": f"Zoho-oauthtoken {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "date": reimbursement.bill_date.isoformat(),
            "account_id": "", # In a real implementation we would map nature_of_expense to a Zoho Account ID
            "amount": reimbursement.approved_amount or reimbursement.amount,
            "currency_id": "", # Need default currency ID
            "description": reimbursement.brief_description or reimbursement.nature_of_expense,
            "reference_number": reimbursement.bill_number,
            "gst_treatment": settings.ZOHO_DEFAULT_GST_TREATMENT,
            "source_of_supply": settings.ZOHO_DEFAULT_SOURCE_OF_SUPPLY,
            "paid_through_account_id": "", # Should map "Employee Reimbursements" to its account ID
            "custom_fields": [
                {"label": "Employee Name", "value": reimbursement.employee_name},
                {"label": "Business Category", "value": reimbursement.business_category}
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}?organization_id={self.org_id}",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
