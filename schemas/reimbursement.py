from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from models.enums import ReimbursementStatus

class ReimbursementBase(BaseModel):
    request_date: date
    business_category: str
    nature_of_expense: str
    brief_description: Optional[str] = None
    bill_number: str
    bill_date: date
    amount: float = Field(..., gt=0)

class ReimbursementCreate(ReimbursementBase):
    pass

class ReimbursementUpdate(BaseModel):
    request_date: Optional[date] = None
    business_category: Optional[str] = None
    nature_of_expense: Optional[str] = None
    brief_description: Optional[str] = None
    bill_number: Optional[str] = None
    bill_date: Optional[date] = None
    amount: Optional[float] = Field(None, gt=0)

class Reimbursement(ReimbursementBase):
    id: UUID
    employee_id: UUID
    employee_name: str
    employee_email: EmailStr
    submission_date: date
    document_url: Optional[str] = None
    gdrive_link: Optional[str] = None
    status: ReimbursementStatus
    reviewed_accepted: bool
    expected_payment_date: Optional[date] = None
    approved_amount: Optional[float] = None
    paid_on: Optional[date] = None
    remarks: Optional[str] = None
    zoho_expense_id: Optional[str] = None
    zoho_sync_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DashboardMetrics(BaseModel):
    total_requests: int
    pending_review: int
    under_review: int
    approved: int
    rejected: int
    paid: int
    total_amount: float
    total_approved_amount: float
    total_paid_amount: float
