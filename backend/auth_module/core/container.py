"""Dependency injection container for the authentication module."""

from typing import Dict, Any, Type, TypeVar, Callable
from functools import lru_cache
from .config import config

T = TypeVar('T')


class Container:
    """Simple dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton service."""
        key = interface.__name__
        self._singletons[key] = implementation
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory for creating instances."""
        key = interface.__name__
        self._factories[key] = factory
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a service instance."""
        key = interface.__name__
        self._services[key] = instance
    
    def get(self, interface: Type[T]) -> T:
        """Get a service instance."""
        key = interface.__name__
        
        # Return singleton if available
        if key in self._singletons:
            return self._singletons[key]
        
        # Create from factory if available
        if key in self._factories:
            instance = self._factories[key]()
            return instance
        
        # Return registered instance if available
        if key in self._services:
            return self._services[key]
        
        # Try to create instance directly
        try:
            return interface()
        except Exception as e:
            raise ValueError(f"Could not resolve service {key}: {e}")
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


# Global container instance
container = Container()


def get_container() -> Container:
    """Get the global container instance."""
    return container


# Service registration helpers
def register_database_repositories(container: Container) -> None:
    """Register database repositories."""
    from ..infrastructure.db.repositories import (
        UserRepository,
        TenantRepository,
        RoleRepository,
        RefreshTokenRepository,
        LoginAttemptRepository,
        AuditLogRepository
    )
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    
    # Create database engine and session factory
    engine = create_engine(config.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Store session factory in container
    container._services["db_session"] = SessionLocal
    
    # Register repositories as factories that depend on db_session
    def create_user_repository():
        return UserRepository(SessionLocal())
    
    def create_tenant_repository():
        return TenantRepository(SessionLocal())
    
    def create_role_repository():
        return RoleRepository(SessionLocal())
    
    def create_refresh_token_repository():
        return RefreshTokenRepository(SessionLocal())
    
    def create_login_attempt_repository():
        return LoginAttemptRepository(SessionLocal())
    
    def create_audit_log_repository():
        return AuditLogRepository(SessionLocal())
    
    container.register_factory(UserRepository, create_user_repository)
    container.register_factory(TenantRepository, create_tenant_repository)
    container.register_factory(RoleRepository, create_role_repository)
    container.register_factory(RefreshTokenRepository, create_refresh_token_repository)
    container.register_factory(LoginAttemptRepository, create_login_attempt_repository)
    container.register_factory(AuditLogRepository, create_audit_log_repository)


def register_services(container: Container) -> None:
    """Register application services."""
    from ..domain.services import (
        AuthService,
        TenantService,
        UserService,
        PermissionService
    )
    
    # Register services as singletons
    container.register_singleton(AuthService, AuthService())
    container.register_singleton(TenantService, TenantService())
    container.register_singleton(UserService, UserService())
    container.register_singleton(PermissionService, PermissionService())


def register_external_services(container: Container) -> None:
    """Register external service adapters."""
    from ..infrastructure.messaging import EmailService, SMSService
    from ..infrastructure.oauth import OAuthService
    from ..infrastructure.cache import CacheService
    
    # Register external services
    container.register_singleton(EmailService, EmailService())
    container.register_singleton(SMSService, SMSService())
    container.register_singleton(OAuthService, OAuthService())
    container.register_singleton(CacheService, CacheService())


def initialize_container() -> Container:
    """Initialize the container with all services."""
    container = get_container()
    
    # Register all services
    register_database_repositories(container)
    register_services(container)
    register_external_services(container)
    
    return container


# Dependency injection decorator
def inject(interface: Type[T]):
    """Decorator for dependency injection."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service = container.get(interface)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator
