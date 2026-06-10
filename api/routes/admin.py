from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import List
from uuid import UUID
from schemas.reimbursement import Reimbursement, DashboardMetrics
from models.enums import ReimbursementStatus
from services.reimbursement import ReimbursementService
from services.zoho import ZohoExpenseService
from api.dependencies.auth import get_current_admin
from api.dependencies.services import get_reimbursement_service, get_zoho_service, get_reimbursement_repo
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
            ReimbursementStatus.sent_to_zoho,
            admin_id,
            zoho_expense_id=zoho_id,
            zoho_sync_status="success"
        )
    except Exception as e:
        reimbursement_service.update_status(
            str(reimbursement.id),
            ReimbursementStatus.approved,
            admin_id,
            zoho_sync_status="failed",
            remarks=str(e)
        )

@router.post("/reimbursements/{id}/approve", response_model=Reimbursement)
def approve_reimbursement(
    id: UUID,
    background_tasks: BackgroundTasks,
    admin = Depends(get_current_admin),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service),
    zoho_service: ZohoExpenseService = Depends(get_zoho_service)
):
    result = reimbursement_service.update_status(
        str(id),
        ReimbursementStatus.approved,
        str(admin.id),
        reviewed_accepted=True
    )
    background_tasks.add_task(run_zoho_sync, result, zoho_service, reimbursement_service, str(admin.id))
    return result

@router.post("/reimbursements/{id}/reject", response_model=Reimbursement)
def reject_reimbursement(
    id: UUID,
    admin = Depends(get_current_admin),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service)
):
    return reimbursement_service.update_status(
        str(id),
        ReimbursementStatus.rejected,
        str(admin.id),
        reviewed_accepted=False
    )

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
        ReimbursementStatus.paid,
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
        sent_to_zoho=0,
        paid=0,
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
        elif r.status == ReimbursementStatus.sent_to_zoho:
            metrics.sent_to_zoho += 1
        elif r.status == ReimbursementStatus.paid:
            metrics.paid += 1
        elif r.status == ReimbursementStatus.rejected:
            metrics.rejected += 1

    return metrics
