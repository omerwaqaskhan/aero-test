"""Repository implementations for database operations."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from .models import (
    UserModel, TenantModel, RoleModel, RefreshTokenModel,
    LoginAttemptModel, AuditLogModel, UserRoleModel
)
from ...domain.models import (
    User, Tenant, Role, RefreshToken, LoginAttempt, AuditLog, UserRoleAssignment
)
from ...core.exceptions import UserNotFoundError, TenantNotFoundError


class BaseRepository:
    """Base repository with common functionality."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def _to_domain_model(self, db_model, domain_class):
        """Convert database model to domain model."""
        if not db_model:
            return None
        
        # Get all attributes from the database model
        attrs = {}
        for column in db_model.__table__.columns:
            value = getattr(db_model, column.name)
            if isinstance(value, datetime):
                attrs[column.name] = value
            else:
                attrs[column.name] = value
        
        return domain_class(**attrs)


class UserRepository(BaseRepository):
    """User repository."""
    
    async def create(self, user: User) -> User:
        """Create a new user."""
        db_user = UserModel(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            password_hash=user.password_hash,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            email_verified=user.email_verified,
            mfa_enabled=user.mfa_enabled,
            mfa_secret=user.mfa_secret,
            mfa_backup_codes=user.mfa_backup_codes,
            last_login=user.last_login
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._to_domain_model(db_user, User)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain_model(db_user, User)
    
    async def get_by_email(self, tenant_id: str, email: str) -> Optional[User]:
        """Get user by email within tenant."""
        db_user = self.db.query(UserModel).filter(
            and_(
                UserModel.tenant_id == tenant_id,
                UserModel.email == email
            )
        ).first()
        return self._to_domain_model(db_user, User)
    
    async def update(self, user: User) -> User:
        """Update user."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise UserNotFoundError(user.id)
        
        # Update fields
        db_user.first_name = user.first_name
        db_user.last_name = user.last_name
        db_user.role = user.role
        db_user.status = user.status
        db_user.email_verified = user.email_verified
        db_user.mfa_enabled = user.mfa_enabled
        db_user.mfa_secret = user.mfa_secret
        db_user.mfa_backup_codes = user.mfa_backup_codes
        db_user.last_login = user.last_login
        db_user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._to_domain_model(db_user, User)
    
    async def delete(self, user_id: str) -> bool:
        """Delete user (soft delete)."""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        db_user.status = "deleted"
        db_user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    async def list_by_tenant(
        self, 
        tenant_id: str, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[User]:
        """List users by tenant."""
        query = self.db.query(UserModel).filter(UserModel.tenant_id == tenant_id)
        
        if status:
            query = query.filter(UserModel.status == status)
        
        db_users = query.offset(skip).limit(limit).all()
        return [self._to_domain_model(db_user, User) for db_user in db_users]
    
    async def count_by_tenant(self, tenant_id: str, status: Optional[str] = None) -> int:
        """Count users by tenant."""
        query = self.db.query(UserModel).filter(UserModel.tenant_id == tenant_id)
        
        if status:
            query = query.filter(UserModel.status == status)
        
        return query.count()


class TenantRepository(BaseRepository):
    """Tenant repository."""
    
    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant."""
        db_tenant = TenantModel(
            id=tenant.id,
            slug=tenant.slug,
            name=tenant.name,
            domain=tenant.domain,
            subdomain=tenant.subdomain,
            status=tenant.status,
            settings=tenant.settings,
            branding=tenant.branding
        )
        
        self.db.add(db_tenant)
        self.db.commit()
        self.db.refresh(db_tenant)
        
        return self._to_domain_model(db_tenant, Tenant)
    
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        db_tenant = self.db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        return self._to_domain_model(db_tenant, Tenant)
    
    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        db_tenant = self.db.query(TenantModel).filter(TenantModel.slug == slug).first()
        return self._to_domain_model(db_tenant, Tenant)
    
    async def get_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """Get tenant by subdomain."""
        db_tenant = self.db.query(TenantModel).filter(TenantModel.subdomain == subdomain).first()
        return self._to_domain_model(db_tenant, Tenant)
    
    async def update(self, tenant: Tenant) -> Tenant:
        """Update tenant."""
        db_tenant = self.db.query(TenantModel).filter(TenantModel.id == tenant.id).first()
        if not db_tenant:
            raise TenantNotFoundError(tenant.id)
        
        # Update fields
        db_tenant.name = tenant.name
        db_tenant.domain = tenant.domain
        db_tenant.subdomain = tenant.subdomain
        db_tenant.status = tenant.status
        db_tenant.settings = tenant.settings
        db_tenant.branding = tenant.branding
        db_tenant.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_tenant)
        
        return self._to_domain_model(db_tenant, Tenant)
    
    async def delete(self, tenant_id: str) -> bool:
        """Delete tenant (soft delete)."""
        db_tenant = self.db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if not db_tenant:
            return False
        
        db_tenant.status = "deleted"
        db_tenant.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """List all tenants."""
        db_tenants = self.db.query(TenantModel).offset(skip).limit(limit).all()
        return [self._to_domain_model(db_tenant, Tenant) for db_tenant in db_tenants]


