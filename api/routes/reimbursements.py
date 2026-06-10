from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List
from uuid import UUID
from datetime import date
from schemas.reimbursement import Reimbursement, ReimbursementCreate, ReimbursementUpdate
from schemas.audit import AuditLog
from services.reimbursement import ReimbursementService
from services.storage import StorageService
from api.dependencies.auth import get_current_user
from api.dependencies.services import get_reimbursement_service, get_storage_service, get_audit_repo, get_reimbursement_repo
from repositories.impl import ReimbursementRepository, AuditLogRepository

router = APIRouter(prefix="/reimbursements", tags=["reimbursements"])

@router.get("", response_model=List[Reimbursement])
def get_my_reimbursements(
    user = Depends(get_current_user), 
    repo: ReimbursementRepository = Depends(get_reimbursement_repo)
):
    # RLS handles viewing only own reimbursements for employees, and all for admins
    return repo.get_active()

@router.post("", response_model=Reimbursement)
async def create_reimbursement(
    request_date: date = Form(...),
    business_category: str = Form(...),
    nature_of_expense: str = Form(...),
    bill_number: str = Form(...),
    bill_date: date = Form(...),
    amount: float = Form(...),
    brief_description: str = Form(None),
    file: UploadFile = File(...),
    user = Depends(get_current_user),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    document_url = await storage_service.upload_file(file)

    data = ReimbursementCreate(
        request_date=request_date,
        business_category=business_category,
        nature_of_expense=nature_of_expense,
        brief_description=brief_description,
        bill_number=bill_number,
        bill_date=bill_date,
        amount=amount
    )

    return reimbursement_service.create(
        data=data,
        employee_id=str(user.id),
        employee_email=user.email,
        employee_name=user.user_metadata.get('full_name', 'Unknown User'),
        document_url=document_url
    )

@router.get("/{id}", response_model=Reimbursement)
def get_reimbursement(
    id: UUID,
    repo: ReimbursementRepository = Depends(get_reimbursement_repo)
):
    reimbursement = repo.get_by_id(str(id))
    if not reimbursement or reimbursement.deleted_at:
        raise HTTPException(status_code=404, detail="Not found")
    return reimbursement

@router.put("/{id}", response_model=Reimbursement)
def update_reimbursement(
    id: UUID,
    data: ReimbursementUpdate,
    user = Depends(get_current_user),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service)
):
    return reimbursement_service.update(str(id), data, str(user.id))

@router.delete("/{id}", status_code=204)
def delete_reimbursement(
    id: UUID,
    user = Depends(get_current_user),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service)
):
    reimbursement_service.soft_delete(str(id), str(user.id))
    return None

@router.get("/{id}/audit", response_model=List[AuditLog])
def get_reimbursement_audit_logs(
    id: UUID,
    repo: AuditLogRepository = Depends(get_audit_repo)
):
    return repo.get_by_reimbursement(str(id))
