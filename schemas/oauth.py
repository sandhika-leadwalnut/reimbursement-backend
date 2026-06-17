from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class OAuthTokenBase(BaseModel):
    provider: str
    access_token: str
    refresh_token: str
    expiry: datetime
    token_type: Optional[str] = None
    scope: Optional[str] = None

class OAuthTokenCreate(OAuthTokenBase):
    pass

class OAuthTokenUpdate(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expiry: Optional[datetime] = None
    token_type: Optional[str] = None
    scope: Optional[str] = None

class OAuthToken(OAuthTokenBase):
    id: UUID
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
