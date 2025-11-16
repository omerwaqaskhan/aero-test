"""
Email sending background tasks using Celery.

This module handles asynchronous email sending to avoid blocking HTTP requests.
"""

from ..core.celery_app import celery_app
from ..infrastructure.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_async(
    self,
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = None
):
    """
    Send email asynchronously.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email content
        text_content: Plain text email content (optional)
    
    Returns:
        bool: True if email sent successfully
    """
    try:
        email_service = EmailService()
        email_service.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email_async(
    self,
    to_email: str,
    verification_token: str,
    user_name: str = None
):
    """
    Send email verification email asynchronously.
    
    Args:
        to_email: Recipient email address
        verification_token: Email verification token
        user_name: User's name (optional)
    """
    try:
        from ..infrastructure.email_service import EmailService
        
        email_service = EmailService()
        
        # Generate verification URL
        verification_url = f"{email_service.config.base_url}/verify-email?token={verification_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Verify Your Email Address</h2>
            <p>Hello {user_name or 'User'},</p>
            <p>Please click the link below to verify your email address:</p>
            <p><a href="{verification_url}">Verify Email</a></p>
            <p>If you didn't create an account, please ignore this email.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Verify Your Email Address
        
        Hello {user_name or 'User'},
        
        Please visit the following link to verify your email address:
        {verification_url}
        
        If you didn't create an account, please ignore this email.
        """
        
        email_service.send_email(
            to_email=to_email,
            subject="Verify Your Email Address",
            html_content=html_content,
            text_content=text_content
        )
        logger.info(f"Verification email sent to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send verification email to {to_email}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_email_async(
    self,
    to_email: str,
    reset_token: str,
    user_name: str = None
):
    """
    Send password reset email asynchronously.
    
    Args:
        to_email: Recipient email address
        reset_token: Password reset token
        user_name: User's name (optional)
    """
    try:
        from ..infrastructure.email_service import EmailService
        
        email_service = EmailService()
        
        # Generate reset URL
        reset_url = f"{email_service.config.base_url}/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Reset Your Password</h2>
            <p>Hello {user_name or 'User'},</p>
            <p>You requested to reset your password. Click the link below:</p>
            <p><a href="{reset_url}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email.</p>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password
        
        Hello {user_name or 'User'},
        
        You requested to reset your password. Visit the following link:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        """
        
        email_service.send_email(
            to_email=to_email,
            subject="Reset Your Password",
            html_content=html_content,
            text_content=text_content
        )
        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send password reset email to {to_email}: {exc}")
        raise self.retry(exc=exc)

