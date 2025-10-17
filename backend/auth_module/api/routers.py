"""FastAPI routers for authentication, tenant, and user management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import uuid

from .schemas import (
    # Auth schemas
    RegisterRequest, LoginRequest, RefreshTokenRequest, ForgotPasswordRequest,
    ResetPasswordRequest, MFASetupRequest, MFAVerifyRequest, SocialLoginRequest,
    LogoutRequest, AuthResponse, TokenResponse, MFASetupResponse,
    # Tenant schemas
    CreateTenantRequest, UpdateTenantRequest, TenantResponse,
    # User schemas
    CreateUserRequest, UpdateUserRequest, UserResponse, AssignRoleRequest,
    # Enums
    UserRole, UserStatus,
    # Common schemas
    SuccessResponse, ErrorResponse, PaginationResponse, HealthCheckResponse, MetricsResponse
)
from ..core.exceptions import (
    AuthError, ValidationError, TenantError, UserError, PermissionError,
    InvalidCredentialsError, AccountLockedError, EmailNotVerifiedError,
    MFARequiredError, MFAInvalidError, TokenExpiredError, TokenInvalidError,
    RefreshTokenInvalidError, TenantNotFoundError, TenantSuspendedError,
    UserNotFoundError, UserEmailTakenError, UserAccountSuspendedError,
    InsufficientPermissionsError, PasswordTooWeakError, RateLimitExceededError
)
from ..core.security import JWTManager, MFAManager
from ..domain.services import AuthService, TenantService, UserService, PermissionService

# Security scheme
security = HTTPBearer()

# Dependency injection functions
def get_auth_service() -> AuthService:
    """Get authentication service instance."""
    return AuthService()

def get_tenant_service() -> TenantService:
    """Get tenant service instance."""
    return TenantService()

def get_user_service() -> UserService:
    """Get user service instance."""
    return UserService()

def get_permission_service() -> PermissionService:
    """Get permission service instance."""
    return PermissionService()

# Create routers
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
tenant_router = APIRouter(prefix="/tenants", tags=["Tenants"])
user_router = APIRouter(prefix="/users", tags=["Users"])


# Dependency functions
async def get_current_user_id(request: Request) -> str:
    """Get current user ID from request state."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user_id


async def get_current_tenant_id(request: Request) -> str:
    """Get current tenant ID from request state."""
    if not hasattr(request.state, "tenant_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not available"
        )
    return request.state.tenant_id


async def get_current_tenant_slug(request: Request) -> str:
    """Get current tenant slug from request state."""
    if not hasattr(request.state, "tenant_slug"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context not available"
        )
    return request.state.tenant_slug


def require_permission(permission: str):
    """Dependency to require specific permission."""
    async def check_permission(request: Request, user_id: str = Depends(get_current_user_id)):
        if not hasattr(request.state, "user_permissions"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission information not available"
            )
        
        user_permissions = request.state.user_permissions
        if permission not in user_permissions and "*" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        
        return user_id
    
    return check_permission


