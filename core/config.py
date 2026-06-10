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
    TOKENS_JSON_PATH: str = "tokens.json"

    ADMIN_EMAILS: str = ""

    # Zoho specific defaults
    ZOHO_DEFAULT_GST_TREATMENT: str = "Unregistered Business"
    ZOHO_DEFAULT_SOURCE_OF_SUPPLY: str = "Karnataka"
    ZOHO_DEFAULT_PAID_THROUGH: str = "Employee Reimbursements"

    class Config:
        env_file = ".env"

    @property
    def admin_emails_list(self) -> List[str]:
        return [email.strip() for email in self.ADMIN_EMAILS.split(",") if email.strip()]

settings = Settings()
