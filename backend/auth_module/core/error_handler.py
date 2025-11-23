"""Standardized error handling."""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, DatabaseError, OperationalError
import logging
import traceback
from typing import Any, Dict

logger = logging.getLogger(__name__)


class StandardErrorResponse:
    """Standard error response format."""
    
    @staticmethod
    def create(
        code: str,
        message: str,
        status_code: int = 500,
        details: Dict[str, Any] = None,
        request_id: str = None
    ) -> JSONResponse:
        """Create standardized error response."""
        error_data = {
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "timestamp": None,  # Will be set by middleware
            }
        }
        
        if request_id:
            error_data["error"]["request_id"] = request_id
        
        return JSONResponse(
            status_code=status_code,
            content=error_data
        )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return StandardErrorResponse.create(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors},
        request_id=getattr(request.state, "request_id", None)
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return StandardErrorResponse.create(
        code=exc.detail.get("code", "HTTP_ERROR") if isinstance(exc.detail, dict) else "HTTP_ERROR",
        message=exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail),
        status_code=exc.status_code,
        details=exc.detail.get("details", {}) if isinstance(exc.detail, dict) else {},
        request_id=getattr(request.state, "request_id", None)
    )


async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(
        f"Database error: {exc}",
        exc_info=True,
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "error_type": type(exc).__name__
        }
    )
    
    # Don't expose internal database errors to users
    return StandardErrorResponse.create(
        code="DATABASE_ERROR",
        message="A database error occurred. Please try again later.",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        details={},
        request_id=getattr(request.state, "request_id", None)
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        }
    )
    
    # Don't expose internal errors to users
    return StandardErrorResponse.create(
        code="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={},
        request_id=getattr(request.state, "request_id", None)
    )

