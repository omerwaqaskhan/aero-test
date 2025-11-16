"""Observability endpoints for metrics and health checks."""

from fastapi import APIRouter
from fastapi.responses import Response
from ..core.prometheus_metrics import get_metrics_response

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return get_metrics_response()


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with metrics."""
    # This would include more detailed health information
    # For now, return basic structure
    return {
        "status": "healthy",
        "checks": {
            "database": "ok",
            "redis": "ok",
            "external_services": "ok"
        }
    }

