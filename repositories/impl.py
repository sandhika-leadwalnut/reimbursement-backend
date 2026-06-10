from supabase import Client
from typing import Optional, List
from schemas.profile import Profile
from schemas.reimbursement import Reimbursement
from schemas.audit import AuditLog
from repositories.base import BaseRepository

class ProfileRepository(BaseRepository[Profile]):
    def __init__(self, client: Client):
        super().__init__(client, "profiles", Profile)
        
    def get_by_email(self, email: str) -> Optional[Profile]:
        response = self.client.table(self.table_name).select("*").eq("email", email).execute()
        if response.data:
            return self.model.model_validate(response.data[0])
        return None

class ReimbursementRepository(BaseRepository[Reimbursement]):
    def __init__(self, client: Client):
        super().__init__(client, "reimbursements", Reimbursement)

    def get_active(self) -> List[Reimbursement]:
        # Filter out soft-deleted
        response = self.client.table(self.table_name).select("*").is_("deleted_at", "null").execute()
        return [self.model.model_validate(item) for item in response.data]

    def soft_delete(self, id: str) -> Reimbursement:
        from datetime import datetime
        response = self.client.table(self.table_name).update({"deleted_at": datetime.utcnow().isoformat()}).eq("id", id).execute()
        return self.model.model_validate(response.data[0])

class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, client: Client):
        super().__init__(client, "audit_logs", AuditLog)

    def get_by_reimbursement(self, reimbursement_id: str) -> List[AuditLog]:
        response = self.client.table(self.table_name).select("*").eq("reimbursement_id", reimbursement_id).order('created_at', desc=True).execute()
        return [self.model.model_validate(item) for item in response.data]
