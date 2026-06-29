from brevo import Brevo
from brevo.transactional_emails import (
    SendTransacEmailRequestSender,
    SendTransacEmailRequestToItem,
)
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.frontend_url = settings.FRONTEND_URL.rstrip('/')
        self.from_email = settings.FROM_EMAIL
        
        # Initialize Brevo client
        self.client = Brevo(api_key=settings.BREVO_API_KEY) if settings.BREVO_API_KEY else None

    def send_reimbursement_update(
        self,
        to_email: str,
        name: str,
        status: str,
        reimbursement_id: str,
        remarks: str = None,
        expected_payment_date: str = None,
        approved_amount: float = None
    ):
        if not self.client:
            logger.warning("BREVO_API_KEY is not set. Skipping email send.")
            return

        subject = f"Reimbursement Status Update: {status}"
        
        if status == "Approved":
            amount_text = f"<p><strong>Approved Amount:</strong> {approved_amount}</p>" if approved_amount is not None else ""
            html_content = f"""
            <h2>Hello {name},</h2>
            <p>Your reimbursement request has been <strong>approved</strong>.</p>
            {amount_text}
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
            self.client.transactional_emails.send_transac_email(
                html_content=html_content,
                sender=SendTransacEmailRequestSender(
                    email=self.from_email,
                    name="Leadwalnut Finance"
                ),
                subject=subject,
                to=[
                    SendTransacEmailRequestToItem(
                        email=to_email,
                        name=name
                    )
                ]
            )
            logger.info(f"Successfully sent {status} email to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via Brevo API: {str(e)}")

