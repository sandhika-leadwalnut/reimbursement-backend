import resend
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        resend.api_key = settings.RESEND_API_KEY
        self.frontend_url = settings.FRONTEND_URL.rstrip('/')
        # When testing without a verified domain, onboarding@resend.dev is allowed.
        # But normally you would use your verified domain here.
        self.from_email = "onboarding@resend.dev"

    def send_reimbursement_update(
        self,
        to_email: str,
        name: str,
        status: str,
        reimbursement_id: str,
        remarks: str = None,
        expected_payment_date: str = None
    ):
        if not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY is not set. Skipping email send.")
            return

        subject = f"Reimbursement Status Update: {status}"
        
        if status == "Approved":
            html_content = f"""
            <h2>Hello {name},</h2>
            <p>Your reimbursement request has been <strong>approved</strong>.</p>
            <p><strong>Expected date of payment:</strong> {expected_payment_date}</p>
            <p>Remarks: {remarks or 'None'}</p>
            """
        elif status == "Rejected":
            html_content = f"""
            <h2>Hello {name},</h2>
            <p>Your reimbursement request has been <strong>rejected</strong>.</p>
            <p><strong>Reason/Remarks:</strong> {remarks or 'None'}</p>
            """
        elif status == "Need Further Clarification":
            edit_link = f"{self.frontend_url}/reimbursement/{reimbursement_id}/edit"
            html_content = f"""
            <h2>Hello {name},</h2>
            <p>Your reimbursement request needs <strong>further clarification</strong>.</p>
            <p><strong>Admin Remarks:</strong> {remarks or 'None'}</p>
            <p>Please update your request by clicking the link below:</p>
            <p><a href="{edit_link}">Edit Reimbursement</a></p>
            """
        else:
            return

        try:
            params = {
                "from": self.from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content
            }
            resend.Emails.send(params)
            logger.info(f"Successfully sent {status} email to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
