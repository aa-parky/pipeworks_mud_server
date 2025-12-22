"""
Input validation utilities for MUD client.

This module provides validation functions for user input across all client
operations. All validators return a tuple of (is_valid: bool, error_message: str).

Validation is separated from API logic to enable:
- Reusability across different UI contexts
- Easy testing of validation rules
- Consistent error messages
- Client-side validation before API calls

Common Patterns:
    All validators return (bool, str) tuples:
    - (True, "") for valid input
    - (False, "Error message") for invalid input
"""


def validate_username(username: str | None) -> tuple[bool, str]:
    """
    Validate username meets requirements.

    Requirements:
    - Must not be None or empty
    - Must be at least 2 characters after stripping whitespace

    Args:
        username: Username to validate

    Returns:
        Tuple of (is_valid, error_message)
        - (True, "") if valid
        - (False, error_message) if invalid

    Examples:
        >>> validate_username("alice")
        (True, "")
        >>> validate_username("a")
        (False, "Username must be at least 2 characters.")
        >>> validate_username("  ")
        (False, "Username must be at least 2 characters.")
        >>> validate_username(None)
        (False, "Username must be at least 2 characters.")
    """
    if not username or len(username.strip()) < 2:
        return False, "Username must be at least 2 characters."
    return True, ""


def validate_password(password: str | None, min_length: int = 8) -> tuple[bool, str]:
    """
    Validate password meets requirements.

    Requirements:
    - Must not be None or empty
    - Must be at least min_length characters (default: 8)

    Args:
        password: Password to validate
        min_length: Minimum required length (default: 8)

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_password("password123")
        (True, "")
        >>> validate_password("short")
        (False, "Password must be at least 8 characters.")
        >>> validate_password(None)
        (False, "Password is required.")
    """
    if password is None or password == "":
        return False, "Password is required."

    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters."

    return True, ""


def validate_password_confirmation(
    password: str | None,
    password_confirm: str | None,
) -> tuple[bool, str]:
    """
    Validate that password and confirmation match.

    This should be called AFTER validate_password() has confirmed the
    password meets basic requirements.

    Args:
        password: Original password
        password_confirm: Confirmation password

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_password_confirmation("password123", "password123")
        (True, "")
        >>> validate_password_confirmation("password123", "different")
        (False, "Passwords do not match.")
    """
    if password != password_confirm:
        return False, "Passwords do not match."
    return True, ""


def validate_password_different(
    old_password: str | None,
    new_password: str | None,
) -> tuple[bool, str]:
    """
    Validate that new password is different from old password.

    Args:
        old_password: Current/old password
        new_password: New password to set

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_password_different("old123", "new456")
        (True, "")
        >>> validate_password_different("same123", "same123")
        (False, "New password must be different from current password.")
    """
    if old_password == new_password:
        return False, "New password must be different from current password."
    return True, ""


def validate_required_field(value: str | None, field_name: str) -> tuple[bool, str]:
    """
    Validate that a required field has a value.

    Args:
        value: Field value to check
        field_name: Name of field (for error message)

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_required_field("something", "username")
        (True, "")
        >>> validate_required_field("", "password")
        (False, "Password is required.")
        >>> validate_required_field(None, "email")
        (False, "Email is required.")
    """
    if not value or not value.strip():
        return False, f"{field_name.capitalize()} is required."
    return True, ""


def validate_session_state(session_state: dict) -> tuple[bool, str]:
    """
    Validate that user has an active session.

    Args:
        session_state: Session state dictionary from Gradio

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_session_state({"logged_in": True})
        (True, "")
        >>> validate_session_state({"logged_in": False})
        (False, "You are not logged in.")
        >>> validate_session_state({})
        (False, "You are not logged in.")
    """
    if not session_state.get("logged_in"):
        return False, "You are not logged in."
    return True, ""


def validate_admin_role(session_state: dict) -> tuple[bool, str]:
    """
    Validate that user has admin or superuser role.

    This should be called AFTER validate_session_state() has confirmed
    the user is logged in.

    Args:
        session_state: Session state dictionary from Gradio

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_admin_role({"role": "admin"})
        (True, "")
        >>> validate_admin_role({"role": "superuser"})
        (True, "")
        >>> validate_admin_role({"role": "player"})
        (False, "Access Denied: Admin or Superuser role required.")
    """
    role = session_state.get("role", "player")
    if role not in ["admin", "superuser"]:
        return False, "Access Denied: Admin or Superuser role required."
    return True, ""


def validate_command_input(command: str | None) -> tuple[bool, str]:
    """
    Validate that a command has been entered.

    Args:
        command: Command string to validate

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> validate_command_input("look")
        (True, "")
        >>> validate_command_input("   ")
        (False, "Enter a command.")
        >>> validate_command_input("")
        (False, "Enter a command.")
    """
    if not command or not command.strip():
        return False, "Enter a command."
    return True, ""
