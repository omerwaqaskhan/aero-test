"""Feature flag management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from pydantic import BaseModel

from ..core.feature_flags import (
    feature_flag_manager, FeatureFlag, FeatureFlagStatus
)
from ..infrastructure.db.database import get_db
from ..infrastructure.db.models import UserModel
from ..core.security import JWTManager

router = APIRouter(prefix="/api/v1/feature-flags", tags=["feature-flags"])

security = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    db = None
) -> Optional[str]:
    """Get current user ID from JWT token (optional)."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = JWTManager.decode_token(token)
        return payload.get("sub")
    except:
        return None


class FeatureFlagResponse(BaseModel):
    """Feature flag response model."""
    name: str
    enabled: bool
    status: str
    description: str
    metadata: Dict[str, Any] = {}


class FeatureFlagListResponse(BaseModel):
    """Feature flag list response."""
    flags: Dict[str, Dict[str, Any]]


@router.get("/", response_model=FeatureFlagListResponse)
async def list_feature_flags(
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """List all feature flags with their status for the current user."""
    flags = feature_flag_manager.list_all()
    
    # Add enabled status for each flag
    for name, flag_data in flags.items():
        flag = feature_flag_manager.get(name)
        if flag:
            flag_data["enabled"] = flag.is_enabled(user_id)
    
    return FeatureFlagListResponse(flags=flags)


@router.get("/{flag_name}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    flag_name: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Get a specific feature flag status."""
    flag = feature_flag_manager.get(flag_name)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Feature flag '{flag_name}' not found")
    
    return FeatureFlagResponse(
        name=flag.name,
        enabled=flag.is_enabled(user_id),
        status=flag.status.value,
        description=flag.description,
        metadata=flag.metadata
    )


@router.post("/{flag_name}/check")
async def check_feature_flag(
    flag_name: str,
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Check if a feature flag is enabled (simple boolean response)."""
    enabled = feature_flag_manager.is_enabled(flag_name, user_id)
    return {"enabled": enabled, "flag": flag_name}