class RoleRepository(BaseRepository):
    """Role repository."""
    
    async def create(self, role: Role) -> Role:
        """Create a new role."""
        db_role = RoleModel(
            id=role.id,
            tenant_id=role.tenant_id,
            name=role.name,
            description=role.description,
            permissions=role.permissions,
            is_system_role=role.is_system_role
        )
        
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        
        return self._to_domain_model(db_role, Role)
    
    async def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        db_role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        return self._to_domain_model(db_role, Role)
    
    async def get_by_name(self, tenant_id: str, name: str) -> Optional[Role]:
        """Get role by name within tenant."""
        db_role = self.db.query(RoleModel).filter(
            and_(
                RoleModel.tenant_id == tenant_id,
                RoleModel.name == name
            )
        ).first()
        return self._to_domain_model(db_role, Role)
    
    async def list_by_tenant(self, tenant_id: str) -> List[Role]:
        """List roles by tenant."""
        db_roles = self.db.query(RoleModel).filter(RoleModel.tenant_id == tenant_id).all()
        return [self._to_domain_model(db_role, Role) for db_role in db_roles]
    
    async def update(self, role: Role) -> Role:
        """Update role."""
        db_role = self.db.query(RoleModel).filter(RoleModel.id == role.id).first()
        if not db_role:
            return None
        
        # Update fields
        db_role.name = role.name
        db_role.description = role.description
        db_role.permissions = role.permissions
        db_role.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(db_role)
        
        return self._to_domain_model(db_role, Role)
    
    async def delete(self, role_id: str) -> bool:
        """Delete role."""
        db_role = self.db.query(RoleModel).filter(RoleModel.id == role_id).first()
        if not db_role:
            return False
        
        self.db.delete(db_role)
        self.db.commit()
        return True


