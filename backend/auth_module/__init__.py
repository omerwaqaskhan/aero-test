"""
Trivago Auth - Multi-Tenant Authentication Module

A production-ready, reusable authentication and authorization module
with multi-tenancy, RBAC, and comprehensive security controls.
"""

__version__ = "1.0.0"
__author__ = "Trivago Plus Team"

from .core.config import AuthConfig
from .core.container import Container
from .api.middleware import TenantMiddleware
from .api.routers import auth_router, tenant_router, user_router

__all__ = [
    "AuthConfig",
    "Container", 
    "TenantMiddleware",
    "auth_router",
    "tenant_router", 
    "user_router",
]
