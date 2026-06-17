from supabase import create_client, Client
from core.config import settings

def get_supabase_client(token: str = None) -> Client:
    # Sanitize inputs to prevent trailing spaces or literal quotes from Vercel env vars
    url = settings.SUPABASE_URL.strip().strip('"').strip("'")
    key = settings.SUPABASE_KEY.strip().strip('"').strip("'")
    client: Client = create_client(url, key)
    if token:
        # Currently, supabase-py doesn't have an easy way to set the token for RLS directly without logging in
        # But we can pass it in the headers
        client.postgrest.auth(token)
    return client

def get_service_client() -> Client:
    # Requires service role key to bypass RLS, but here we can just use anon key if RLS allows or if we have service key in env
    # For now, if we use anon key it's subject to RLS
    service_key = getattr(settings, 'SUPABASE_SERVICE_KEY', None)
    if not service_key:
        service_key = settings.SUPABASE_KEY
        
    url = settings.SUPABASE_URL.strip().strip('"').strip("'")
    key = service_key.strip().strip('"').strip("'")
    return create_client(url, key)