class RefreshTokenRepository(BaseRepository):
    """Refresh token repository."""
    
    async def create(self, refresh_token: RefreshToken) -> RefreshToken:
        """Create a new refresh token."""
        db_token = RefreshTokenModel(
            id=refresh_token.id,
            user_id=refresh_token.user_id,
            token_hash=refresh_token.token_hash,
            status=refresh_token.status,
            issued_at=refresh_token.issued_at,
            expires_at=refresh_token.expires_at,
            device_info=refresh_token.device_info,
            ip_address=refresh_token.ip_address
        )
        
        self.db.add(db_token)
        self.db.commit()
        self.db.refresh(db_token)
        
        return self._to_domain_model(db_token, RefreshToken)
    
    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        db_token = self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.token_hash == token_hash
        ).first()
        return self._to_domain_model(db_token, RefreshToken)
    
    async def get_active_by_user(self, user_id: str) -> List[RefreshToken]:
        """Get active refresh tokens for user."""
        db_tokens = self.db.query(RefreshTokenModel).filter(
            and_(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.status == "active",
                RefreshTokenModel.expires_at > datetime.utcnow()
            )
        ).all()
        return [self._to_domain_model(db_token, RefreshToken) for db_token in db_tokens]
    
    async def revoke_by_hash(self, token_hash: str) -> bool:
        """Revoke refresh token by hash."""
        db_token = self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.token_hash == token_hash
        ).first()
        if not db_token:
            return False
        
        db_token.status = "revoked"
        self.db.commit()
        return True
    
    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all refresh tokens for user."""
        count = self.db.query(RefreshTokenModel).filter(
            and_(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.status == "active"
            )
        ).update({"status": "revoked"})
        
        self.db.commit()
        return count
    
    async def cleanup_expired(self) -> int:
        """Clean up expired refresh tokens."""
        count = self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.expires_at < datetime.utcnow()
        ).delete()
        
        self.db.commit()
        return count


class LoginAttemptRepository(BaseRepository):
    """Login attempt repository."""
    
    async def create(self, login_attempt: LoginAttempt) -> LoginAttempt:
        """Create a new login attempt record."""
        db_attempt = LoginAttemptModel(
            id=login_attempt.id,
            tenant_id=login_attempt.tenant_id,
            user_id=login_attempt.user_id,
            email=login_attempt.email,
            ip_address=login_attempt.ip_address,
            user_agent=login_attempt.user_agent,
            success=login_attempt.success,
            reason=login_attempt.reason
        )
        
        self.db.add(db_attempt)
        self.db.commit()
        self.db.refresh(db_attempt)
        
        return self._to_domain_model(db_attempt, LoginAttempt)
    
    async def get_failed_attempts(
        self, 
        user_id: str, 
        since: Optional[datetime] = None
    ) -> List[LoginAttempt]:
        """Get failed login attempts for user."""
        query = self.db.query(LoginAttemptModel).filter(
            and_(
                LoginAttemptModel.user_id == user_id,
                LoginAttemptModel.success == False
            )
        )
        
        if since:
            query = query.filter(LoginAttemptModel.occurred_at >= since)
        
        db_attempts = query.order_by(desc(LoginAttemptModel.occurred_at)).all()
        return [self._to_domain_model(db_attempt, LoginAttempt) for db_attempt in db_attempts]
    
    async def get_failed_attempts_by_email(
        self, 
        email: str, 
        since: Optional[datetime] = None
    ) -> List[LoginAttempt]:
        """Get failed login attempts by email."""
        query = self.db.query(LoginAttemptModel).filter(
            and_(
                LoginAttemptModel.email == email,
                LoginAttemptModel.success == False
            )
        )
        
        if since:
            query = query.filter(LoginAttemptModel.occurred_at >= since)
        
        db_attempts = query.order_by(desc(LoginAttemptModel.occurred_at)).all()
        return [self._to_domain_model(db_attempt, LoginAttempt) for db_attempt in db_attempts]
    
    async def cleanup_old_attempts(self, days: int = 30) -> int:
        """Clean up old login attempts."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = self.db.query(LoginAttemptModel).filter(
            LoginAttemptModel.occurred_at < cutoff_date
        ).delete()
        
        self.db.commit()
        return count


class AuditLogRepository(BaseRepository):
    """Audit log repository."""
    
    async def create(self, audit_log: AuditLog) -> AuditLog:
        """Create a new audit log entry."""
        db_log = AuditLogModel(
            id=audit_log.id,
            tenant_id=audit_log.tenant_id,
            actor_user_id=audit_log.actor_user_id,
            action=audit_log.action,
            resource=audit_log.resource,
            audit_metadata=audit_log.audit_metadata
        )
        
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        
        return self._to_domain_model(db_log, AuditLog)
    
    async def get_by_tenant(
        self, 
        tenant_id: str, 
        skip: int = 0, 
        limit: int = 100,
        action: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[AuditLog]:
        """Get audit logs by tenant."""
        query = self.db.query(AuditLogModel).filter(AuditLogModel.tenant_id == tenant_id)
        
        if action:
            query = query.filter(AuditLogModel.action == action)
        
        if since:
            query = query.filter(AuditLogModel.occurred_at >= since)
        
        db_logs = query.order_by(desc(AuditLogModel.occurred_at)).offset(skip).limit(limit).all()
        return [self._to_domain_model(db_log, AuditLog) for db_log in db_logs]
    
    async def get_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[AuditLog]:
        """Get audit logs by user."""
        db_logs = self.db.query(AuditLogModel).filter(
            AuditLogModel.actor_user_id == user_id
        ).order_by(desc(AuditLogModel.occurred_at)).offset(skip).limit(limit).all()
        
        return [self._to_domain_model(db_log, AuditLog) for db_log in db_logs]
    
    async def cleanup_old_logs(self, days: int = 90) -> int:
        """Clean up old audit logs."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = self.db.query(AuditLogModel).filter(
            AuditLogModel.occurred_at < cutoff_date
        ).delete()
        
        self.db.commit()
        return count
