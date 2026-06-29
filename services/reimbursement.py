import uuid
from typing import List
from datetime import datetime
from fastapi import HTTPException
from schemas.reimbursement import ReimbursementCreate, ReimbursementUpdate, Reimbursement
from schemas.audit import AuditAction
from models.enums import ReimbursementStatus
from repositories.impl import ReimbursementRepository
from services.audit import AuditService
from utils.payment_calc import calculate_payment_date

class ReimbursementService:
    def __init__(self, repository: ReimbursementRepository, audit_service: AuditService):
        self.repository = repository
        self.audit_service = audit_service

    def create(self, data: ReimbursementCreate, employee_id: str, employee_email: str, employee_name: str, document_url: str = None, gdrive_link: str = None) -> Reimbursement:
        today = datetime.utcnow().date()
        payment_date = calculate_payment_date(today)

        payload = data.model_dump(mode='json')
        payload.update({
            "employee_id": employee_id,
            "employee_email": employee_email,
            "employee_name": employee_name,
            "document_url": document_url,
            "gdrive_link": gdrive_link,
            "status": ReimbursementStatus.pending_review.value,
            "expected_payment_date": payment_date.isoformat(),
        })
        # Note: pydantic objects use enum values
        result = self.repository.create(payload)
        
        self.audit_service.log_action(
            reimbursement_id=result.id,
            action=AuditAction.create,
            new_value=result.model_dump(mode='json'),
            performed_by=uuid.UUID(employee_id)
        )
        return result

    def update(self, id: str, data: ReimbursementUpdate, user_id: str, document_url: str = None, gdrive_link: str = None) -> Reimbursement:
        existing = self.repository.get_by_id(id)
        if not existing:
            raise HTTPException(status_code=404, detail="Not found")

        # if employee is updating, ensure it's pending review or under_review
        if str(existing.employee_id) == user_id and existing.status not in [ReimbursementStatus.pending_review, ReimbursementStatus.under_review]:
             raise HTTPException(status_code=400, detail="Cannot update unless pending review or under review")

        # Automatically update status back to pending review if it was clarified
        update_data = data.model_dump(mode='json', exclude_unset=True)
        if document_url:
            update_data["document_url"] = document_url
        if gdrive_link is not None:
            update_data["gdrive_link"] = gdrive_link
        if existing.status == ReimbursementStatus.under_review:
            update_data["status"] = ReimbursementStatus.pending_review.value
        if not update_data:
            return existing

        result = self.repository.update(id, update_data)
        
        self.audit_service.log_action(
            reimbursement_id=result.id,
            action=AuditAction.update if existing.status != ReimbursementStatus.under_review else AuditAction.clarification_updated,
            old_value=existing.model_dump(mode='json'),
            new_value=result.model_dump(mode='json'),
            performed_by=uuid.UUID(user_id)
        )
        return result

    def update_status(self, id: str, status: ReimbursementStatus, admin_id: str, **kwargs) -> Reimbursement:
        existing = self.repository.get_by_id(id)
        if not existing:
            raise HTTPException(status_code=404, detail="Not found")

        update_data = {"status": status.value}

        update_data.update(kwargs)

        result = self.repository.update(id, update_data)
        
        action = AuditAction.update
        if status == ReimbursementStatus.approved:
            action = AuditAction.approve
        elif status == ReimbursementStatus.rejected:
            action = AuditAction.reject
        elif status == ReimbursementStatus.under_review:
            action = AuditAction.clarification_requested

        self.audit_service.log_action(
            reimbursement_id=result.id,
            action=action,
            old_value=existing.model_dump(mode='json'),
            new_value=result.model_dump(mode='json'),
            performed_by=uuid.UUID(admin_id)
        )
        return result

    def soft_delete(self, id: str, user_id: str) -> bool:
        existing = self.repository.get_by_id(id)
        if not existing:
            raise HTTPException(status_code=404, detail="Not found")

        result = self.repository.soft_delete(id)
        self.audit_service.log_action(
            reimbursement_id=result.id,
            action=AuditAction.soft_delete,
            performed_by=uuid.UUID(user_id)
        )
        return True
