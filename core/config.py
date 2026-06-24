from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str = ""
    
    ZOHO_CLIENT_ID: str = ""
    ZOHO_CLIENT_SECRET: str = ""
    ZOHO_ORGANIZATION_ID: str = ""

    RESEND_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    ADMIN_EMAILS: str = ""

    # Zoho specific defaults
    ZOHO_TRAVEL_ACCOUNT_ID: str = ""
    ZOHO_REIMBURSEMENT_ACCOUNT_ID: str = ""
    ZOHO_DEFAULT_GST_TREATMENT: str = "business_none"
    ZOHO_DEFAULT_SOURCE_OF_SUPPLY: str = "KA"

    # Ledger Mappings for Expense Categories
    ZOHO_LEDGER_TRAVEL_EXPENSES: str = ""
    ZOHO_LEDGER_BOARDING_LODGING: str = ""
    ZOHO_LEDGER_OFFICE_EXPENSES: str = ""
    ZOHO_LEDGER_STAFF_WELFARE: str = ""
    ZOHO_LEDGER_SUBSCRIPTION_COST: str = ""
    ZOHO_LEDGER_MISC_EXPENSES: str = ""

    class Config:
        env_file = ".env"

    @property
    def admin_emails_list(self) -> List[str]:
        return [email.strip() for email in self.ADMIN_EMAILS.split(",") if email.strip()]

settings = Settings()
