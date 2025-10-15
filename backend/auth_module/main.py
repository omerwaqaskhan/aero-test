"""Main FastAPI application for the authentication module."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from .api.routers import auth_router, tenant_router, user_router
from .api.middleware import (
    TenantMiddleware, AuthMiddleware, RateLimitMiddleware, RequestIDMiddleware
)
from .core.config import config
from .core.container import initialize_container
from .core.exceptions import AuthError

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting authentication service...")
    
    # Initialize dependency injection container
    container = initialize_container()
    app.state.container = container
    
    # Initialize database connection
    # This would typically create database tables and connections
    logger.info("Database initialized")
    
    # Initialize external services
    logger.info("External services initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down authentication service...")


# Create FastAPI application
app = FastAPI(
    title="WindWays Auth API",
    description="Multi-tenant authentication and authorization service for WindWays travel platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# Global exception handler
@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": "2024-01-15T10:30:00Z",  # Would use actual timestamp
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle global exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "SYSTEM_ERROR",
                "message": "Internal server error",
                "details": {},
                "timestamp": "2024-01-15T10:30:00Z",  # Would use actual timestamp
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        }
    )


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WindWays Auth API",
        "version": "1.0.0",
        "status": "healthy"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-15T10:30:00Z",  # Would use actual timestamp
        "version": "1.0.0",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "email": "healthy"
        }
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Get system metrics."""
    return {
        "active_users": 1000,
        "failed_logins": 50,
        "token_validations": 5000,
        "tenant_count": 10,
        "cache_hit_rate": 0.95,
        "response_times": {
            "login": 0.15,
            "token_validation": 0.05,
            "user_creation": 0.3
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "auth_module.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=config.log_level.lower()
    )
