from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import List
from uuid import UUID
from schemas.reimbursement import Reimbursement, DashboardMetrics
from models.enums import ReimbursementStatus
from services.reimbursement import ReimbursementService
from services.zoho import ZohoExpenseService
from api.dependencies.auth import get_current_admin, get_db_client
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
    # expected_payment_date is intentionally absent. It is derived from the payment
    # cycle at submission (utils/payment_calc.py) and is not admin-editable:
    # overriding it desynced the payment sheet from the actual payment run.

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
            approved_amount=payload.approved_amount
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
    background_tasks: BackgroundTasks,
    admin = Depends(get_current_admin),
    reimbursement_service: ReimbursementService = Depends(get_reimbursement_service),
    email_service: EmailService = Depends(get_email_service)
):
    result = reimbursement_service.update_status(
        str(id),
        ReimbursementStatus.paid,
        str(admin.id),
        paid_on=payload.paid_on.isoformat()
    )

    # Amount paid is the approved amount, which may be lower than the claim.
    background_tasks.add_task(
        email_service.send_payment_confirmation,
        result.employee_email,
        result.employee_name,
        result.bill_number,
        result.nature_of_expense,
        result.approved_amount if result.approved_amount is not None else result.amount,
        result.paid_on.isoformat() if result.paid_on else payload.paid_on.isoformat()
    )

    return result

@router.get("/reimbursements", response_model=List[Reimbursement])
def get_all_reimbursements(
    admin = Depends(get_current_admin),
    repo: ReimbursementRepository = Depends(get_reimbursement_repo)
):
    return repo.get_active()

@router.get("/bank-details")
def get_bank_details(
    admin = Depends(get_current_admin),
    client = Depends(get_db_client)
):
    """Bank details for the payment sheet export. Served via the backend because
    the frontend's Supabase client is unauthenticated (auth uses HttpOnly cookies),
    so RLS would return no rows on direct browser queries."""
    employees = client.table("employee_bank_details").select(
        "employee_name, employee_email, bank_name, ifsc_code, account_number"
    ).execute()
    vendors = client.table("vendor_bank_details").select(
        "vendor_name, vendor_email, bank_name, ifsc_code, account_number"
    ).execute()
    return {"employees": employees.data or [], "vendors": vendors.data or []}

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
        paid=0,
        total_amount=0.0,
        total_approved_amount=0.0,
        total_paid_amount=0.0
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
        elif r.status == ReimbursementStatus.paid:
            metrics.paid += 1
            metrics.total_paid_amount += r.approved_amount or r.amount

    return metrics
