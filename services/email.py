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

    def _send(self, to_email: str, name: str, subject: str, html_content: str, label: str):
        """Shared Brevo send. Never raises: these run as BackgroundTasks and an email
        failure must not affect the request that triggered it."""
        if not self.client:
            logger.warning("BREVO_API_KEY is not set. Skipping email send.")
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
            logger.info(f"Successfully sent {label} email to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {to_email} via Brevo API: {str(e)}")

    def send_submission_confirmation(
        self,
        to_email: str,
        name: str,
        bill_number: str = None,
        nature_of_expense: str = None,
        amount: float = None,
        request_date: str = None,
        expected_payment_date: str = None
    ):
        """Sent when an employee files a new request, so they have a record of it."""
        html_content = f"""
        <h2>Hello {name},</h2>
        <p>We've received your reimbursement request. It is now pending review by the finance team.</p>
        <p><strong>Bill Number:</strong> {bill_number}</p>
        <p><strong>Nature of Expense:</strong> {nature_of_expense}</p>
        <p><strong>Amount Claimed:</strong> {amount}</p>
        <p><strong>Submitted On:</strong> {request_date}</p>
        <p><strong>Expected Payment Date:</strong> {expected_payment_date}</p>
        <p>You will receive an update once your request has been reviewed.</p>
        """
        self._send(to_email, name, "Reimbursement Request Received", html_content, "Submission")

    def send_payment_confirmation(
        self,
        to_email: str,
        name: str,
        bill_number: str = None,
        nature_of_expense: str = None,
        amount_paid: float = None,
        paid_on: str = None
    ):
        """Sent when an admin marks a request paid. `amount_paid` is the approved
        amount, which may be lower than the amount originally claimed."""
        html_content = f"""
        <h2>Hello {name},</h2>
        <p>Your reimbursement has been <strong>paid</strong>.</p>
        <p><strong>Bill Number:</strong> {bill_number}</p>
        <p><strong>Nature of Expense:</strong> {nature_of_expense}</p>
        <p><strong>Amount Paid:</strong> {amount_paid}</p>
        <p><strong>Payment Date:</strong> {paid_on}</p>
        <p>The amount has been released to your registered bank account.</p>
        """
        self._send(to_email, name, "Reimbursement Paid", html_content, "Paid")

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

