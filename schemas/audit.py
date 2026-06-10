from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from models.enums import AuditAction

class AuditLogBase(BaseModel):
    reimbursement_id: UUID
    action: AuditAction
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None

class AuditLogCreate(AuditLogBase):
    performed_by: Optional[UUID] = None

class AuditLog(AuditLogBase):
    id: UUID
    performed_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
