from fastapi import APIRouter, Depends
from schemas.profile import Profile
from services.auth import AuthService
from api.dependencies.auth import get_current_user
from api.dependencies.services import get_auth_service

router = APIRouter(prefix="/me", tags=["auth"])

@router.get("", response_model=Profile)
def get_me(user = Depends(get_current_user), auth_service: AuthService = Depends(get_auth_service)):
    profile = auth_service.get_or_create_profile(user)
    return profile
