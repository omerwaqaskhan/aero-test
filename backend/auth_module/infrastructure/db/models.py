"""SQLAlchemy models for the authentication module."""

from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON,
    Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class TenantModel(Base):
    """Tenant database model."""
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    subdomain = Column(String(100), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="active")
    settings = Column(JSON, nullable=False, default=dict)
    branding = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("UserModel", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("RoleModel", back_populates="tenant", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="ck_tenant_status"),
        Index("ix_tenants_slug", "slug"),
        Index("ix_tenants_subdomain", "subdomain"),
    )


class UserModel(Base):
    """User database model."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(100), nullable=False, default="")
    last_name = Column(String(100), nullable=False, default="")
    role = Column(String(50), nullable=False, default="user")
    status = Column(String(20), nullable=False, default="pending")
    email_verified = Column(Boolean, nullable=False, default=False)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret = Column(String(255), nullable=True)
    mfa_backup_codes = Column(JSON, nullable=False, default=list)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("TenantModel", back_populates="users")
    user_roles = relationship("UserRoleModel", foreign_keys="UserRoleModel.user_id", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user", cascade="all, delete-orphan")
    login_attempts = relationship("LoginAttemptModel", back_populates="user")
    audit_logs = relationship("AuditLogModel", back_populates="actor")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        CheckConstraint("status IN ('pending', 'active', 'suspended', 'deleted')", name="ck_user_status"),
        CheckConstraint("role IN ('super_admin', 'tenant_admin', 'manager', 'user')", name="ck_user_role"),
        Index("ix_users_tenant_email", "tenant_id", "email"),
        Index("ix_users_email", "email"),
        Index("ix_users_status", "status"),
    )


class RoleModel(Base):
    """Role database model."""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=False, default=list)
    is_system_role = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("TenantModel", back_populates="roles")
    user_roles = relationship("UserRoleModel", back_populates="role", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),
        Index("ix_roles_tenant_name", "tenant_id", "name"),
    )


class UserRoleModel(Base):
    """User role assignment database model."""
    __tablename__ = "user_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("RoleModel", back_populates="user_roles")
    assigned_by_user = relationship("UserModel", foreign_keys=[assigned_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        Index("ix_user_roles_user", "user_id"),
        Index("ix_user_roles_role", "role_id"),
        Index("ix_user_roles_expires", "expires_at"),
    )


class RefreshTokenModel(Base):
    """Refresh token database model."""
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, default="active")
    issued_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    device_info = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String(45), nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="refresh_tokens")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('active', 'revoked', 'expired')", name="ck_refresh_token_status"),
        Index("ix_refresh_tokens_user", "user_id"),
        Index("ix_refresh_tokens_hash", "token_hash"),
        Index("ix_refresh_tokens_status", "status"),
        Index("ix_refresh_tokens_expires", "expires_at"),
    )


class LoginAttemptModel(Base):
    """Login attempt database model."""
    __tablename__ = "login_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    reason = Column(String(100), nullable=False)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("TenantModel")
    user = relationship("UserModel", back_populates="login_attempts")
    
    # Constraints
    __table_args__ = (
        Index("ix_login_attempts_tenant", "tenant_id"),
        Index("ix_login_attempts_user", "user_id"),
        Index("ix_login_attempts_email", "email"),
        Index("ix_login_attempts_ip", "ip_address"),
        Index("ix_login_attempts_occurred", "occurred_at"),
        Index("ix_login_attempts_success", "success"),
    )


class AuditLogModel(Base):
    """Audit log database model."""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    audit_metadata = Column(JSON, nullable=False, default=dict)
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship("TenantModel")
    actor = relationship("UserModel", back_populates="audit_logs")
    
    # Constraints
    __table_args__ = (
        Index("ix_audit_logs_tenant", "tenant_id"),
        Index("ix_audit_logs_actor", "actor_user_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_resource", "resource"),
        Index("ix_audit_logs_occurred", "occurred_at"),
    )
