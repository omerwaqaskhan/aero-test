"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from auth_module.domain.models import User, Tenant, UserRole, UserStatus, TenantStatus
from auth_module.core.security import PasswordManager, JWTManager, MFAManager


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return User(
        id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        email="test@example.com",
        password_hash=PasswordManager.hash_password("TestPassword123!"),
        first_name="Test",
        last_name="User",
        role="user",
        status=UserStatus.ACTIVE,
        email_verified=True,
        mfa_enabled=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_tenant():
    """Create a mock tenant."""
    return Tenant(
        id=str(uuid.uuid4()),
        slug="test-tenant",
        name="Test Tenant",
        status=TenantStatus.ACTIVE,
        settings={},
        branding={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_user_repository():
    """Create a mock user repository."""
    repo = Mock()
    repo.get_by_email = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.update_password = AsyncMock()
    return repo


@pytest.fixture
def mock_tenant_repository():
    """Create a mock tenant repository."""
    repo = Mock()
    repo.get_by_slug = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    return repo


@pytest.fixture
def mock_email_service():
    """Create a mock email service."""
    service = Mock()
    service.send_email = AsyncMock(return_value=True)
    service.send_verification_email = AsyncMock(return_value=True)
    service.send_password_reset_email = AsyncMock(return_value=True)
    service.send_mfa_code_email = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    limiter = Mock()
    limiter.is_rate_limited = Mock(return_value=(False, 0, 0))
    limiter.get_rate_limit_info = Mock(return_value={"current_count": 0})
    limiter.clear_rate_limit = Mock(return_value=True)
    return limiter

