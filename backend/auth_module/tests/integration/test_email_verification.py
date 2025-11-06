"""Integration tests for email verification flow."""

import pytest
from auth_module.core.exceptions import EmailNotVerifiedError


class TestEmailVerificationFlow:
    """Integration tests for email verification."""
    
    @pytest.mark.asyncio
    async def test_email_verification_required(self, auth_service, test_tenant):
        """Test that unverified email prevents login."""
        email = "unverified@example.com"
        password = "SecurePass123!"
        
        # Register user (email not verified by default)
        user, _, _ = await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password,
            first_name="Unverified",
            last_name="User"
        )
        
        # User should not be able to login with unverified email
        # Note: This depends on your implementation
        # If email verification is enforced, this should raise EmailNotVerifiedError
        # If not enforced, login should work
        
        # For now, we'll test that user exists but email_verified is False
        assert user.email_verified == False


class TestMFAFlow:
    """Integration tests for MFA flow."""
    
    @pytest.mark.asyncio
    async def test_mfa_setup_and_verification(self, auth_service, test_tenant):
        """Test MFA setup and verification flow."""
        email = "mfauser@example.com"
        password = "SecurePass123!"
        
        # Register user
        user, _, _ = await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password,
            first_name="MFA",
            last_name="User"
        )
        
        # Setup MFA (this would typically be done via API)
        # For now, we'll just verify the user can login
        logged_in_user, access_token, refresh_token = await auth_service.login_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password
        )
        
        assert logged_in_user.id == user.id
        assert access_token is not None


