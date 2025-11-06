"""Integration tests for authentication flows."""

import pytest
from datetime import datetime
import uuid
from auth_module.core.exceptions import (
    UserEmailTakenError, PasswordTooWeakError, InvalidCredentialsError,
    AccountLockedError, EmailNotVerifiedError
)
from auth_module.core.security import PasswordManager, JWTManager


class TestRegistrationFlow:
    """Integration tests for user registration flow."""
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, test_tenant):
        """Test successful user registration end-to-end."""
        email = "newuser@example.com"
        password = "SecurePass123!"
        
        # Register user
        user, access_token, refresh_token = await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password,
            first_name="New",
            last_name="User"
        )
        
        # Assertions
        assert user is not None
        assert user.email == email
        assert user.first_name == "New"
        assert user.last_name == "User"
        assert user.tenant_id == test_tenant.id
        assert access_token is not None
        assert refresh_token is not None
        
        # Verify token is valid
        payload = JWTManager.verify_token(access_token, "access")
        assert payload["sub"] == user.id
        assert payload["email"] == email
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, test_tenant):
        """Test registration with duplicate email."""
        email = "duplicate@example.com"
        password = "SecurePass123!"
        
        # First registration
        await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password,
            first_name="First",
            last_name="User"
        )
        
        # Second registration with same email
        with pytest.raises(UserEmailTakenError):
            await auth_service.register_user(
                tenant_id=test_tenant.id,
                email=email,
                password=password,
                first_name="Second",
                last_name="User"
            )
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, auth_service, test_tenant):
        """Test registration with weak password."""
        with pytest.raises(PasswordTooWeakError):
            await auth_service.register_user(
                tenant_id=test_tenant.id,
                email="test@example.com",
                password="weak",  # Too weak
                first_name="Test",
                last_name="User"
            )


class TestLoginFlow:
    """Integration tests for user login flow."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, test_tenant):
        """Test successful login end-to-end."""
        email = "loginuser@example.com"
        password = "SecurePass123!"
        
        # Register user first
        registered_user, _, _ = await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password,
            first_name="Login",
            last_name="User"
        )
        
        # Login
        user, access_token, refresh_token = await auth_service.login_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password
        )
        
        # Assertions
        assert user is not None
        assert user.id == registered_user.id
        assert user.email == email
        assert access_token is not None
        assert refresh_token is not None
        
        # Verify token
        payload = JWTManager.verify_token(access_token, "access")
        assert payload["sub"] == user.id
    
    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, test_tenant):
        """Test login with invalid password."""
        email = "invalidpass@example.com"
        password = "SecurePass123!"
        
        # Register user
        await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password,
            first_name="Test",
            last_name="User"
        )
        
        # Try to login with wrong password
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login_user(
                tenant_id=test_tenant.id,
                email=email,
                password="WrongPassword123!"
            )
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, auth_service, test_tenant):
        """Test login with non-existent user."""
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login_user(
                tenant_id=test_tenant.id,
                email="nonexistent@example.com",
                password="SomePassword123!"
            )


class TestTokenRefreshFlow:
    """Integration tests for token refresh flow."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, test_tenant):
        """Test successful token refresh."""
        email = "refreshtoken@example.com"
        password = "SecurePass123!"
        
        # Register and login
        _, _, refresh_token = await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=password,
            first_name="Refresh",
            last_name="User"
        )
        
        # Refresh token
        new_access_token, new_refresh_token = await auth_service.refresh_token(refresh_token)
        
        # Assertions
        assert new_access_token is not None
        assert new_refresh_token is not None
        assert new_refresh_token != refresh_token  # Should be rotated
        
        # Verify new token
        payload = JWTManager.verify_token(new_access_token, "access")
        assert payload["email"] == email


class TestPasswordResetFlow:
    """Integration tests for password reset flow."""
    
    @pytest.mark.asyncio
    async def test_password_reset_flow(self, auth_service, test_tenant):
        """Test password reset flow end-to-end."""
        email = "resetpass@example.com"
        old_password = "OldPassword123!"
        new_password = "NewPassword123!"
        
        # Register user
        user, _, _ = await auth_service.register_user(
            tenant_id=test_tenant.id,
            email=email,
            password=old_password,
            first_name="Reset",
            last_name="User"
        )
        
        # Change password
        await auth_service.change_password(
            user_id=user.id,
            current_password=old_password,
            new_password=new_password
        )
        
        # Try to login with old password (should fail)
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login_user(
                tenant_id=test_tenant.id,
                email=email,
                password=old_password
            )
        
        # Login with new password (should succeed)
        logged_in_user, _, _ = await auth_service.login_user(
            tenant_id=test_tenant.id,
            email=email,
            password=new_password
        )
        
        assert logged_in_user.id == user.id


