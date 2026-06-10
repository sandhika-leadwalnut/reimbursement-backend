from schemas.profile import Profile
from repositories.impl import ProfileRepository
from core.config import settings

class AuthService:
    def __init__(self, repository: ProfileRepository):
        self.repository = repository

    def get_or_create_profile(self, user) -> Profile:
        # Check if profile exists
        profile = self.repository.get_by_id(str(user.id))
        if not profile:
            # Fallback if trigger didn't fire or was delayed
            # Actually, the trigger does it. But we enforce admin role based on email
            pass
        
        # Enforce admin role dynamically based on environment if it differs
        if user.email in settings.admin_emails_list and profile and profile.role != 'admin':
            profile = self.repository.update(str(user.id), {"role": "admin"})

        return profile
