from enum import Enum

class UserRole(str, Enum):
    employee = "employee"
    admin = "admin"

class ReimbursementStatus(str, Enum):
    pending_review = "Pending Review"
    under_review = "Under Review"
    approved = "Approved"
    sent_to_zoho = "Sent To Zoho"
    paid = "Paid"
    rejected = "Rejected"

class AuditAction(str, Enum):
    create = "Create"
    update = "Update"
    approve = "Approve"
    reject = "Reject"
    zoho_sync = "Zoho Sync"
    payment_update = "Payment Update"
    soft_delete = "Soft Delete"
    restore = "Restore"
