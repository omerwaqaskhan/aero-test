"""Domain services for authentication, tenant, user, and permission management."""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from .models import User, Tenant, Role, RefreshToken, LoginAttempt, AuditLog, UserRoleAssignment
from .policies import RBACPolicy, ABACPolicy
from ..core.exceptions import (
    AuthError, ValidationError, TenantError, UserError, PermissionError,
    InvalidCredentialsError, AccountLockedError, EmailNotVerifiedError,
    MFARequiredError, MFAInvalidError, TokenExpiredError, TokenInvalidError,
    RefreshTokenInvalidError, TenantNotFoundError, TenantSuspendedError,
    UserNotFoundError, UserEmailTakenError, UserAccountSuspendedError,
    InsufficientPermissionsError, PasswordTooWeakError, RateLimitExceededError
)
from ..core.security import PasswordManager, JWTManager, MFAManager, RateLimiter, AuditLogger
from ..core.config import config


class AuthService:
    """Authentication service."""
    
    def __init__(self):
        self.password_manager = PasswordManager()
        self.jwt_manager = JWTManager()
        self.mfa_manager = MFAManager()
        self.rate_limiter = RateLimiter()
        self.rbac_policy = RBACPolicy()
        self.abac_policy = ABACPolicy()
    
    async def register_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "user",
        invitation_code: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """Register a new user."""
        # Validate password strength
        password_validation = self.password_manager.validate_password_strength(password)
        if not password_validation["is_valid"]:
            raise PasswordTooWeakError(password_validation["requirements"], password_validation["errors"])
        
        # Check rate limiting
        rate_limit_key = f"register:{email}"
        is_limited, current_count, reset_time = self.rate_limiter.is_rate_limited(
            rate_limit_key, config.rate_limit_register, 3600
        )
        if is_limited:
            raise RateLimitExceededError(config.rate_limit_register, reset_time)
        
        # Hash password
        password_hash = self.password_manager.hash_password(password)
        
        # Create user (this would typically use a repository)
        user = User(
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            status="pending"
        )
        
        # Generate tokens
        access_token = self.jwt_manager.generate_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            permissions=[]  # Would be populated from role
        )
        
        refresh_token = self.jwt_manager.generate_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id
        )
        
        # Log audit event
        AuditLogger.log_security_event(
            event_type="user_registered",
            user_id=user.id,
            tenant_id=tenant_id,
            details={"email": email, "role": role}
        )
        
        return user, access_token, refresh_token
    
    async def login_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        mfa_code: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """Authenticate a user."""
        # Check rate limiting
        rate_limit_key = f"login:{email}"
        is_limited, current_count, reset_time = self.rate_limiter.is_rate_limited(
            rate_limit_key, config.rate_limit_login, 60
        )
        if is_limited:
            raise RateLimitExceededError(config.rate_limit_login, reset_time)
        
        # Get user using repository
        user = await self._get_user_by_email(tenant_id, email)
        if not user:
            # Log failed attempt
            await self._log_login_attempt(
                tenant_id=tenant_id,
                email=email,
                success=False,
                reason="user_not_found",
                ip_address=ip_address,
                user_agent=user_agent
            )
            raise InvalidCredentialsError()
        
        # Check if user is active
        if not user.is_active():
            if user.is_suspended():
                raise UserAccountSuspendedError(user.id)
            else:
                raise EmailNotVerifiedError()
        
        # Check if account is locked
        if await self._is_account_locked(user.id):
            raise AccountLockedError()
        
        # Verify password
        if not self.password_manager.verify_password(password, user.password_hash):
            # Log failed attempt
            await self._log_login_attempt(
                tenant_id=tenant_id,
                user_id=user.id,
                email=email,
                success=False,
                reason="invalid_password",
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Check if account should be locked
            failed_attempts = await self._get_failed_login_attempts(user.id)
            attempts_remaining = config.max_failed_login_attempts - len(failed_attempts)
            
            if attempts_remaining <= 0:
                await self._lock_account(user.id)
                raise AccountLockedError()
            
            raise InvalidCredentialsError(attempts_remaining)
        
        # Check MFA if enabled
        if user.mfa_enabled:
            if not mfa_code:
                # Log successful password verification
                await self._log_login_attempt(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    email=email,
                    success=True,
                    reason="password_verified_mfa_required",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise MFARequiredError(["totp", "sms", "email"])
            
            # Verify MFA code
            if not self.mfa_manager.verify_totp_code(user.mfa_secret, mfa_code):
                # Log failed MFA attempt
                await self._log_login_attempt(
                    tenant_id=tenant_id,
                    user_id=user.id,
                    email=email,
                    success=False,
                    reason="invalid_mfa_code",
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                raise MFAInvalidError()
        
        # Update last login
        user.update_last_login()
        
        # Generate tokens
        permissions = await self._get_user_permissions(user.id)
        access_token = self.jwt_manager.generate_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            permissions=permissions
        )
        
        refresh_token = self.jwt_manager.generate_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            device_info=device_info
        )
        
        # Log successful login
        await self._log_login_attempt(
            tenant_id=tenant_id,
            user_id=user.id,
            email=email,
            success=True,
            reason="successful_login",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Log audit event
        AuditLogger.log_security_event(
            event_type="user_login",
            user_id=user.id,
            tenant_id=tenant_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user, access_token, refresh_token

    async def social_login(
        self,
        tenant_id: str,
        provider: str,
        access_token: str,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """Authenticate or register a user via social login."""
        from ..infrastructure.oauth import OAuthService
        
        # Initialize OAuth service
        oauth_service = OAuthService()
        
        # Verify the social token and get user info
        try:
            social_user_info = await oauth_service.verify_social_token(provider, access_token, redirect_uri)
        except Exception as e:
            # Log failed attempt
            await self._log_login_attempt(
                tenant_id=tenant_id,
                email="unknown",
                success=False,
                reason="invalid_social_token",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"provider": provider, "error": str(e)}
            )
            raise InvalidCredentialsError(f"Invalid {provider} token")
        
        email = social_user_info["email"]
        provider_id = social_user_info["provider_id"]
        
        # Check rate limiting
        rate_limit_key = f"social_login:{email}:{provider}"
        is_limited, current_count, reset_time = self.rate_limiter.is_rate_limited(
            rate_limit_key, config.rate_limit_login, 60
        )
        if is_limited:
            raise RateLimitExceededError(config.rate_limit_login, reset_time)
        
        # Check if user exists
        user = await self._get_user_by_email(tenant_id, email)
        
        if user:
            # User exists - check if they have this social provider linked
            if not await self._is_social_provider_linked(user.id, provider, provider_id):
                # Link the social provider to existing account
                await self._link_social_provider(user.id, provider, provider_id, social_user_info)
            
            # Check if user is active
            if not user.is_active():
                if user.is_suspended():
                    raise UserAccountSuspendedError(user.id)
                else:
                    # For social login, we can auto-verify email
                    user.verify_email()
                    await self._update_user(user)
            
            # Update last login
            user.update_last_login()
            
            # Log successful login
            await self._log_login_attempt(
                tenant_id=tenant_id,
                user_id=user.id,
                email=email,
                success=True,
                reason="social_login_success",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"provider": provider}
            )
            
        else:
            # User doesn't exist - create new account
            user = await self._create_social_user(
                tenant_id=tenant_id,
                social_user_info=social_user_info,
                provider=provider,
                provider_id=provider_id
            )
            
            # Log successful registration
            await self._log_login_attempt(
                tenant_id=tenant_id,
                user_id=user.id,
                email=email,
                success=True,
                reason="social_registration_success",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"provider": provider}
            )
        
        # Generate tokens
        permissions = await self._get_user_permissions(user.id)
        access_token = self.jwt_manager.generate_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role,
            permissions=permissions
        )
        
        refresh_token = self.jwt_manager.generate_refresh_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            device_info=device_info
        )
        
        # Log audit event
        AuditLogger.log_security_event(
            event_type="social_login",
            user_id=user.id,
            tenant_id=tenant_id,
            details={
                "provider": provider,
                "email": email,
                "is_new_user": user.created_at == user.updated_at
            }
        )
        
        return user, access_token, refresh_token

    async def _create_social_user(
        self,
        tenant_id: str,
        social_user_info: Dict[str, Any],
        provider: str,
        provider_id: str
    ) -> User:
        """Create a new user from social login info."""
        # Create user without password
        user = User(
            tenant_id=tenant_id,
            email=social_user_info["email"],
            password_hash=None,  # No password for social users
            first_name=social_user_info["first_name"],
            last_name=social_user_info["last_name"],
            role="user",
            status="active",  # Auto-activate social users
            email_verified=True  # Social providers verify emails
        )
        
        # Save user (this would typically use a repository)
        await self._save_user(user)
        
        # Link social provider
        await self._link_social_provider(user.id, provider, provider_id, social_user_info)
        
        return user

    async def _is_social_provider_linked(self, user_id: str, provider: str, provider_id: str) -> bool:
        """Check if a social provider is linked to a user."""
        # This would typically query a social_providers table
        # For now, return False to always link
        return False

    async def _link_social_provider(
        self,
        user_id: str,
        provider: str,
        provider_id: str,
        social_user_info: Dict[str, Any]
    ) -> None:
        """Link a social provider to a user account."""
        # This would typically save to a social_providers table
        # For now, just log the action
        AuditLogger.log_security_event(
            event_type="social_provider_linked",
            user_id=user_id,
            tenant_id=None,
            details={
                "provider": provider,
                "provider_id": provider_id,
                "user_info": social_user_info
            }
        )
    
    async def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token."""
        try:
            payload = self.jwt_manager.verify_token(refresh_token, "refresh")
            user_id = payload["sub"]
            tenant_id = payload["tenant_id"]
            
            # Check if refresh token is still valid in database
            token_record = await self._get_refresh_token(refresh_token)
            if not token_record or not token_record.is_active():
                raise RefreshTokenInvalidError()
            
            # Get user
            user = await self._get_user_by_id(user_id)
            if not user or not user.is_active():
                raise RefreshTokenInvalidError()
            
            # Generate new tokens
            permissions = await self._get_user_permissions(user.id)
            access_token = self.jwt_manager.generate_access_token(
                user_id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                role=user.role,
                permissions=permissions
            )
            
            new_refresh_token = self.jwt_manager.generate_refresh_token(
                user_id=user.id,
                tenant_id=user.tenant_id,
                device_info=token_record.device_info
            )
            
            # Revoke old refresh token
            token_record.revoke()
            
            # Log audit event
            AuditLogger.log_security_event(
                event_type="token_refreshed",
                user_id=user.id,
                tenant_id=tenant_id
            )
            
            return access_token, new_refresh_token
            
        except Exception as e:
            if isinstance(e, (TokenExpiredError, TokenInvalidError, RefreshTokenInvalidError)):
                raise
            raise RefreshTokenInvalidError()
    
    async def logout_user(self, refresh_token: str, revoke_all: bool = False) -> None:
        """Logout user and revoke tokens."""
        try:
            payload = self.jwt_manager.verify_token(refresh_token, "refresh")
            user_id = payload["sub"]
            tenant_id = payload["tenant_id"]
            
            if revoke_all:
                # Revoke all refresh tokens for user
                await self._revoke_all_refresh_tokens(user_id)
            else:
                # Revoke specific refresh token
                token_record = await self._get_refresh_token(refresh_token)
                if token_record:
                    token_record.revoke()
            
            # Log audit event
            AuditLogger.log_security_event(
                event_type="user_logout",
                user_id=user_id,
                tenant_id=tenant_id,
                details={"revoke_all": revoke_all}
            )
            
        except Exception:
            # Ignore errors during logout
            pass
    
    async def _get_user_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        """Get user by email (placeholder - would use repository)."""
        # This would typically use a repository
        return None
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID (placeholder - would use repository)."""
        # This would typically use a repository
        return None
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions (placeholder - would use repository)."""
        # This would typically use a repository
        return []
    
    async def _get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        """Get refresh token record (placeholder - would use repository)."""
        # This would typically use a repository
        return None
    
    async def _log_login_attempt(
        self,
        tenant_id: str,
        email: str,
        success: bool,
        reason: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """Log login attempt (placeholder - would use repository)."""
        # This would typically use a repository
        pass
    
    async def _is_account_locked(self, user_id: str) -> bool:
        """Check if account is locked (placeholder - would use repository)."""
        # This would typically use a repository
        return False
    
    async def _get_failed_login_attempts(self, user_id: str) -> List[LoginAttempt]:
        """Get failed login attempts (placeholder - would use repository)."""
        # This would typically use a repository
        return []
    
    async def _lock_account(self, user_id: str) -> None:
        """Lock user account (placeholder - would use repository)."""
        # This would typically use a repository
        pass
    
    async def _revoke_all_refresh_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for user (placeholder - would use repository)."""
        # This would typically use a repository
        pass
    
    async def _get_user_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        """Get user by email within tenant."""
        from ..infrastructure.db.repositories import UserRepository
        from ..infrastructure.db.database import get_db
        
        db = next(get_db())
        repository = UserRepository(db)
        return await repository.get_by_email(tenant_id, email)


