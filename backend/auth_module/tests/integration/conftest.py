"""Pytest configuration and fixtures for integration tests."""

import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from auth_module.infrastructure.db.database import Base
from auth_module.infrastructure.db.models import TenantModel, UserModel
from auth_module.core.config import config
from auth_module.domain.services import AuthService, TenantService, UserService
from auth_module.infrastructure.db.repositories import (
    TenantRepository, UserRepository, RefreshTokenRepository, LoginAttemptRepository
)


# Use in-memory SQLite for integration tests
TEST_DATABASE_URL = "sqlite:///:memory:"


# Mock the config to use test database
@pytest.fixture(scope="function", autouse=True)
def mock_config():
    """Mock config for integration tests."""
    from unittest.mock import patch
    with patch('auth_module.core.config.config') as mock_config:
        mock_config.database_url = TEST_DATABASE_URL
        mock_config.redis_url = "redis://localhost:6379/0"
        mock_config.jwt_secret_key = "test-secret-key"
        mock_config.jwt_algorithm = "HS256"
        mock_config.jwt_access_token_expire_minutes = 60
        mock_config.jwt_refresh_token_expire_days = 30
        mock_config.jwt_issuer = "test-issuer"
        mock_config.jwt_audience = "test-audience"
        mock_config.password_min_length = 8
        mock_config.password_max_length = 128
        mock_config.password_require_uppercase = False
        mock_config.password_require_lowercase = False
        mock_config.password_require_numbers = False
        mock_config.password_require_special_chars = False
        mock_config.password_forbidden_patterns = ["password", "123456", "qwerty", "admin"]
        mock_config.bcrypt_rounds = 12
        yield mock_config


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session."""
    from auth_module.infrastructure.db.database import Base as AuthBase
    from auth_module.infrastructure.db.models import TenantModel, UserModel
    
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    AuthBase.metadata.create_all(engine)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        AuthBase.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_tenant(test_db):
    """Create a test tenant."""
    tenant = TenantModel(
        id="test-tenant-id",
        slug="test-tenant",
        name="Test Tenant",
        status="active",
        settings={},
        branding={}
    )
    test_db.add(tenant)
    test_db.commit()
    test_db.refresh(tenant)
    
    return tenant


@pytest.fixture(scope="function")
def tenant_repository(test_db):
    """Create a tenant repository."""
    return TenantRepository(test_db)


@pytest.fixture(scope="function")
def user_repository(test_db):
    """Create a user repository."""
    return UserRepository(test_db)


@pytest.fixture(scope="function")
def auth_service(test_db, tenant_repository):
    """Create an AuthService instance with test database."""
    from unittest.mock import Mock, patch, MagicMock
    
    # Mock rate limiter
    mock_rate_limiter = Mock()
    mock_rate_limiter.is_rate_limited = Mock(return_value=(False, 0, 0))
    
    # Create service with mocked dependencies
    with patch('auth_module.domain.services.RateLimiter', return_value=mock_rate_limiter):
        with patch('auth_module.domain.services.create_engine'):
            with patch('auth_module.domain.services.sessionmaker'):
                service = AuthService()
                # Override repository with test repository
                service.user_repository = UserRepository(test_db)
                service.rate_limiter = mock_rate_limiter
                # Mock helper methods
                service._is_account_locked = MagicMock(return_value=False)
                service._get_failed_login_attempts = MagicMock(return_value=[])
                service._lock_account = MagicMock()
                service._get_refresh_token = MagicMock(return_value=None)
                service._get_user_by_id = MagicMock(return_value=None)
                service._get_user_permissions = MagicMock(return_value=[])
                service._log_login_attempt = MagicMock()
                service._revoke_all_refresh_tokens = MagicMock()
                service._log_audit_event = MagicMock()
                return service


@pytest.fixture(scope="function")
def tenant_service(test_db, tenant_repository):
    """Create a TenantService instance."""
    service = TenantService()
    service.tenant_repository = tenant_repository
    return service


@pytest.fixture(scope="function")
def user_service(test_db, user_repository):
    """Create a UserService instance."""
    service = UserService()
    service.user_repository = user_repository
    return service

