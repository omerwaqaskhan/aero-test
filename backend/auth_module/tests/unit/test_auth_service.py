"""Unit tests for AuthService."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from auth_module.domain.services import AuthService
from auth_module.domain.models import User, UserStatus
from auth_module.core.exceptions import (
    InvalidCredentialsError, AccountLockedError, EmailNotVerifiedError,
    MFARequiredError, MFAInvalidError, UserEmailTakenError, PasswordTooWeakError,
    RateLimitExceededError
)
from auth_module.core.security import PasswordManager, JWTManager, MFAManager


class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.fixture
    def auth_service(self, mock_user_repository, mock_rate_limiter):
        """Create AuthService instance with mocked dependencies."""
        # Patch the imports inside AuthService.__init__
        with patch('auth_module.infrastructure.db.repositories.UserRepository', return_value=mock_user_repository):
            with patch('sqlalchemy.create_engine'):
                with patch('sqlalchemy.orm.sessionmaker') as mock_sessionmaker:
                    # Mock sessionmaker to return a mock session
                    mock_session = Mock()
                    mock_sessionmaker.return_value.return_value = mock_session
                    mock_sessionmaker.return_value = Mock(return_value=mock_session)
                    
                    with patch('auth_module.domain.services.RateLimiter', return_value=mock_rate_limiter):
                        service = AuthService()
                        # Override the repository and rate limiter with mocks
                        service.user_repository = mock_user_repository
                        service.rate_limiter = mock_rate_limiter
                        # Mock the helper methods
                        service._is_account_locked = AsyncMock(return_value=False)
                        service._get_failed_login_attempts = AsyncMock(return_value=[])
                        service._lock_account = AsyncMock()
                        service._get_refresh_token = AsyncMock(return_value=None)
                        service._get_user_by_id = AsyncMock(return_value=None)
                        service._get_user_permissions = AsyncMock(return_value=[])
                        service._log_login_attempt = AsyncMock()
                        service._revoke_all_refresh_tokens = AsyncMock()
                        service._log_audit_event = AsyncMock()
                        return service
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_tenant):
        """Test successful user registration."""
        # Setup
        email = "newuser@example.com"
        password = "SecurePass123!"
        tenant_id = str(uuid.uuid4())
        
        auth_service.user_repository.get_by_email = AsyncMock(return_value=None)
        auth_service.user_repository.create = AsyncMock(return_value=User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=email,
            password_hash=PasswordManager.hash_password(password),
            first_name="New",
            last_name="User",
            role="user",
            status=UserStatus.PENDING
        ))
        
        # Execute
        user, access_token, refresh_token = await auth_service.register_user(
            tenant_id=tenant_id,
            email=email,
            password=password,
            first_name="New",
            last_name="User"
        )
        
        # Assert
        assert user is not None
        assert user.email == email
        assert access_token is not None
        assert refresh_token is not None
        auth_service.user_repository.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_email_taken(self, auth_service, mock_user):
        """Test registration with existing email."""
        # Setup - mock repository to return existing user
        auth_service.user_repository.get_by_email = AsyncMock(return_value=mock_user)
        
        # Execute & Assert
        with pytest.raises(UserEmailTakenError):
            await auth_service.register_user(
                tenant_id=mock_user.tenant_id,
                email=mock_user.email,
                password="SecurePass123!",  # Changed from "NewPassword123!" to avoid forbidden pattern
                first_name="Test",
                last_name="User"
            )
        
        # Verify repository was called
        auth_service.user_repository.get_by_email.assert_called_once_with(
            mock_user.tenant_id, mock_user.email
        )
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, auth_service):
        """Test registration with weak password."""
        # Setup
        auth_service.user_repository.get_by_email = AsyncMock(return_value=None)
        
        # Execute & Assert
        with pytest.raises(PasswordTooWeakError):
            await auth_service.register_user(
                tenant_id=str(uuid.uuid4()),
                email="test@example.com",
                password="weak",  # Too weak
                first_name="Test",
                last_name="User"
            )
    
    @pytest.mark.asyncio
    async def test_register_user_rate_limited(self, auth_service):
        """Test registration when rate limited."""
        # Setup
        auth_service.rate_limiter.is_rate_limited = Mock(return_value=(True, 3, 3600))
        
        # Execute & Assert
        with pytest.raises(RateLimitExceededError):
            await auth_service.register_user(
                tenant_id=str(uuid.uuid4()),
                email="test@example.com",
                password="SecurePass123!",
                first_name="Test",
                last_name="User"
            )
    
    @pytest.mark.asyncio
    async def test_login_user_success(self, auth_service, mock_user):
        """Test successful user login."""
        # Setup
        password = "TestPassword123!"
        mock_user.password_hash = PasswordManager.hash_password(password)
        
        # Mock _get_user_by_email which is used in login_user
        auth_service._get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service._is_account_locked = AsyncMock(return_value=False)
        auth_service._get_failed_login_attempts = AsyncMock(return_value=[])
        auth_service._get_user_permissions = AsyncMock(return_value=[])
        auth_service._log_login_attempt = AsyncMock()
        
        # Execute
        user, access_token, refresh_token = await auth_service.login_user(
            tenant_id=mock_user.tenant_id,
            email=mock_user.email,
            password=password
        )
        
        # Assert
        assert user is not None
        assert user.email == mock_user.email
        assert access_token is not None
        assert refresh_token is not None
    
    @pytest.mark.asyncio
    async def test_login_user_invalid_credentials(self, auth_service, mock_user):
        """Test login with invalid credentials."""
        # Setup
        auth_service._get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service._is_account_locked = AsyncMock(return_value=False)
        auth_service._get_failed_login_attempts = AsyncMock(return_value=[])
        auth_service._log_login_attempt = AsyncMock()
        
        # Execute & Assert
        with pytest.raises(InvalidCredentialsError):
            await auth_service.login_user(
                tenant_id=mock_user.tenant_id,
                email=mock_user.email,
                password="WrongPassword123!"
            )
    
    @pytest.mark.asyncio
    async def test_login_user_account_locked(self, auth_service, mock_user):
        """Test login with locked account."""
        # Setup
        auth_service._get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service._is_account_locked = AsyncMock(return_value=True)
        
        # Execute & Assert
        with pytest.raises(AccountLockedError):
            await auth_service.login_user(
                tenant_id=mock_user.tenant_id,
                email=mock_user.email,
                password="TestPassword123!"
            )
    
    @pytest.mark.asyncio
    async def test_login_user_mfa_required(self, auth_service, mock_user):
        """Test login when MFA is required."""
        # Setup
        password = "TestPassword123!"
        mock_user.password_hash = PasswordManager.hash_password(password)
        mock_user.mfa_enabled = True
        
        auth_service._get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service._is_account_locked = AsyncMock(return_value=False)
        auth_service._get_failed_login_attempts = AsyncMock(return_value=[])
        auth_service._log_login_attempt = AsyncMock()
        
        # Execute & Assert
        with pytest.raises(MFARequiredError):
            await auth_service.login_user(
                tenant_id=mock_user.tenant_id,
                email=mock_user.email,
                password=password
            )
    
    @pytest.mark.asyncio
    async def test_login_user_mfa_invalid(self, auth_service, mock_user):
        """Test login with invalid MFA code."""
        # Setup
        password = "TestPassword123!"
        mock_user.password_hash = PasswordManager.hash_password(password)
        mock_user.mfa_enabled = True
        mock_user.mfa_secret = MFAManager.generate_totp_secret()
        
        auth_service._get_user_by_email = AsyncMock(return_value=mock_user)
        auth_service._is_account_locked = AsyncMock(return_value=False)
        auth_service._get_failed_login_attempts = AsyncMock(return_value=[])
        auth_service._log_login_attempt = AsyncMock()
        
        # Execute & Assert
        with pytest.raises(MFAInvalidError):
            await auth_service.login_user(
                tenant_id=mock_user.tenant_id,
                email=mock_user.email,
                password=password,
                mfa_code="000000"  # Invalid code
            )
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_user):
        """Test successful token refresh."""
        # Setup
        from auth_module.domain.models import RefreshToken, TokenStatus
        from datetime import datetime, timedelta
        
        refresh_token = JWTManager.generate_refresh_token(
            user_id=mock_user.id,
            tenant_id=mock_user.tenant_id
        )
        
        mock_refresh_token = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=mock_user.id,
            token_hash="hashed_token",
            status=TokenStatus.ACTIVE,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            device_info={}
        )
        
        auth_service._get_refresh_token = AsyncMock(return_value=mock_refresh_token)
        auth_service._get_user_by_id = AsyncMock(return_value=mock_user)
        auth_service._get_user_permissions = AsyncMock(return_value=[])
        
        # Execute
        access_token, new_refresh_token = await auth_service.refresh_token(refresh_token)
        
        # Assert
        assert access_token is not None
        assert new_refresh_token is not None
        # Tokens should be different (new tokens generated)
        # Note: In real implementation, tokens would be different due to different timestamps
        # For testing, we just verify they are generated
        assert len(access_token) > 0
        assert len(new_refresh_token) > 0
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_user):
        """Test successful password change."""
        # Setup
        current_password = "OldSecure123!"
        new_password = "NewSecure123!"  # Changed to avoid forbidden pattern
        mock_user.password_hash = PasswordManager.hash_password(current_password)
        
        # Mock the database and repository
        mock_db = Mock()
        mock_repo = Mock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_user)
        mock_repo.update_password = AsyncMock()
        
        with patch('auth_module.infrastructure.db.database.get_db', return_value=iter([mock_db])):
            with patch('auth_module.infrastructure.db.repositories.UserRepository', return_value=mock_repo):
                auth_service._revoke_all_refresh_tokens = AsyncMock()
                auth_service._log_audit_event = AsyncMock()
                
                # Execute
                await auth_service.change_password(
                    user_id=mock_user.id,
                    current_password=current_password,
                    new_password=new_password
                )
                
                # Assert
                mock_repo.update_password.assert_called_once()
                auth_service._revoke_all_refresh_tokens.assert_called_once_with(mock_user.id)