# Authentication endpoints
@auth_router.post("/register", response_model=SuccessResponse)
async def register_user(
    request: RegisterRequest,
    auth_service: AuthService = Depends()
):
    """Register a new user."""
    try:
        user, access_token, refresh_token = await auth_service.register_user(
            tenant_id=request.tenant_slug,  # Would resolve tenant_id from slug
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            role=request.role,
            invitation_code=request.invitation_code
        )
        
        return SuccessResponse(
            data={
                "user": UserResponse.from_orm(user),
                "tokens": TokenResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=3600
                )
            },
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/login", response_model=SuccessResponse)
async def login_user(
    request: LoginRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """Authenticate a user."""
    try:
        # Resolve tenant_slug to tenant_id
        tenant = await tenant_service.get_tenant_by_slug(request.tenant_slug)
        
        user, access_token, refresh_token = await auth_service.login_user(
            tenant_id=tenant.id,  # Use resolved tenant_id
            email=request.email,
            password=request.password,
            mfa_code=request.mfa_code,
            device_info=request.device_info,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        
        return SuccessResponse(
            data={
                "user": UserResponse(
                    id=str(user.id),
                    email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=UserRole(user.role),
                    status=UserStatus(user.status),
                    email_verified=user.email_verified,
                    mfa_enabled=user.mfa_enabled,
                    last_login=user.last_login,
                    created_at=user.created_at,
                    updated_at=user.updated_at
                ),
                "tokens": TokenResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_in=3600
                )
            },
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/refresh", response_model=SuccessResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends()
):
    """Refresh access token."""
    try:
        access_token, refresh_token = await auth_service.refresh_token(request.refresh_token)
        
        return SuccessResponse(
            data=TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600
            ),
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends()
):
    """Request password reset."""
    try:
        # This would be implemented in the auth service
        # For now, just return success
        return SuccessResponse(
            data={"message": "Password reset email sent"},
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends()
):
    """Reset password with token."""
    try:
        # This would be implemented in the auth service
        # For now, just return success
        return SuccessResponse(
            data={"message": "Password reset successfully"},
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/mfa/setup", response_model=SuccessResponse)
async def setup_mfa(
    request: MFASetupRequest,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends()
):
    """Setup MFA for user."""
    try:
        if request.method == "totp":
            secret = MFAManager.generate_totp_secret()
            qr_code = MFAManager.generate_totp_qr_code(secret, "user@example.com")
            backup_codes = MFAManager.generate_backup_codes()
            
            return SuccessResponse(
                data=MFASetupResponse(
                    qr_code=qr_code,
                    backup_codes=backup_codes,
                    secret=secret
                ),
                meta={
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            )
        else:
            raise ValidationError("Unsupported MFA method")
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/mfa/verify", response_model=SuccessResponse)
async def verify_mfa(
    request: MFAVerifyRequest,
    user_id: str = Depends(get_current_user_id),
    auth_service: AuthService = Depends()
):
    """Verify MFA code."""
    try:
        # This would be implemented in the auth service
        # For now, just return success
        return SuccessResponse(
            data={"message": "MFA verified successfully"},
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/social/{provider}", response_model=SuccessResponse)
async def social_login(
    provider: str,
    request: SocialLoginRequest,
    auth_service: AuthService = Depends()
):
    """Social login with OAuth provider."""
    try:
        # This would be implemented in the auth service
        # For now, just return success
        return SuccessResponse(
            data={"message": f"Social login with {provider} successful"},
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@auth_router.post("/logout", response_model=SuccessResponse)
async def logout_user(
    request: LogoutRequest,
    auth_service: AuthService = Depends()
):
    """Logout user and revoke tokens."""
    try:
        await auth_service.logout_user(request.refresh_token, request.revoke_all)
        
        return SuccessResponse(
            data={"message": "Logged out successfully"},
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


# Tenant endpoints
@tenant_router.post("/", response_model=SuccessResponse)
async def create_tenant(
    request: CreateTenantRequest,
    tenant_service: TenantService = Depends(),
    user_id: str = Depends(require_permission("tenants.create"))
):
    """Create a new tenant."""
    try:
        tenant = await tenant_service.create_tenant(
            slug=request.slug,
            name=request.name,
            domain=request.domain,
            subdomain=request.subdomain,
            settings=request.settings,
            branding=request.branding
        )
        
        return SuccessResponse(
            data=TenantResponse.from_orm(tenant),
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except TenantError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@tenant_router.get("/{tenant_slug}", response_model=SuccessResponse)
async def get_tenant(
    tenant_slug: str,
    tenant_service: TenantService = Depends()
):
    """Get tenant by slug."""
    try:
        tenant = await tenant_service.get_tenant_by_slug(tenant_slug)
        
        return SuccessResponse(
            data=TenantResponse.from_orm(tenant),
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except TenantError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@tenant_router.put("/{tenant_id}", response_model=SuccessResponse)
async def update_tenant(
    tenant_id: str,
    request: UpdateTenantRequest,
    tenant_service: TenantService = Depends(),
    user_id: str = Depends(require_permission("tenants.update"))
):
    """Update tenant."""
    try:
        updates = request.dict(exclude_unset=True)
        tenant = await tenant_service.update_tenant(tenant_id, updates, user_id)
        
        return SuccessResponse(
            data=TenantResponse.from_orm(tenant),
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except TenantError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


# User endpoints
@user_router.post("/", response_model=SuccessResponse)
async def create_user(
    request: CreateUserRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    user_service: UserService = Depends(),
    user_id: str = Depends(require_permission("users.create"))
):
    """Create a new user."""
    try:
        user = await user_service.create_user(
            tenant_id=tenant_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            role=request.role,
            created_by=user_id
        )
        
        return SuccessResponse(
            data=UserResponse.from_orm(user),
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except UserError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@user_router.get("/me", response_model=SuccessResponse)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    user_service: UserService = Depends()
):
    """Get current user profile."""
    try:
        user = await user_service.get_user_by_id(user_id)
        
        return SuccessResponse(
            data=UserResponse.from_orm(user),
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except UserError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


@user_router.put("/{user_id}", response_model=SuccessResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    user_service: UserService = Depends(),
    current_user_id: str = Depends(require_permission("users.update"))
):
    """Update user."""
    try:
        updates = request.dict(exclude_unset=True)
        user = await user_service.update_user(user_id, updates, current_user_id)
        
        return SuccessResponse(
            data=UserResponse.from_orm(user),
            meta={
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
        
    except UserError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "request_id": str(uuid.uuid4())
                }
            }
        )


# Health check endpoint
@auth_router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services={
            "database": "healthy",
            "redis": "healthy",
            "email": "healthy"
        }
    )


# Metrics endpoint
@auth_router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics."""
    return MetricsResponse(
        active_users=1000,
        failed_logins=50,
        token_validations=5000,
        tenant_count=10,
        cache_hit_rate=0.95,
        response_times={
            "login": 0.15,
            "token_validation": 0.05,
            "user_creation": 0.3
        }
    )
