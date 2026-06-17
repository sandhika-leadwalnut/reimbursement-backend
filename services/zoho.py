import json
import httpx
from core.config import settings
from schemas.reimbursement import Reimbursement

class ZohoExpenseService:
    def __init__(self):
        self.base_url = "https://www.zohoapis.com/books/v3/expenses"
        self.org_id = settings.ZOHO_ORGANIZATION_ID

    def _get_account_id_for_expense(self, nature_of_expense: str) -> str:
        nature = nature_of_expense.lower()
        if "taxi" in nature or "auto" in nature or "travel" in nature:
            return settings.ZOHO_LEDGER_TRAVEL_EXPENSES
        elif "hotel" in nature or "stay" in nature:
            return settings.ZOHO_LEDGER_BOARDING_LODGING
        elif "office" in nature or "repair" in nature:
            return settings.ZOHO_LEDGER_OFFICE_EXPENSES
        elif "food" in nature or "fitness" in nature or "recreation" in nature:
            return settings.ZOHO_LEDGER_STAFF_WELFARE
        elif "subscription" in nature or "tool" in nature:
            return settings.ZOHO_LEDGER_SUBSCRIPTION_COST
        else:
            return settings.ZOHO_LEDGER_MISC_EXPENSES

    async def sync_expense(self, reimbursement: Reimbursement) -> dict:
        from services.oauth import oauth_service
        token = await oauth_service.get_valid_access_token()
        headers = {
            "Authorization": f"Zoho-oauthtoken {token}"
            # Content-Type is set automatically by httpx when using files/data
        }
        
        expense_data = {
            "date": reimbursement.bill_date.isoformat(),
            "account_id": self._get_account_id_for_expense(reimbursement.nature_of_expense),
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
