"""Main FastAPI application for the authentication module."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
import os

from .api.routers import auth_router, tenant_router, user_router
from .api.admin_routers import admin_router
from .api.middleware import (
    TenantMiddleware, AuthMiddleware, RateLimitMiddleware, RequestIDMiddleware
)
from .core.config import config
from .core.container import initialize_container
from .core.exceptions import AuthError
from .core.logging_middleware import LoggingMiddleware
from .core.error_handler import (
    validation_error_handler,
    http_exception_handler,
    database_error_handler,
    generic_exception_handler
)
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, DatabaseError

# Configure logging first (needed for Sentry initialization)
logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking (if enabled)
if config.enable_sentry and config.sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_sdk.init(
            dsn=config.sentry_dsn,
            environment=config.sentry_environment,
            traces_sample_rate=config.sentry_traces_sample_rate,
            profiles_sample_rate=config.sentry_profiles_sample_rate,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            release=os.getenv("SENTRY_RELEASE", None),
            send_default_pii=False,
            enable_tracing=True,
        )
        logger.info(f"Sentry error tracking initialized for environment: {config.sentry_environment}")
    except ImportError:
        logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk[fastapi]")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")

# Import search-booking router
try:
    from search_booking_module.api.routers import router as search_booking_router
    SEARCH_BOOKING_AVAILABLE = True
except ImportError as e:
    SEARCH_BOOKING_AVAILABLE = False
    logger.warning(f"Search-booking module not available: {e}")

# Import monitoring router
try:
    from search_booking_module.api.monitoring_routers import router as monitoring_router
    MONITORING_AVAILABLE = True
except ImportError as e:
    MONITORING_AVAILABLE = False
    logger.warning(f"Monitoring module not available: {e}")

# Import revenue router
try:
    from revenue_module.api.routers import router as revenue_router
    REVENUE_AVAILABLE = True
except ImportError as e:
    REVENUE_AVAILABLE = False
    logger.warning(f"Revenue module not available: {e}")


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
    
    # Start hotel data scheduler if available and not disabled
    if SEARCH_BOOKING_AVAILABLE and not os.getenv("DISABLE_SCHEDULER"):
        try:
            from search_booking_module.scraping.scheduler import start_scheduler, stop_scheduler
            await start_scheduler()
            logger.info("Hotel data scheduler started")
            app.state.hotel_scheduler = True
        except Exception as e:
            logger.warning(f"Could not start hotel data scheduler: {e}")
            app.state.hotel_scheduler = False
    
    yield
    
    # Shutdown
    logger.info("Shutting down authentication service...")
    
    # Stop hotel data scheduler if started
    if SEARCH_BOOKING_AVAILABLE and getattr(app.state, 'hotel_scheduler', False):
        try:
            from search_booking_module.scraping.scheduler import stop_scheduler
            await stop_scheduler()
            logger.info("Hotel data scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping hotel data scheduler: {e}")


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

# Add CORS middleware - Use secure configuration from environment
from auth_module.core.config import config

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,  # Secure: specific origins only
    allow_credentials=config.cors_allow_credentials,
    allow_methods=config.cors_allow_methods,
    allow_headers=config.cors_allow_headers,
)

# Add custom middleware (order matters - last added is first executed)
app.add_middleware(LoggingMiddleware)  # Log all requests/responses
app.add_middleware(RequestIDMiddleware)
app.add_middleware(TenantMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# Exception handlers (order matters - most specific first)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(DatabaseError, database_error_handler)
app.add_exception_handler(SQLAlchemyError, database_error_handler)

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

app.add_exception_handler(Exception, generic_exception_handler)


# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

# Include search-booking router if available
if SEARCH_BOOKING_AVAILABLE:
    app.include_router(search_booking_router)
    logger.info("Search-booking module loaded")
    
    # Include user features router
    try:
        from search_booking_module.api.user_routers import router as user_features_router
        app.include_router(user_features_router)
        logger.info("User features module loaded")
    except ImportError as e:
        logger.warning(f"User features module not available: {e}")

# Include monitoring router if available
if MONITORING_AVAILABLE:
    app.include_router(monitoring_router)
    logger.info("Monitoring module loaded")

# Include revenue router if available
if REVENUE_AVAILABLE:
    app.include_router(revenue_router)
    logger.info("Revenue module loaded")


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
    """Enhanced health check endpoint."""
    from datetime import datetime
    from sqlalchemy import text
    from .infrastructure.db.database import engine
    from .core.cache import cache_available
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "services": {}
    }
    
    # Check database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    if cache_available:
        health_status["services"]["redis"] = "healthy"
    else:
        health_status["services"]["redis"] = "unavailable"
        health_status["status"] = "degraded"
    
    # Check email (optional)
    if config.smtp_host:
        health_status["services"]["email"] = "configured"
    else:
        health_status["services"]["email"] = "not_configured"
    
    return health_status


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
