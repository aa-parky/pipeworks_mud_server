"""Session management and authentication."""

from typing import Dict, Optional, Tuple
from fastapi import HTTPException
from mud_server.db import database
from mud_server.api.permissions import Permission, has_permission

# Store active sessions (session_id -> (username, role))
active_sessions: Dict[str, Tuple[str, str]] = {}


def get_username_from_session(session_id: str) -> Optional[str]:
    """
    Get username from session ID.
    Returns only username for backward compatibility.
    """
    session_data = active_sessions.get(session_id)
    if session_data:
        return session_data[0]  # Return username from tuple
    return None


def get_username_and_role_from_session(session_id: str) -> Optional[Tuple[str, str]]:
    """Get (username, role) tuple from session ID."""
    return active_sessions.get(session_id)


def validate_session(session_id: str) -> Tuple[str, str]:
    """
    Validate session and return (username, role).

    Args:
        session_id: Session ID to validate

    Returns:
        Tuple of (username, role)

    Raises:
        HTTPException: If session is invalid
    """
    session_data = get_username_and_role_from_session(session_id)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    username, role = session_data
    database.update_session_activity(username)
    return username, role


def validate_session_with_permission(session_id: str, permission: Permission) -> Tuple[str, str]:
    """
    Validate session and check if user has required permission.

    Args:
        session_id: Session ID to validate
        permission: Required permission

    Returns:
        Tuple of (username, role)

    Raises:
        HTTPException: If session invalid or permission denied
    """
    username, role = validate_session(session_id)

    if not has_permission(role, permission):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {permission.value}",
        )

    return username, role
