from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import List
from uuid import UUID
from schemas.reimbursement import Reimbursement, DashboardMetrics
from models.enums import ReimbursementStatus
from services.reimbursement import ReimbursementService
from services.zoho import ZohoExpenseService
from api.dependencies.auth import get_current_admin
from api.dependencies.services import get_reimbursement_service, get_zoho_service, get_reimbursement_repo, get_email_service
from services.email import EmailService
from repositories.impl import ReimbursementRepository
import asyncio
from datetime import date
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

async def run_zoho_sync(reimbursement: Reimbursement, zoho_service: ZohoExpenseService, reimbursement_service: ReimbursementService, admin_id: str):
    try:
        response = await zoho_service.sync_expense(reimbursement)
        zoho_id = response.get("expense", {}).get("expense_id")
        reimbursement_service.update_status(
            str(reimbursement.id),
            ReimbursementStatus.approved,
            admin_id,
            zoho_expense_id=zoho_id,
            zoho_sync_status="success"
        )
    except Exception as e:
        updated_remarks = f"{reimbursement.remarks or ''}\n[Zoho Sync Error]: {str(e)}".strip()
        reimbursement_service.update_status(
            str(reimbursement.id),
            ReimbursementStatus.approved,
            admin_id,
            zoho_sync_status="failed",
            remarks=updated_remarks
        )

class StatusUpdateRequest(BaseModel):
    status: str
    remarks: str | None = None
    approved_amount: float | None = None
    expected_payment_date: str | None = None

@router.put("/reimbursements/{id}/status", response_model=Reimbursement)
def update_reimbursement_status(
    id: UUID,
    payload: StatusUpdateRequest,
    background_tasks: BackgroundTasks,
    admin = Depends(get_current_admin),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service),
    zoho_service: ZohoExpenseService = Depends(get_zoho_service),
    email_service: EmailService = Depends(get_email_service)
):
    if payload.status == "Approved":
        result = reimbursement_service.update_status(
            str(id),
            ReimbursementStatus.approved,
            str(admin.id),
            reviewed_accepted=True,
            remarks=payload.remarks,
            approved_amount=payload.approved_amount,
            expected_payment_date=payload.expected_payment_date
        )
        background_tasks.add_task(run_zoho_sync, result, zoho_service, reimbursement_service, str(admin.id))
        
        background_tasks.add_task(
            email_service.send_reimbursement_update,
            result.employee_email,
            result.employee_name,
            "Approved",
            str(result.id),
            result.remarks,
            result.expected_payment_date.isoformat() if result.expected_payment_date else None,
            result.approved_amount
        )
        return result
    elif payload.status == "Rejected":
        result = reimbursement_service.update_status(
            str(id),
            ReimbursementStatus.rejected,
            str(admin.id),
            reviewed_accepted=False,
            remarks=payload.remarks
        )
        background_tasks.add_task(
            email_service.send_reimbursement_update,
            result.employee_email,
            result.employee_name,
            "Rejected",
            str(result.id),
            result.remarks
        )
        return result
    elif payload.status == "Under Review":
        result = reimbursement_service.update_status(
            str(id),
            ReimbursementStatus.under_review,
            str(admin.id),
            reviewed_accepted=False,
            remarks=payload.remarks
        )
        background_tasks.add_task(
            email_service.send_reimbursement_update,
            result.employee_email,
            result.employee_name,
            "Need Further Clarification",
            str(result.id),
            result.remarks
        )
        return result
    raise HTTPException(status_code=400, detail="Invalid status")

class MarkPaidRequest(BaseModel):
    paid_on: date

@router.post("/reimbursements/{id}/mark-paid", response_model=Reimbursement)
def mark_paid(
    id: UUID,
    payload: MarkPaidRequest,
    admin = Depends(get_current_admin),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service)
):
    return reimbursement_service.update_status(
        str(id),
        ReimbursementStatus.approved,
        str(admin.id),
        paid_on=payload.paid_on
    )

@router.get("/reimbursements", response_model=List[Reimbursement])
def get_all_reimbursements(
    admin = Depends(get_current_admin),
    repo: ReimbursementRepository = Depends(get_reimbursement_repo)
):
    return repo.get_active()

@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(
    admin = Depends(get_current_admin),
    repo: ReimbursementRepository = Depends(get_reimbursement_repo)
):
    active = repo.get_active()
    
    metrics = DashboardMetrics(
        total_requests=len(active),
        pending_review=0,
        under_review=0,
        approved=0,
        rejected=0,
        total_amount=0.0,
        total_approved_amount=0.0
    )

    for r in active:
        metrics.total_amount += r.amount
        if r.approved_amount:
            metrics.total_approved_amount += r.approved_amount

        if r.status == ReimbursementStatus.pending_review:
            metrics.pending_review += 1
        elif r.status == ReimbursementStatus.under_review:
            metrics.under_review += 1
        elif r.status == ReimbursementStatus.approved:
            metrics.approved += 1
        elif r.status == ReimbursementStatus.rejected:
            metrics.rejected += 1

    return metrics
