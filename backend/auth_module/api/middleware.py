"""FastAPI middleware for tenant resolution and authentication."""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import re
from ..core.config import config
from ..core.exceptions import TenantNotFoundError, TenantSuspendedError
from ..core.security import SecurityHeaders


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for tenant resolution and context management."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.resolution_strategy = config.tenant_resolution_strategy
        self.default_tenant_slug = config.default_tenant_slug
    
    async def dispatch(self, request: Request, call_next):
        """Process request and resolve tenant context."""
        try:
            # Resolve tenant from request
            tenant_slug = await self._resolve_tenant(request)
            
            # Add tenant context to request state
            request.state.tenant_slug = tenant_slug
            request.state.tenant_id = None  # Will be resolved by service layer
            
            # Add security headers
            response = await call_next(request)
            self._add_security_headers(response, request)
            
            return response
            
        except (TenantNotFoundError, TenantSuspendedError) as e:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": {
                        "code": e.code,
                        "message": e.message,
                        "details": e.details,
                        "timestamp": "2024-01-15T10:30:00Z",  # Would use actual timestamp
                        "request_id": request.headers.get("X-Request-ID", "unknown")
                    }
                }
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "SYSTEM_ERROR",
                        "message": "Internal server error",
                        "details": {},
                        "timestamp": "2024-01-15T10:30:00Z",  # Would use actual timestamp
                        "request_id": request.headers.get("X-Request-ID", "unknown")
                    }
                }
            )
    
    async def _resolve_tenant(self, request: Request) -> str:
        """Resolve tenant from request based on strategy."""
        if self.resolution_strategy == "subdomain":
            return self._resolve_from_subdomain(request)
        elif self.resolution_strategy == "path":
            return self._resolve_from_path(request)
        elif self.resolution_strategy == "header":
            return self._resolve_from_header(request)
        else:
            return self.default_tenant_slug
    
    def _resolve_from_subdomain(self, request: Request) -> str:
        """Resolve tenant from subdomain."""
        host = request.headers.get("host", "")
        
        # Extract subdomain from host
        # e.g., "tenant1.trivago-plus.com" -> "tenant1"
        parts = host.split(".")
        if len(parts) >= 3:
            subdomain = parts[0]
            if subdomain != "www" and subdomain != "api":
                return subdomain
        
        return self.default_tenant_slug
    
    def _resolve_from_path(self, request: Request) -> str:
        """Resolve tenant from path prefix."""
        path = request.url.path
        
        # Extract tenant from path
        # e.g., "/tenant1/api/v1/auth/login" -> "tenant1"
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 1 and path_parts[0].startswith("tenant"):
            tenant_slug = path_parts[0].replace("tenant", "")
            if tenant_slug:
                return tenant_slug
        
        return self.default_tenant_slug
    
    def _resolve_from_header(self, request: Request) -> str:
        """Resolve tenant from header."""
        tenant_slug = request.headers.get("X-Tenant-ID")
        if tenant_slug:
            return tenant_slug
        
        return self.default_tenant_slug
    
    def _add_security_headers(self, response, request: Request):
        """Add security headers to response."""
        # Skip CSP headers for documentation endpoints to allow external CDN resources
        path = request.url.path
        if path in ["/docs", "/redoc", "/openapi.json"]:
            headers = SecurityHeaders.get_security_headers()
            # Remove CSP header for docs endpoints
            if "Content-Security-Policy" in headers:
                del headers["Content-Security-Policy"]
        else:
            headers = SecurityHeaders.get_security_headers()
        
        for header, value in headers.items():
            response.headers[header] = value


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and authorization."""
    
    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/social",
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check authentication."""
        # Skip authentication for excluded paths
        if self._should_skip_auth(request):
            return await call_next(request)
        
        try:
            # Extract and validate token
            token = self._extract_token(request)
            if not token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": {
                            "code": "AUTH_TOKEN_MISSING",
                            "message": "Authorization token required",
                            "details": {},
                            "timestamp": "2024-01-15T10:30:00Z",
                            "request_id": request.headers.get("X-Request-ID", "unknown")
                        }
                    }
                )
            
            # Validate token and get user context
            user_context = await self._validate_token(token)
            if not user_context:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": {
                            "code": "AUTH_TOKEN_INVALID",
                            "message": "Invalid or expired token",
                            "details": {},
                            "timestamp": "2024-01-15T10:30:00Z",
                            "request_id": request.headers.get("X-Request-ID", "unknown")
                        }
                    }
                )
            
            # Add user context to request state
            request.state.user_id = user_context["user_id"]
            request.state.tenant_id = user_context["tenant_id"]
            request.state.user_role = user_context["role"]
            request.state.user_permissions = user_context["permissions"]
            
            return await call_next(request)
            
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "AUTH_ERROR",
                        "message": "Authentication failed",
                        "details": {"error": str(e)},
                        "timestamp": "2024-01-15T10:30:00Z",
                        "request_id": request.headers.get("X-Request-ID", "unknown")
                    }
                }
            )
    
    def _should_skip_auth(self, request: Request) -> bool:
        """Check if authentication should be skipped for this path."""
        path = request.url.path
        
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request."""
        authorization = request.headers.get("authorization")
        if not authorization:
            return None
        
        # Check for Bearer token
        if authorization.startswith("Bearer "):
            return authorization[7:]
        
        return None
    
    async def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user context."""
        try:
            from ..core.security import JWTManager
            
            payload = JWTManager.verify_token(token, "access")
            
            return {
                "user_id": payload["sub"],
                "tenant_id": payload["tenant_id"],
                "email": payload["email"],
                "role": payload["role"],
                "permissions": payload.get("permissions", [])
            }
            
        except Exception:
            return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiter = None  # Would be initialized with actual rate limiter
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check rate limits."""
        try:
            # Get client identifier
            client_id = self._get_client_id(request)
            
            # Check rate limit
            is_limited, current_count, reset_time = await self._check_rate_limit(
                client_id, request
            )
            
            if is_limited:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": "SYSTEM_RATE_LIMITED",
                            "message": "Rate limit exceeded",
                            "details": {
                                "retry_after": reset_time,
                                "current_count": current_count
                            },
                            "timestamp": "2024-01-15T10:30:00Z",
                            "request_id": request.headers.get("X-Request-ID", "unknown")
                        }
                    },
                    headers={
                        "Retry-After": str(reset_time),
                        "X-RateLimit-Limit": "1000",
                        "X-RateLimit-Remaining": str(1000 - current_count),
                        "X-RateLimit-Reset": str(reset_time)
                    }
                )
            
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = "1000"
            response.headers["X-RateLimit-Remaining"] = str(1000 - current_count)
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            
            return response
            
        except Exception:
            # Fail open for rate limiting
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Use IP address as primary identifier
        ip_address = request.client.host if request.client else "unknown"
        
        # For authenticated requests, also include user ID
        if hasattr(request.state, "user_id"):
            return f"{ip_address}:{request.state.user_id}"
        
        return ip_address
    
    async def _check_rate_limit(self, client_id: str, request: Request) -> tuple[bool, int, int]:
        """Check rate limit for client."""
        # This would use the actual rate limiter
        # For now, return not limited
        return False, 0, 0


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request IDs."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Add request ID to request and response."""
        import uuid
        
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Custom CORS middleware with tenant-aware origins."""
    
    def __init__(self, app: ASGIApp, allow_origins: list = None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS headers."""
        origin = request.headers.get("origin")
        
        # Check if origin is allowed
        if self._is_origin_allowed(origin):
            response = await call_next(request)
            
            # Add CORS headers
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Tenant-ID, X-Request-ID"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "86400"
            
            return response
        
        return await call_next(request)
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return True
        
        if "*" in self.allow_origins:
            return True
        
        return origin in self.allow_origins
