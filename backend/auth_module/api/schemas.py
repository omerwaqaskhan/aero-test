"""Pydantic schemas for API request/response models."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserStatus(str, Enum):
    """User status enum."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, Enum):
    """User role enum."""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    USER = "user"


class TenantStatus(str, Enum):
    """Tenant status enum."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


# Base response schemas
class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    data: Any
    meta: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: Dict[str, Any]


class PaginationResponse(BaseModel):
    """Pagination metadata."""
    page: int
    limit: int
    total: int
    pages: int


# Authentication schemas
class RegisterRequest(BaseModel):
    """User registration request."""
    tenant_slug: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.USER
    invitation_code: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""
    tenant_slug: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)
    device_info: Optional[Dict[str, Any]] = None


class RefreshTokenRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    tenant_slug: str = Field(..., min_length=1, max_length=50)
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class MFASetupRequest(BaseModel):
    """MFA setup request."""
    method: str = Field(..., pattern="^(totp|sms|email)$")


class MFAVerifyRequest(BaseModel):
    """MFA verification request."""
    code: str = Field(..., min_length=6, max_length=6)
    backup_code: Optional[str] = None


class SocialLoginRequest(BaseModel):
    """Social login request."""
    tenant_slug: str = Field(..., min_length=1, max_length=50)
    provider: str = Field(..., pattern="^(google|facebook|apple)$")
    access_token: str


class LogoutRequest(BaseModel):
    """Logout request."""
    refresh_token: str
    revoke_all: bool = False


# Tenant schemas
class CreateTenantRequest(BaseModel):
    """Create tenant request."""
    slug: str = Field(..., min_length=1, max_length=50, pattern="^[a-z0-9-]+$")
    name: str = Field(..., min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    subdomain: Optional[str] = Field(None, max_length=100)
    settings: Dict[str, Any] = Field(default_factory=dict)
    branding: Dict[str, Any] = Field(default_factory=dict)


class UpdateTenantRequest(BaseModel):
    """Update tenant request."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    subdomain: Optional[str] = Field(None, max_length=100)
    status: Optional[TenantStatus] = None
    settings: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None


# User schemas
class CreateUserRequest(BaseModel):
    """Create user request."""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.USER
    send_invitation: bool = True


class UpdateUserRequest(BaseModel):
    """Update user request."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class AssignRoleRequest(BaseModel):
    """Assign role request."""
    role_id: str
    expires_at: Optional[datetime] = None


# Response schemas
class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    email_verified: bool
    mfa_enabled: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantResponse(BaseModel):
    """Tenant response."""
    id: str
    slug: str
    name: str
    domain: Optional[str]
    subdomain: Optional[str]
    status: TenantStatus
    settings: Dict[str, Any]
    branding: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    """Authentication response."""
    user: UserResponse
    tenant: TenantResponse
    tokens: TokenResponse


class MFASetupResponse(BaseModel):
    """MFA setup response."""
    qr_code: Optional[str] = None
    backup_codes: List[str] = []
    secret: Optional[str] = None


class RoleResponse(BaseModel):
    """Role response."""
    id: str
    name: str
    description: str
    permissions: List[str]
    is_system_role: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserRoleResponse(BaseModel):
    """User role assignment response."""
    id: str
    role: RoleResponse
    assigned_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class LoginAttemptResponse(BaseModel):
    """Login attempt response."""
    id: str
    email: str
    ip_address: str
    success: bool
    reason: str
    occurred_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Audit log response."""
    id: str
    action: str
    resource: str
    metadata: Dict[str, Any]
    occurred_at: datetime
    
    class Config:
        from_attributes = True


# Health check schemas
class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, str]


class MetricsResponse(BaseModel):
    """Metrics response."""
    active_users: int
    failed_logins: int
    token_validations: int
    tenant_count: int
    cache_hit_rate: float
    response_times: Dict[str, float]


# Validation helpers
class PasswordValidator:
    """Password validation helper - uses PasswordManager from core.security."""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength using PasswordManager."""
        from ..core.security import PasswordManager
        return PasswordManager.validate_password_strength(password)


# Custom validators
def validate_tenant_slug(slug: str) -> str:
    """Validate tenant slug format."""
    import re
    if not re.match(r"^[a-z0-9-]+$", slug):
        raise ValueError("Tenant slug must contain only lowercase letters, numbers, and hyphens")
    return slug


def validate_password(password: str) -> str:
    """Validate password strength."""
    validation = PasswordValidator.validate_password_strength(password)
    if not validation["is_valid"]:
        raise ValueError(f"Password validation failed: {', '.join(validation['errors'])}")
    return password


# Add validators to schemas
RegisterRequest.__validators__ = {
    "tenant_slug": [validator("tenant_slug")(validate_tenant_slug)],
    "password": [validator("password")(validate_password)]
}

CreateTenantRequest.__validators__ = {
    "slug": [validator("slug")(validate_tenant_slug)]
}
