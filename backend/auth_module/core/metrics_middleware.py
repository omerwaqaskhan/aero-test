"""FastAPI middleware for Prometheus metrics."""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
import re
from .prometheus_metrics import (
    http_requests_total,
    http_request_duration_seconds
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP metrics for FastAPI."""
    
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = self._normalize_path(request.url.path)
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        status_code = response.status_code
        
        # Record metrics
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status_code=status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)
        
        return response
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path for metrics (remove IDs, etc.)."""
        # Replace UUIDs and IDs with placeholders
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path
        )
        path = re.sub(r'/\d+', '/{id}', path)
        return path

