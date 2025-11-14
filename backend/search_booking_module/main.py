"""Main FastAPI application for search-booking module."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search_booking_module.api.routers import router as search_booking_router
from search_booking_module.scraping.scheduler import start_scheduler, stop_scheduler

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search_booking_router, prefix="/api/v1/search-booking", tags=["search-booking"])


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
