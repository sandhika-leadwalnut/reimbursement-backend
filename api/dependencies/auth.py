from fastapi import Depends, HTTPException, Request, status
from supabase import Client
from core.supabase import get_supabase_client
from core.config import settings

ACCESS_COOKIE_NAME = "sb_access_token"
REFRESH_COOKIE_NAME = "sb_refresh_token"
CSRF_HEADER_NAME = "X-Requested-With"

def get_token(request: Request) -> str:
    cookie_token = request.cookies.get(ACCESS_COOKIE_NAME)
    if not cookie_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if CSRF_HEADER_NAME not in request.headers:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing required header")
    return cookie_token

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
    # First check if the user is set as admin in the database profile
    response = client.table("profiles").select("role").eq("id", str(user.id)).execute()
    if response.data and response.data[0].get("role") == "admin":
        return user
        
    # Fallback to email list check
    if user.email not in settings.admin_emails_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return user
