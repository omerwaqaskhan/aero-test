"""Custom exceptions for the authentication module."""

from typing import Dict, Any, Optional


class AuthError(Exception):
    """Base exception for authentication errors."""
    
    def __init__(
        self, 
        message: str, 
        code: str, 
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AuthError):
    """Validation error for input data."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class TenantError(AuthError):
    """Tenant-related errors."""
    
    def __init__(self, message: str, code: str = "TENANT_ERROR", **kwargs):
        super().__init__(
            message=message,
            code=code,
            status_code=kwargs.get("status_code", 400),
            details=kwargs.get("details", {})
        )


class UserError(AuthError):
    """User-related errors."""
    
    def __init__(self, message: str, code: str = "USER_ERROR", **kwargs):
        super().__init__(
            message=message,
            code=code,
            status_code=kwargs.get("status_code", 400),
            details=kwargs.get("details", {})
        )


class PermissionError(AuthError):
    """Permission/authorization errors."""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            message=message,
            code="PERMISSION_ERROR",
            status_code=403,
            details=kwargs.get("details", {})
        )


# Specific error classes for common scenarios
class InvalidCredentialsError(AuthError):
    """Invalid login credentials."""
    
    def __init__(self, attempts_remaining: Optional[int] = None):
        details = {}
        if attempts_remaining is not None:
            details["attempts_remaining"] = attempts_remaining
        super().__init__(
            message="Invalid email or password",
            code="AUTH_INVALID_CREDENTIALS",
            status_code=401,
            details=details
        )


class AccountLockedError(AuthError):
    """Account is locked due to failed attempts."""
    
    def __init__(self, lockout_duration_minutes: Optional[int] = None):
        details = {}
        if lockout_duration_minutes is not None:
            details["lockout_duration_minutes"] = lockout_duration_minutes
        super().__init__(
            message="Account is temporarily locked",
            code="AUTH_ACCOUNT_LOCKED",
            status_code=423,
            details=details
        )


class EmailNotVerifiedError(AuthError):
    """Email address not verified."""
    
    def __init__(self):
        super().__init__(
            message="Email address not verified",
            code="AUTH_EMAIL_NOT_VERIFIED",
            status_code=403,
            details={"action_required": "verify_email"}
        )


class MFARequiredError(AuthError):
    """Multi-factor authentication required."""
    
    def __init__(self, mfa_methods: list):
        super().__init__(
            message="Multi-factor authentication required",
            code="AUTH_MFA_REQUIRED",
            status_code=202,
            details={"mfa_methods": mfa_methods}
        )


class MFAInvalidError(AuthError):
    """Invalid MFA code."""
    
    def __init__(self, attempts_remaining: Optional[int] = None):
        details = {}
        if attempts_remaining is not None:
            details["attempts_remaining"] = attempts_remaining
        super().__init__(
            message="Invalid MFA code",
            code="AUTH_MFA_INVALID",
            status_code=401,
            details=details
        )


class TokenExpiredError(AuthError):
    """JWT token has expired."""
    
    def __init__(self):
        super().__init__(
            message="Token has expired",
            code="AUTH_TOKEN_EXPIRED",
            status_code=401,
            details={"action_required": "refresh_token"}
        )


class TokenInvalidError(AuthError):
    """JWT token is invalid."""
    
    def __init__(self):
        super().__init__(
            message="Invalid token",
            code="AUTH_TOKEN_INVALID",
            status_code=401,
            details={"action_required": "login"}
        )


class RefreshTokenInvalidError(AuthError):
    """Refresh token is invalid or expired."""
    
    def __init__(self):
        super().__init__(
            message="Invalid or expired refresh token",
            code="AUTH_REFRESH_TOKEN_INVALID",
            status_code=401,
            details={"action_required": "login"}
        )


class TenantNotFoundError(TenantError):
    """Tenant not found."""
    
    def __init__(self, tenant_slug: str):
        super().__init__(
            message=f"Tenant '{tenant_slug}' not found",
            code="TENANT_NOT_FOUND",
            status_code=404,
            details={"tenant_slug": tenant_slug}
        )


class TenantSuspendedError(TenantError):
    """Tenant is suspended."""
    
    def __init__(self, tenant_slug: str):
        super().__init__(
            message=f"Tenant '{tenant_slug}' is suspended",
            code="TENANT_SUSPENDED",
            status_code=403,
            details={"tenant_slug": tenant_slug}
        )


class TenantSlugTakenError(TenantError):
    """Tenant slug is already taken."""
    
    def __init__(self, tenant_slug: str):
        super().__init__(
            message=f"Tenant slug '{tenant_slug}' is already taken",
            code="TENANT_SLUG_TAKEN",
            status_code=409,
            details={"tenant_slug": tenant_slug}
        )


class UserNotFoundError(UserError):
    """User not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            message=f"User '{user_id}' not found",
            code="USER_NOT_FOUND",
            status_code=404,
            details={"user_id": user_id}
        )


class UserEmailTakenError(UserError):
    """Email address is already taken."""
    
    def __init__(self, email: str):
        super().__init__(
            message=f"Email '{email}' is already taken",
            code="USER_EMAIL_TAKEN",
            status_code=409,
            details={"email": email}
        )


class UserAccountSuspendedError(UserError):
    """User account is suspended."""
    
    def __init__(self, user_id: str):
        super().__init__(
            message=f"User account '{user_id}' is suspended",
            code="USER_ACCOUNT_SUSPENDED",
            status_code=403,
            details={"user_id": user_id}
        )


class InsufficientPermissionsError(PermissionError):
    """User has insufficient permissions."""
    
    def __init__(self, required_permission: str, user_permissions: list):
        super().__init__(
            message=f"Insufficient permissions. Required: {required_permission}",
            details={
                "required_permission": required_permission,
                "user_permissions": user_permissions
            }
        )


class PasswordTooWeakError(ValidationError):
    """Password doesn't meet strength requirements."""
    
    def __init__(self, requirements: Dict[str, Any]):
        super().__init__(
            message="Password doesn't meet strength requirements",
            field="password",
            details={"requirements": requirements}
        )


class RateLimitExceededError(AuthError):
    """Rate limit exceeded."""
    
    def __init__(self, limit: str, retry_after: Optional[int] = None):
        details = {"limit": limit}
        if retry_after is not None:
            details["retry_after"] = retry_after
        super().__init__(
            message="Rate limit exceeded",
            code="SYSTEM_RATE_LIMITED",
            status_code=429,
            details=details
        )


class SystemError(AuthError):
    """System/internal error."""
    
    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            message=message,
            code="SYSTEM_ERROR",
            status_code=500
        )


class MaintenanceError(AuthError):
    """System is under maintenance."""
    
    def __init__(self, message: str = "System is under maintenance"):
        super().__init__(
            message=message,
            code="SYSTEM_MAINTENANCE",
            status_code=503
        )
