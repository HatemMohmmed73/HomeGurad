"""
Role-Based Access Control (RBAC) Module
"""
from fastapi import HTTPException, status, Depends
from typing import List
from database.models import UserRole
from core.security import get_current_user


async def require_role(required_roles: List[str]):
    """
    Decorator to check if user has required role
    Usage: 
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: dict = Depends(require_role([UserRole.ADMIN]))
        ):
    """
    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", UserRole.ADMIN)
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(required_roles)}"
            )
        return current_user
    
    return role_checker


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Check if user is admin"""
    if current_user.get("role", UserRole.ADMIN) != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action is restricted to administrators"
        )
    return current_user


async def get_user_role(current_user: dict = Depends(get_current_user)) -> str:
    """Get current user's role"""
    return current_user.get("role", UserRole.ADMIN)


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if user role has specific permission
    
    Permissions:
    - view_devices: Can view devices
    - control_devices: Can start/stop devices
    - view_alerts: Can view alerts
    - acknowledge_alerts: Can acknowledge alerts
    - manage_settings: Can modify system settings
    - manage_users: Can create/delete users
    - view_analytics: Can view detailed analytics
    """
    permissions = {
        UserRole.ADMIN: [
            "view_devices",
            "control_devices",
            "view_alerts",
            "acknowledge_alerts",
            "manage_settings",
            "manage_users",
            "view_analytics",
            "access_ml_controls",
        ]
    }
    
    user_permissions = permissions.get(user_role, [])
    return permission in user_permissions


def get_permissions_for_role(role: str) -> List[str]:
    """Get all permissions for a role"""
    permissions = {
        UserRole.ADMIN: [
            "view_devices",
            "control_devices",
            "view_alerts",
            "acknowledge_alerts",
            "manage_settings",
            "manage_users",
            "view_analytics",
            "access_ml_controls",
        ]
    }
    return permissions.get(role, [])
