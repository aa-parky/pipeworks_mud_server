"""API route definitions."""

import uuid
from fastapi import FastAPI, HTTPException
from typing import List

from mud_server.api.models import (
    LoginRequest,
    RegisterRequest,
    ChangePasswordRequest,
    UserManagementRequest,
    CommandRequest,
    LoginResponse,
    RegisterResponse,
    CommandResponse,
    StatusResponse,
    UserListResponse,
)
from mud_server.api.auth import validate_session, active_sessions, validate_session_with_permission
from mud_server.api.permissions import Permission, has_permission, can_manage_role
from mud_server.core.engine import GameEngine
from mud_server.db import database


def register_routes(app: FastAPI, engine: GameEngine):
    """Register all API routes with the FastAPI app."""

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "MUD Server API", "version": "0.1.0"}

    @app.post("/login", response_model=LoginResponse)
    async def login(request: LoginRequest):
        """Login with username and password."""
        username = request.username.strip()
        password = request.password

        if not username or len(username) < 2 or len(username) > 20:
            raise HTTPException(
                status_code=400, detail="Username must be 2-20 characters"
            )

        # Create session ID
        session_id = str(uuid.uuid4())

        # Attempt login with password verification
        success, message, role = engine.login(username, password, session_id)

        if success and role:
            # Store session with role
            active_sessions[session_id] = (username, role)
            return LoginResponse(
                success=True, message=message, session_id=session_id, role=role
            )
        else:
            raise HTTPException(status_code=401, detail=message)

    @app.post("/register", response_model=RegisterResponse)
    async def register(request: RegisterRequest):
        """Register a new player account."""
        username = request.username.strip()
        password = request.password
        password_confirm = request.password_confirm

        # Validate username
        if not username or len(username) < 2 or len(username) > 20:
            raise HTTPException(
                status_code=400, detail="Username must be 2-20 characters"
            )

        # Check if username already exists
        if database.player_exists(username):
            raise HTTPException(status_code=400, detail="Username already taken")

        # Validate passwords match
        if password != password_confirm:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Validate password strength
        if len(password) < 8:
            raise HTTPException(
                status_code=400, detail="Password must be at least 8 characters"
            )

        # Create player with default 'player' role
        if database.create_player_with_password(username, password, role="player"):
            return RegisterResponse(
                success=True,
                message=f"Account created successfully! You can now login as {username}.",
            )
        else:
            raise HTTPException(
                status_code=500, detail="Failed to create account. Please try again."
            )

    @app.post("/logout")
    async def logout(request: CommandRequest):
        """Logout a player."""
        username, role = validate_session(request.session_id)

        engine.logout(username)
        if request.session_id in active_sessions:
            del active_sessions[request.session_id]

        return {"success": True, "message": f"Goodbye, {username}!"}

    @app.post("/command", response_model=CommandResponse)
    async def execute_command(request: CommandRequest):
        """Execute a game command."""
        username, role = validate_session(request.session_id)

        command = request.command.strip().lower()

        if not command:
            return CommandResponse(success=False, message="Enter a command.")

        # Parse command
        parts = command.split(maxsplit=1)
        cmd = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # Handle commands
        if cmd in ["n", "north", "s", "south", "e", "east", "w", "west"]:
            # Map shorthand to full direction
            direction_map = {
                "n": "north",
                "s": "south",
                "e": "east",
                "w": "west",
            }
            direction = direction_map.get(cmd, cmd)
            success, message = engine.move(username, direction)
            return CommandResponse(success=success, message=message)

        elif cmd == "look":
            message = engine.look(username)
            return CommandResponse(success=True, message=message)

        elif cmd == "inventory" or cmd == "inv":
            message = engine.get_inventory(username)
            return CommandResponse(success=True, message=message)

        elif cmd == "get" or cmd == "take":
            if not args:
                return CommandResponse(success=False, message="Get what?")
            success, message = engine.pickup_item(username, args)
            return CommandResponse(success=success, message=message)

        elif cmd == "drop":
            if not args:
                return CommandResponse(success=False, message="Drop what?")
            success, message = engine.drop_item(username, args)
            return CommandResponse(success=success, message=message)

        elif cmd == "chat" or cmd == "say":
            if not args:
                return CommandResponse(success=False, message="Say what?")
            success, message = engine.chat(username, args)
            return CommandResponse(success=success, message=message)

        elif cmd == "who":
            players = engine.get_active_players()
            if not players:
                message = "No other players online."
            else:
                message = "Active players:\n" + "\n".join(f"  - {p}" for p in players)
            return CommandResponse(success=True, message=message)

        elif cmd == "help":
            help_text = """
[Available Commands]
  north/n, south/s, east/e, west/w - Move in a direction
  look - Examine the current room
  inventory/inv - View your inventory
  get/take <item> - Pick up an item
  drop <item> - Drop an item
  say/chat <message> - Send a message to the room
  who - List active players
  help - Show this help message
            """
            return CommandResponse(success=True, message=help_text)

        else:
            return CommandResponse(
                success=False,
                message=f"Unknown command: {cmd}. Type 'help' for available commands.",
            )

    @app.get("/chat/{session_id}")
    async def get_chat(session_id: str):
        """Get recent chat messages from current room."""
        username, role = validate_session(session_id)
        chat = engine.get_room_chat(username)
        return {"chat": chat}

    @app.get("/status/{session_id}")
    async def get_status(session_id: str):
        """Get player status."""
        username, role = validate_session(session_id)

        current_room = database.get_player_room(username)
        inventory = engine.get_inventory(username)
        active_players = engine.get_active_players()

        return StatusResponse(
            active_players=active_players,
            current_room=current_room,
            inventory=inventory,
        )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok", "active_players": len(active_sessions)}
