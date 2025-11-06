"""Unit tests for UserService."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid

from auth_module.domain.services import UserService
from auth_module.domain.models import User, UserStatus, UserRole
from auth_module.core.exceptions import UserNotFoundError, UserEmailTakenError


class TestUserService:
    """Test cases for UserService."""
    
    @pytest.fixture
    def user_service(self, mock_user_repository):
        """Create UserService instance with mocked dependencies."""
        service = UserService()
        service.user_repository = mock_user_repository
        return service
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_tenant):
        """Test successful user creation."""
        email = "newuser@example.com"
        
        # Mock the internal method
        user_service._get_user_by_email = AsyncMock(return_value=None)
        
        # Create user object that will be returned
        created_user = User(
            id=str(uuid.uuid4()),
            tenant_id=mock_tenant.id,
            email=email,
            password_hash=None,
            first_name="New",
            last_name="User",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock repository if needed
        user_service.user_repository = Mock()
        
        # The create_user method creates a User object and returns it
        # We need to patch the method to return our mock user
        with patch.object(user_service, '_get_user_by_email', return_value=None):
            with patch('auth_module.domain.services.AuditLogger.log_security_event'):
                user = await user_service.create_user(
                    tenant_id=mock_tenant.id,
                    email=email,
                    first_name="New",
                    last_name="User",
                    created_by="admin-user-id"
                )
                
                assert user is not None
                assert user.email == email
                assert user.tenant_id == mock_tenant.id
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_tenant, mock_user):
        """Test user creation with duplicate email."""
        user_service._get_user_by_email = AsyncMock(return_value=mock_user)
        
        with pytest.raises(UserEmailTakenError):
            await user_service.create_user(
                tenant_id=mock_tenant.id,
                email=mock_user.email,
                first_name="Test",
                last_name="User",
                created_by="admin-user-id"
            )
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_user):
        """Test getting user by ID."""
        user_service.user_repository.get_by_id = AsyncMock(return_value=mock_user)
        
        user = await user_service.get_user_by_id(mock_user.id)
        
        assert user is not None
        assert user.id == mock_user.id
        assert user.email == mock_user.email
        user_service.user_repository.get_by_id.assert_called_once_with(mock_user.id)
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service):
        """Test getting non-existent user."""
        user_id = str(uuid.uuid4())
        user_service.user_repository.get_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(UserNotFoundError):
            await user_service.get_user_by_id(user_id)
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_user):
        """Test successful user update."""
        updated_first_name = "Updated"
        updated_last_name = "Name"
        
        # Mock the internal method
        user_service._get_user_by_id = AsyncMock(return_value=mock_user)
        
        # Update the mock user's fields
        mock_user.first_name = updated_first_name
        mock_user.last_name = updated_last_name
        
        # Mock AuditLogger
        with patch('auth_module.domain.services.AuditLogger.log_security_event'):
            result = await user_service.update_user(
                user_id=mock_user.id,
                updates={"first_name": updated_first_name, "last_name": updated_last_name},
                updated_by="admin-user-id"
            )
            
            assert result.first_name == updated_first_name
            assert result.last_name == updated_last_name
    
    @pytest.mark.asyncio
    async def test_update_user_not_found(self, user_service):
        """Test updating non-existent user."""
        user_id = str(uuid.uuid4())
        user_service._get_user_by_id = AsyncMock(return_value=None)
        
        with pytest.raises(UserNotFoundError):
            await user_service.update_user(
                user_id=user_id,
                updates={"first_name": "New Name"},
                updated_by="admin-user-id"
            )

