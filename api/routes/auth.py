from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from schemas.profile import Profile
from services.auth import AuthService
from api.dependencies.auth import get_current_user, ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME
from api.dependencies.services import get_auth_service
from core.config import settings
from core.supabase import get_supabase_client

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _set_auth_cookies(response: Response, session) -> None:
    secure = settings.FRONTEND_URL.startswith("https://")
    samesite = "none" if secure else "lax"
    response.set_cookie(
        ACCESS_COOKIE_NAME,
        session.access_token,
        max_age=session.expires_in,
        path="/",
        httponly=True,
        secure=secure,
        samesite=samesite,
    )
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        session.refresh_token,
        path="/auth",
        httponly=True,
        secure=secure,
        samesite=samesite,
    )


@router.get("/me", response_model=Profile)
def get_me(user = Depends(get_current_user), auth_service: AuthService = Depends(get_auth_service)):
    profile = auth_service.get_or_create_profile(user)
    return profile


@router.post("/auth/login")
def login(body: LoginRequest, response: Response):
    client = get_supabase_client()
    try:
        result = client.auth.sign_in_with_password({"email": body.email, "password": body.password})
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not result.session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _set_auth_cookies(response, result.session)
    return {"ok": True}


@router.post("/auth/refresh")
def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    client = get_supabase_client()
    try:
        result = client.auth.refresh_session(refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    if not result.session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    _set_auth_cookies(response, result.session)
    return {"ok": True}


@router.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(ACCESS_COOKIE_NAME)
    if token:
        try:
            get_supabase_client(token).auth.sign_out()
        except Exception:
            pass

    response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/auth")
    return {"ok": True}
