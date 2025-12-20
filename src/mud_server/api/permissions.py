"""Role-based permission system."""

from enum import Enum
from typing import Set, Dict
from functools import wraps
from fastapi import HTTPException


class Role(Enum):
    """User roles in the system."""

    PLAYER = "player"
    WORLDBUILDER = "worldbuilder"
    ADMIN = "admin"
    SUPERUSER = "superuser"


class Permission(Enum):
    """Permissions that can be granted to roles."""

    # Player permissions
    PLAY_GAME = "play_game"
    CHAT = "chat"

    # World Builder permissions
    EDIT_WORLD = "edit_world"
    CREATE_ROOMS = "create_rooms"
    CREATE_ITEMS = "create_items"

    # Admin permissions
    KICK_USERS = "kick_users"
    BAN_USERS = "ban_users"
    VIEW_LOGS = "view_logs"

    # Superuser permissions
    MANAGE_USERS = "manage_users"
    CHANGE_ROLES = "change_roles"
    FULL_ACCESS = "full_access"


# Role permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.PLAYER: {
        Permission.PLAY_GAME,
        Permission.CHAT,
    },
    Role.WORLDBUILDER: {
        Permission.PLAY_GAME,
        Permission.CHAT,
        Permission.EDIT_WORLD,
        Permission.CREATE_ROOMS,
        Permission.CREATE_ITEMS,
    },
    Role.ADMIN: {
        Permission.PLAY_GAME,
        Permission.CHAT,
        Permission.KICK_USERS,
        Permission.BAN_USERS,
        Permission.VIEW_LOGS,
        Permission.EDIT_WORLD,
    },
    Role.SUPERUSER: {
        Permission.FULL_ACCESS,  # Superuser has all permissions
    },
}


def has_permission(role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.

    Args:
        role: Role string (player, worldbuilder, admin, superuser)
        permission: Permission to check

    Returns:
        True if role has permission, False otherwise
    """
    try:
        role_enum = Role(role.lower())
    except ValueError:
        return False

    # Superuser has all permissions
    if role_enum == Role.SUPERUSER:
        return True

    permissions = ROLE_PERMISSIONS.get(role_enum, set())
    return permission in permissions


def get_role_hierarchy_level(role: str) -> int:
    """
    Get the hierarchy level of a role.
    Higher number = more privileged.

    Args:
        role: Role string

    Returns:
        Hierarchy level (0-3)
    """
    hierarchy = {
        "player": 0,
        "worldbuilder": 1,
        "admin": 2,
        "superuser": 3,
    }
    return hierarchy.get(role.lower(), 0)


def can_manage_role(manager_role: str, target_role: str) -> bool:
    """
    Check if a manager can manage (promote/demote/ban) a target user.
    You can only manage users with lower hierarchy level.

    Args:
        manager_role: Role of the user performing the action
        target_role: Role of the user being managed

    Returns:
        True if manager can manage target, False otherwise
    """
    return get_role_hierarchy_level(manager_role) > get_role_hierarchy_level(target_role)


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for a route.

    Usage:
        @require_permission(Permission.MANAGE_USERS)
        async def my_route(username: str, role: str):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # The route should have username and role in kwargs
            role = kwargs.get("role")
            if not role or not has_permission(role, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required: {permission.value}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(min_role: Role):
    """
    Decorator to require a minimum role level for a route.

    Usage:
        @require_role(Role.ADMIN)
        async def my_route(username: str, role: str):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # The route should have role in kwargs
            role = kwargs.get("role")
            if not role:
                raise HTTPException(status_code=403, detail="Role not found in session")

            if get_role_hierarchy_level(role) < get_role_hierarchy_level(min_role.value):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient privileges. Minimum role required: {min_role.value}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator
