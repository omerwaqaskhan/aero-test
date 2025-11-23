"""Feature flag system for A/B testing and gradual rollouts."""

from typing import Dict, Optional, Any
from enum import Enum
import json
import os
from datetime import datetime

class FeatureFlagStatus(Enum):
    """Feature flag status."""
    DISABLED = "disabled"
    ENABLED = "enabled"
    ROLLOUT = "rollout"  # Gradual rollout


class FeatureFlag:
    """Feature flag definition."""
    
    def __init__(
        self,
        name: str,
        status: FeatureFlagStatus,
        description: str = "",
        rollout_percentage: int = 0,
        user_ids: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.status = status
        self.description = description
        self.rollout_percentage = rollout_percentage
        self.user_ids = user_ids or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_enabled(self, user_id: Optional[str] = None) -> bool:
        """Check if feature flag is enabled for a user."""
        if self.status == FeatureFlagStatus.DISABLED:
            return False
        
        if self.status == FeatureFlagStatus.ENABLED:
            return True
        
        if self.status == FeatureFlagStatus.ROLLOUT:
            # Check if user is in whitelist
            if user_id and user_id in self.user_ids:
                return True
            
            # Check rollout percentage (simple hash-based)
            if user_id:
                user_hash = hash(user_id) % 100
                return user_hash < self.rollout_percentage
            
            return False
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "description": self.description,
            "rollout_percentage": self.rollout_percentage,
            "user_ids": self.user_ids,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class FeatureFlagManager:
    """Manages feature flags."""
    
    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._load_from_env()
        self._load_default_flags()
    
    def _load_from_env(self):
        """Load feature flags from environment variables."""
        # Format: FEATURE_FLAG_NAME=status:percentage:user_ids
        for key, value in os.environ.items():
            if key.startswith("FEATURE_FLAG_"):
                flag_name = key.replace("FEATURE_FLAG_", "").lower()
                parts = value.split(":")
                status = FeatureFlagStatus(parts[0]) if parts else FeatureFlagStatus.DISABLED
                percentage = int(parts[1]) if len(parts) > 1 else 0
                user_ids = parts[2].split(",") if len(parts) > 2 and parts[2] else []
                
                self._flags[flag_name] = FeatureFlag(
                    name=flag_name,
                    status=status,
                    rollout_percentage=percentage,
                    user_ids=user_ids
                )
    
    def _load_default_flags(self):
        """Load default feature flags."""
        default_flags = {
            "new_search_ui": FeatureFlag(
                name="new_search_ui",
                status=FeatureFlagStatus.DISABLED,
                description="New search UI design"
            ),
            "advanced_filters": FeatureFlag(
                name="advanced_filters",
                status=FeatureFlagStatus.ENABLED,
                description="Advanced hotel filters"
            ),
            "price_alerts": FeatureFlag(
                name="price_alerts",
                status=FeatureFlagStatus.ENABLED,
                description="Price alert notifications"
            ),
            "social_login": FeatureFlag(
                name="social_login",
                status=FeatureFlagStatus.ROLLOUT,
                description="Social media login",
                rollout_percentage=50
            ),
        }
        
        for name, flag in default_flags.items():
            if name not in self._flags:
                self._flags[name] = flag
    
    def register(self, flag: FeatureFlag):
        """Register a feature flag."""
        self._flags[flag.name] = flag
    
    def get(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        return self._flags.get(name)
    
    def is_enabled(self, name: str, user_id: Optional[str] = None) -> bool:
        """Check if a feature flag is enabled."""
        flag = self.get(name)
        if not flag:
            return False
        return flag.is_enabled(user_id)
    
    def list_all(self) -> Dict[str, Dict[str, Any]]:
        """List all feature flags."""
        return {name: flag.to_dict() for name, flag in self._flags.items()}
    
    def update(self, name: str, **kwargs):
        """Update a feature flag."""
        flag = self.get(name)
        if not flag:
            raise ValueError(f"Feature flag '{name}' not found")
        
        for key, value in kwargs.items():
            if hasattr(flag, key):
                setattr(flag, key, value)
        
        flag.updated_at = datetime.utcnow()


# Global feature flag manager instance
feature_flag_manager = FeatureFlagManager()


def is_feature_enabled(name: str, user_id: Optional[str] = None) -> bool:
    """Check if a feature is enabled (convenience function)."""
    return feature_flag_manager.is_enabled(name, user_id)

