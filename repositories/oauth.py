import supabase
from typing import Optional
from core.supabase import get_service_client
from schemas.oauth import OAuthToken, OAuthTokenCreate, OAuthTokenUpdate

class OAuthTokenRepository:
    def __init__(self, client: supabase.Client):
        self.client = client
        self.table_name = "oauth_tokens"

    def get_by_provider(self, provider: str) -> Optional[OAuthToken]:
        response = self.client.table(self.table_name).select("*").eq("provider", provider).execute()
        if response.data and len(response.data) > 0:
            return OAuthToken(**response.data[0])
        return None

    def create(self, data: OAuthTokenCreate) -> OAuthToken:
        response = self.client.table(self.table_name).insert(data.model_dump(mode='json')).execute()
        if response.data:
            return OAuthToken(**response.data[0])
        raise Exception("Failed to create OAuth token record")

    def update(self, provider: str, data: OAuthTokenUpdate) -> OAuthToken:
        update_data = data.model_dump(mode='json', exclude_unset=True)
        response = self.client.table(self.table_name).update(update_data).eq("provider", provider).execute()
        if response.data:
            return OAuthToken(**response.data[0])
        raise Exception(f"Failed to update OAuth token for provider: {provider}")

    def upsert(self, data: OAuthTokenCreate) -> OAuthToken:
        existing = self.get_by_provider(data.provider)
        if existing:
            update_data = OAuthTokenUpdate(
                access_token=data.access_token,
                refresh_token=data.refresh_token,
                expiry=data.expiry,
                token_type=data.token_type,
                scope=data.scope
            )
            return self.update(data.provider, update_data)
        else:
            return self.create(data)

oauth_repository = OAuthTokenRepository(get_service_client())
