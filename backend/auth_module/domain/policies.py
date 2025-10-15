"""Authorization policies for RBAC and ABAC."""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class PermissionPolicy(ABC):
    """Base class for permission policies."""
    
    @abstractmethod
    def has_permission(self, user_permissions: List[str], permission: str) -> bool:
        """Check if user has permission."""
        pass


class RBACPolicy(PermissionPolicy):
    """Role-Based Access Control policy."""
    
    def has_permission(self, user_permissions: List[str], permission: str) -> bool:
        """Check if user has permission based on RBAC."""
        # Direct permission check
        if permission in user_permissions:
            return True
        
        # Check for wildcard permissions
        if "*" in user_permissions:
            return True
        
        # Check for namespace permissions (e.g., "users.*" for "users.read")
        permission_parts = permission.split(".")
        if len(permission_parts) > 1:
            namespace = permission_parts[0] + ".*"
            if namespace in user_permissions:
                return True
        
        return False
    
    def get_role_permissions(self, role: str) -> List[str]:
        """Get permissions for a role."""
        role_permissions = {
            "super_admin": [
                "*"  # All permissions
            ],
            "tenant_admin": [
                "users.*",
                "tenants.read",
                "tenants.update",
                "roles.*",
                "audit.read"
            ],
            "manager": [
                "users.read",
                "users.create",
                "users.update",
                "bookings.*",
                "reports.read"
            ],
            "user": [
                "profile.read",
                "profile.update",
                "bookings.read",
                "bookings.create"
            ]
        }
        
        return role_permissions.get(role, [])
    
    def can_manage_user(self, manager_role: str, target_role: str) -> bool:
        """Check if manager can manage target user."""
        role_hierarchy = {
            "super_admin": 4,
            "tenant_admin": 3,
            "manager": 2,
            "user": 1
        }
        
        manager_level = role_hierarchy.get(manager_role, 0)
        target_level = role_hierarchy.get(target_role, 0)
        
        return manager_level > target_level


class ABACPolicy:
    """Attribute-Based Access Control policy."""
    
    def __init__(self):
        self.policies = []
        self._load_default_policies()
    
    def _load_default_policies(self):
        """Load default ABAC policies."""
        self.policies = [
            {
                "name": "tenant_isolation",
                "description": "Users can only access resources within their tenant",
                "condition": lambda user, resource, context: (
                    user.get("tenant_id") == resource.get("tenant_id")
                )
            },
            {
                "name": "resource_ownership",
                "description": "Users can only access their own resources",
                "condition": lambda user, resource, context: (
                    user.get("id") == resource.get("owner_id")
                )
            },
            {
                "name": "time_based_access",
                "description": "Access based on time constraints",
                "condition": lambda user, resource, context: (
                    self._check_time_constraints(context.get("time_constraints", {}))
                )
            },
            {
                "name": "ip_whitelist",
                "description": "Access based on IP whitelist",
                "condition": lambda user, resource, context: (
                    self._check_ip_whitelist(
                        context.get("ip_address"),
                        context.get("ip_whitelist", [])
                    )
                )
            }
        ]
    
    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check permission using ABAC policies."""
        # Get user context
        user_context = await self._get_user_context(user_id)
        if not user_context:
            return False
        
        # Get resource context
        resource_context = await self._get_resource_context(resource)
        if not resource_context:
            return False
        
        # Apply all relevant policies
        for policy in self.policies:
            if not policy["condition"](user_context, resource_context, context):
                return False
        
        return True
    
    def _check_time_constraints(self, time_constraints: Dict[str, Any]) -> bool:
        """Check time-based constraints."""
        from datetime import datetime, time
        
        if not time_constraints:
            return True
        
        now = datetime.now().time()
        
        # Check time window
        if "start_time" in time_constraints and "end_time" in time_constraints:
            start_time = time.fromisoformat(time_constraints["start_time"])
            end_time = time.fromisoformat(time_constraints["end_time"])
            
            if not (start_time <= now <= end_time):
                return False
        
        # Check day of week
        if "allowed_days" in time_constraints:
            current_day = datetime.now().weekday()
            if current_day not in time_constraints["allowed_days"]:
                return False
        
        return True
    
    def _check_ip_whitelist(self, ip_address: str, whitelist: List[str]) -> bool:
        """Check IP whitelist."""
        if not whitelist:
            return True
        
        if not ip_address:
            return False
        
        # Simple IP matching (in production, use proper IP range matching)
        return ip_address in whitelist
    
    async def _get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user context for ABAC evaluation."""
        # This would typically use a repository to get user data
        # For now, return a placeholder
        return {
            "id": user_id,
            "tenant_id": "tenant_123",  # Would be fetched from database
            "role": "user",
            "attributes": {}
        }
    
    async def _get_resource_context(self, resource: str) -> Optional[Dict[str, Any]]:
        """Get resource context for ABAC evaluation."""
        # This would typically use a repository to get resource data
        # For now, return a placeholder
        return {
            "id": resource,
            "tenant_id": "tenant_123",  # Would be fetched from database
            "owner_id": "user_456",  # Would be fetched from database
            "attributes": {}
        }
    
    def add_policy(self, name: str, description: str, condition: callable):
        """Add a custom ABAC policy."""
        self.policies.append({
            "name": name,
            "description": description,
            "condition": condition
        })
    
    def remove_policy(self, name: str):
        """Remove an ABAC policy."""
        self.policies = [p for p in self.policies if p["name"] != name]


class PermissionPolicy:
    """Combined permission policy that uses both RBAC and ABAC."""
    
    def __init__(self):
        self.rbac_policy = RBACPolicy()
        self.abac_policy = ABACPolicy()
    
    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check permission using both RBAC and ABAC."""
        # Get user permissions
        user_permissions = await self._get_user_permissions(user_id)
        
        # Check RBAC first
        if not self.rbac_policy.has_permission(user_permissions, permission):
            return False
        
        # Check ABAC if resource and context provided
        if resource and context:
            return await self.abac_policy.check_permission(
                user_id=user_id,
                permission=permission,
                resource=resource,
                context=context
            )
        
        return True
    
    async def _get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions (placeholder - would use repository)."""
        # This would typically use a repository
        return []