class TenantService:
    """Tenant management service."""
    
    def __init__(self):
        self.rbac_policy = RBACPolicy()
        self.abac_policy = ABACPolicy()
    
    async def create_tenant(
        self,
        slug: str,
        name: str,
        domain: Optional[str] = None,
        subdomain: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        branding: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """Create a new tenant."""
        # Validate slug format
        import re
        if not re.match(config.tenant_slug_pattern, slug):
            raise ValidationError("Invalid tenant slug format", field="slug")
        
        # Check if slug is already taken
        existing_tenant = await self._get_tenant_by_slug(slug)
        if existing_tenant:
            raise TenantError(f"Tenant slug '{slug}' is already taken", "TENANT_SLUG_TAKEN")
        
        # Create tenant
        tenant = Tenant(
            slug=slug,
            name=name,
            domain=domain,
            subdomain=subdomain,
            settings=settings or {},
            branding=branding or {}
        )
        
        # Log audit event
        AuditLogger.log_security_event(
            event_type="tenant_created",
            tenant_id=tenant.id,
            details={"slug": slug, "name": name}
        )
        
        return tenant
    
    async def get_tenant_by_slug(self, slug: str) -> Tenant:
        """Get tenant by slug."""
        tenant = await self._get_tenant_by_slug(slug)
        if not tenant:
            raise TenantNotFoundError(slug)
        
        if tenant.is_suspended():
            raise TenantSuspendedError(slug)
        
        return tenant
    
    async def update_tenant(
        self,
        tenant_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> Tenant:
        """Update tenant."""
        tenant = await self._get_tenant_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        
        # Update fields
        if "name" in updates:
            tenant.name = updates["name"]
        if "settings" in updates:
            tenant.update_settings(updates["settings"])
        if "branding" in updates:
            tenant.update_branding(updates["branding"])
        
        # Log audit event
        AuditLogger.log_security_event(
            event_type="tenant_updated",
            tenant_id=tenant_id,
            actor_user_id=updated_by,
            details={"updates": updates}
        )
        
        return tenant
    
    async def _get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        from ..infrastructure.db.repositories import TenantRepository
        from ..infrastructure.db.database import get_db
        
        db = next(get_db())
        repository = TenantRepository(db)
        return await repository.get_by_slug(slug)
    
    async def _get_tenant_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID (placeholder - would use repository)."""
        # This would typically use a repository
        return None


class UserService:
    """User management service."""
    
    def __init__(self):
        self.rbac_policy = RBACPolicy()
        self.abac_policy = ABACPolicy()
    
    async def create_user(
        self,
        tenant_id: str,
        email: str,
        first_name: str,
        last_name: str,
        created_by: str,
        role: str = "user"
    ) -> User:
        """Create a new user."""
        # Check if email is already taken in tenant
        existing_user = await self._get_user_by_email(tenant_id, email)
        if existing_user:
            raise UserEmailTakenError(email)
        
        # Create user
        user = User(
            tenant_id=tenant_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            status="active"
        )
        
        # Log audit event
        AuditLogger.log_security_event(
            event_type="user_created",
            tenant_id=tenant_id,
            actor_user_id=created_by,
            details={"user_id": user.id, "email": email, "role": role}
        )
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        return user
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
        updated_by: str
    ) -> User:
        """Update user."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        # Update fields
        if "first_name" in updates:
            user.first_name = updates["first_name"]
        if "last_name" in updates:
            user.last_name = updates["last_name"]
        if "role" in updates:
            user.role = updates["role"]
        
        # Log audit event
        AuditLogger.log_security_event(
            event_type="user_updated",
            tenant_id=user.tenant_id,
            actor_user_id=updated_by,
            details={"user_id": user_id, "updates": updates}
        )
        
        return user
    
    async def _get_user_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        """Get user by email (placeholder - would use repository)."""
        # This would typically use a repository
        return None
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID (placeholder - would use repository)."""
        # This would typically use a repository
        return None


class PermissionService:
    """Permission and authorization service."""
    
    def __init__(self):
        self.rbac_policy = RBACPolicy()
        self.abac_policy = ABACPolicy()
    
    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has permission."""
        # Get user permissions
        user_permissions = await self._get_user_permissions(user_id)
        
        # Check RBAC
        if not self.rbac_policy.has_permission(user_permissions, permission):
            return False
        
        # Check ABAC if resource and context provided
        if resource and context:
            return await self.abac_policy.check_permission(
                user_id=user_id,
                permission=permission,
                resource=resource,
                context=context
            )
        
        return True
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions."""
        return await self._get_user_permissions(user_id)
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions (placeholder - would use repository)."""
        # This would typically use a repository
        return []
