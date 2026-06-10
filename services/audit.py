from typing import Dict, Any, Optional
from uuid import UUID
from schemas.audit import AuditLogCreate
from models.enums import AuditAction
from repositories.impl import AuditLogRepository

class AuditService:
    def __init__(self, repository: AuditLogRepository):
        self.repository = repository

    def log_action(self, reimbursement_id: UUID, action: AuditAction, 
                   old_value: Optional[Dict[str, Any]] = None, 
                   new_value: Optional[Dict[str, Any]] = None, 
                   performed_by: Optional[UUID] = None):
        
        audit_data = AuditLogCreate(
            reimbursement_id=reimbursement_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            performed_by=performed_by
        )
        self.repository.create(audit_data.model_dump(exclude_none=True))
