"""Implementation helpers for AuthService - account lockout and email integration."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .models import User, LoginAttempt
from ..core.config import config
from ..infrastructure.messaging import EmailService
from ..infrastructure.db.repositories import LoginAttemptRepository, UserRepository


class AccountLockoutManager:
    """Manages account lockout logic."""
    
    def __init__(self, login_attempt_repo: LoginAttemptRepository, user_repo: UserRepository):
        self.login_attempt_repo = login_attempt_repo
        self.user_repo = user_repo
    
    async def is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked."""
        # Get recent failed attempts
        failed_attempts = await self.get_failed_login_attempts(user_id)
        
        if len(failed_attempts) >= config.max_failed_login_attempts:
            # Check if lockout period has passed
            oldest_failed = min(failed_attempts, key=lambda x: x.occurred_at)
            lockout_duration = timedelta(minutes=config.lockout_duration_minutes)
            
            if datetime.utcnow() - oldest_failed.occurred_at < lockout_duration:
                return True
        
        return False
    
    async def get_failed_login_attempts(self, user_id: str) -> List[LoginAttempt]:
        """Get recent failed login attempts."""
        window_start = datetime.utcnow() - timedelta(minutes=config.lockout_duration_minutes)
        return await self.login_attempt_repo.get_failed_attempts_since(
            user_id=user_id,
            since=window_start
        )
    
    async def lock_account(self, user_id: str) -> None:
        """Lock user account."""
        user = await self.user_repo.get_by_id(user_id)
        if user:
            user.suspend()
            await self.user_repo.update(user)
    
    async def unlock_account(self, user_id: str) -> None:
        """Unlock user account."""
        user = await self.user_repo.get_by_id(user_id)
        if user and user.is_suspended():
            user.activate()
            await self.user_repo.update(user)


class EmailIntegration:
    """Email service integration for auth flows."""
    
    def __init__(self):
        self.email_service = EmailService()
    
    async def send_verification_email(self, user: User, tenant_name: str, verification_token: str) -> bool:
        """Send email verification email."""
        try:
            return await self.email_service.send_verification_email(
                to_email=user.email,
                verification_token=verification_token,
                tenant_name=tenant_name
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send verification email: {e}")
            return False
    
    async def send_password_reset_email(self, user: User, tenant_name: str, reset_token: str) -> bool:
        """Send password reset email."""
        try:
            return await self.email_service.send_password_reset_email(
                to_email=user.email,
                reset_token=reset_token,
                tenant_name=tenant_name
            )
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False
    
    async def send_mfa_code_email(self, user: User, tenant_name: str, mfa_code: str) -> bool:
        """Send MFA code via email."""
        try:
            return await self.email_service.send_mfa_code_email(
                to_email=user.email,
                mfa_code=mfa_code,
                tenant_name=tenant_name
            )
        except Exception as e:
            print(f"Failed to send MFA code email: {e}")
            return False


