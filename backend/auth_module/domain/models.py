"""Domain models for the authentication module."""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from dataclasses import dataclass, field


class UserStatus(str, Enum):
    """User account status."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRole(str, Enum):
    """User roles."""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    USER = "user"


class TenantStatus(str, Enum):
    """Tenant status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class TokenStatus(str, Enum):
    """Refresh token status."""
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class Tenant:
    """Tenant domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    slug: str = ""
    name: str = ""
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    status: TenantStatus = TenantStatus.ACTIVE
    settings: Dict[str, Any] = field(default_factory=dict)
    branding: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == TenantStatus.ACTIVE
    
    def is_suspended(self) -> bool:
        """Check if tenant is suspended."""
        return self.status == TenantStatus.SUSPENDED
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update tenant settings."""
        self.settings.update(settings)
        self.updated_at = datetime.utcnow()
    
    def update_branding(self, branding: Dict[str, Any]) -> None:
        """Update tenant branding."""
        self.branding.update(branding)
        self.updated_at = datetime.utcnow()


@dataclass
class User:
    """User domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    email: str = ""
    password_hash: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING
    email_verified: bool = False
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    mfa_backup_codes: List[str] = field(default_factory=list)
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    def is_suspended(self) -> bool:
        """Check if user is suspended."""
        return self.status == UserStatus.SUSPENDED
    
    def is_pending(self) -> bool:
        """Check if user is pending."""
        return self.status == UserStatus.PENDING
    
    def get_full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def enable_mfa(self, secret: str, backup_codes: List[str]) -> None:
        """Enable MFA for user."""
        self.mfa_enabled = True
        self.mfa_secret = secret
        self.mfa_backup_codes = backup_codes
        self.updated_at = datetime.utcnow()
    
    def disable_mfa(self) -> None:
        """Disable MFA for user."""
        self.mfa_enabled = False
        self.mfa_secret = None
        self.mfa_backup_codes = []
        self.updated_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """Mark email as verified."""
        self.email_verified = True
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate user account."""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
    
    def suspend(self) -> None:
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()


@dataclass
class Role:
    """Role domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    name: str = ""
    description: str = ""
    permissions: List[str] = field(default_factory=list)
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to the role."""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission: str) -> None:
        """Remove a permission from the role."""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.updated_at = datetime.utcnow()
    
    def update_permissions(self, permissions: List[str]) -> None:
        """Update role permissions."""
        self.permissions = permissions
        self.updated_at = datetime.utcnow()


@dataclass
class UserRoleAssignment:
    """User role assignment domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    role_id: str = ""
    assigned_by: Optional[str] = None
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if role assignment is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_active(self) -> bool:
        """Check if role assignment is active."""
        return not self.is_expired()


@dataclass
class RefreshToken:
    """Refresh token domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    token_hash: str = ""
    status: TokenStatus = TokenStatus.ACTIVE
    issued_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow())
    device_info: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_active(self) -> bool:
        """Check if token is active."""
        return self.status == TokenStatus.ACTIVE and not self.is_expired()
    
    def revoke(self) -> None:
        """Revoke the token."""
        self.status = TokenStatus.REVOKED


@dataclass
class LoginAttempt:
    """Login attempt domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    user_id: Optional[str] = None
    email: str = ""
    ip_address: str = ""
    user_agent: str = ""
    success: bool = False
    reason: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    
    def is_successful(self) -> bool:
        """Check if login attempt was successful."""
        return self.success
    
    def is_failed(self) -> bool:
        """Check if login attempt failed."""
        return not self.success


@dataclass
class AuditLog:
    """Audit log domain model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    actor_user_id: Optional[str] = None
    action: str = ""
    resource: str = ""
    audit_metadata: Dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_actor_info(self) -> Dict[str, Any]:
        """Get actor information."""
        return {
            "user_id": self.actor_user_id,
            "tenant_id": self.tenant_id
        }
    
    def get_resource_info(self) -> Dict[str, Any]:
        """Get resource information."""
        return {
            "resource": self.resource,
            "action": self.action,
            "audit_metadata": self.audit_metadata
        }
