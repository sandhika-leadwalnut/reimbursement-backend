from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
from uuid import UUID
from datetime import date
from schemas.reimbursement import Reimbursement, ReimbursementCreate, ReimbursementUpdate
from schemas.audit import AuditLog
from services.reimbursement import ReimbursementService
from services.storage import StorageService
from services.email import EmailService
from api.dependencies.auth import get_current_user
from api.dependencies.services import get_reimbursement_service, get_storage_service, get_audit_repo, get_reimbursement_repo, get_email_service
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
    background_tasks: BackgroundTasks,
    request_date: date = Form(...),
    business_category: str = Form(...),
    nature_of_expense: str = Form(...),
    bill_number: str = Form(...),
    bill_date: date = Form(...),
    amount: float = Form(...),
    brief_description: str = Form(None),
    file: Optional[UploadFile] = File(None),
    gdrive_link: Optional[str] = Form(None),
    user = Depends(get_current_user),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service),
    storage_service: StorageService = Depends(get_storage_service),
    email_service: EmailService = Depends(get_email_service)
):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")

    if not file and not gdrive_link:
        raise HTTPException(status_code=400, detail="Either file or gdrive_link must be provided")

    document_url = None
    if file:
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

    result = reimbursement_service.create(
        data=data,
        employee_id=str(user.id),
        employee_email=user.email,
        employee_name=user.user_metadata.get('full_name', 'Unknown User'),
        document_url=document_url,
        gdrive_link=gdrive_link
    )

    # Sent in the background so a Brevo outage can never block a submission.
    background_tasks.add_task(
        email_service.send_submission_confirmation,
        result.employee_email,
        result.employee_name,
        result.bill_number,
        result.nature_of_expense,
        result.amount,
        result.request_date.isoformat() if result.request_date else None,
        result.expected_payment_date.isoformat() if result.expected_payment_date else None
    )

    return result

@router.get("/{id}", response_model=Reimbursement)
def get_reimbursement(
    id: UUID,
    user = Depends(get_current_user),
    repo: ReimbursementRepository = Depends(get_reimbursement_repo)
):
    reimbursement = repo.get_by_id(str(id))
    if not reimbursement or reimbursement.deleted_at:
        raise HTTPException(status_code=404, detail="Not found")
    return reimbursement

@router.put("/{id}", response_model=Reimbursement)
async def update_reimbursement(
    id: UUID,
    request_date: Optional[date] = Form(None),
    business_category: Optional[str] = Form(None),
    nature_of_expense: Optional[str] = Form(None),
    bill_number: Optional[str] = Form(None),
    bill_date: Optional[date] = Form(None),
    amount: Optional[float] = Form(None),
    brief_description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    gdrive_link: Optional[str] = Form(None),
    user = Depends(get_current_user),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    kwargs = {}
    if request_date is not None: kwargs["request_date"] = request_date
    if business_category is not None: kwargs["business_category"] = business_category
    if nature_of_expense is not None: kwargs["nature_of_expense"] = nature_of_expense
    if brief_description is not None: kwargs["brief_description"] = brief_description
    if bill_number is not None: kwargs["bill_number"] = bill_number
    if bill_date is not None: kwargs["bill_date"] = bill_date
    if amount is not None: kwargs["amount"] = amount

    update_data = ReimbursementUpdate(**kwargs)
    document_url = None
    if file:
        document_url = await storage_service.upload_file(file)
    return reimbursement_service.update(str(id), update_data, str(user.id), document_url=document_url, gdrive_link=gdrive_link)

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
    user = Depends(get_current_user),
    repo: AuditLogRepository = Depends(get_audit_repo)
):
    return repo.get_by_reimbursement(str(id))
