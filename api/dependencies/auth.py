from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from core.supabase import get_supabase_client
from core.config import settings

security = HTTPBearer()

def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials

def get_db_client(token: str = Depends(get_token)) -> Client:
    client = get_supabase_client(token)
    return client

def get_current_user(token: str = Depends(get_token), client: Client = Depends(get_db_client)):
    try:
        user = client.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user.user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

def get_current_admin(client: Client = Depends(get_db_client), user = Depends(get_current_user)):
    if user.email not in settings.admin_emails_list:
        # Double check via database if needed, but email checking is specified
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return user
