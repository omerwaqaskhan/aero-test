"""API layer for FastAPI routers and middleware."""

from .routers import auth_router, tenant_router, user_router
from .middleware import TenantMiddleware
from .schemas import (
    # Auth schemas
    RegisterRequest, LoginRequest, RefreshTokenRequest, ForgotPasswordRequest,
    ResetPasswordRequest, MFASetupRequest, MFAVerifyRequest, SocialLoginRequest,
    AuthResponse, TokenResponse,
    # Tenant schemas
    CreateTenantRequest, UpdateTenantRequest, TenantResponse,
    # User schemas
    CreateUserRequest, UpdateUserRequest, UserResponse,
    # Common schemas
    ErrorResponse, SuccessResponse, PaginationResponse
)

__all__ = [
    "auth_router",
    "tenant_router", 
    "user_router",
    "TenantMiddleware",
    "RegisterRequest",
    "LoginRequest",
    "RefreshTokenRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "MFASetupRequest",
    "MFAVerifyRequest",
    "SocialLoginRequest",
    "AuthResponse",
    "TokenResponse",
    "CreateTenantRequest",
    "UpdateTenantRequest",
    "TenantResponse",
    "CreateUserRequest",
    "UpdateUserRequest",
    "UserResponse",
    "ErrorResponse",
    "SuccessResponse",
    "PaginationResponse",
]
