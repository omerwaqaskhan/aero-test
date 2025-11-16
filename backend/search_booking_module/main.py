"""Main FastAPI application for search-booking module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_booking_module.api.routers import router as search_booking_router
from search_booking_module.api.monitoring_routers import router as monitoring_router
from search_booking_module.scraping.scheduler import start_scheduler, stop_scheduler

# Initialize Sentry for error tracking (if enabled)
sentry_dsn = os.getenv("SENTRY_DSN")
sentry_enabled = os.getenv("ENABLE_SENTRY", "false").lower() == "true"
sentry_environment = os.getenv("SENTRY_ENVIRONMENT", "development")

if sentry_enabled and sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=sentry_environment,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "1.0")),
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        release=os.getenv("SENTRY_RELEASE", None),
        send_default_pii=False,
        enable_tracing=True,
    )
    logger.info(f"Sentry error tracking initialized for environment: {sentry_environment}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Search & Booking API",
    description="Hotel search and booking API",
    version="1.0.0"
)

# CORS middleware - Use secure configuration
import os
from typing import List

# Parse CORS origins from environment variable (comma-separated) or use defaults
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173")
cors_origins: List[str] = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Secure: specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_booking_router, prefix="/api/v1/search-booking", tags=["search-booking"])
app.include_router(monitoring_router)  # Already has /api/v1/monitoring prefix


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting search-booking service...")
    
    # Start automatic data collection scheduler
    try:
        await start_scheduler()
        logger.info("Hotel data scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start hotel data scheduler: {e}")
        # Continue even if scheduler fails


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down search-booking service...")
    
    # Stop scheduler
    try:
        await stop_scheduler()
        logger.info("Hotel data scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "search-booking"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
